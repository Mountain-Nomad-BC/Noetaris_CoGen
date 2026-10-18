"""Bounded original-byte provenance and explicit per-page extraction coverage."""
from __future__ import annotations
import hashlib
from io import BytesIO
import json
import logging
from pathlib import PurePosixPath
import re
import threading
import unicodedata
import zlib
from contextlib import contextmanager

from .upload_limits import ACTIVE
from .text_chunks import iter_text_chunks
from .normalization import line_offset_map,validate_line_offset_map,identity_offset_map
MAX_BYTES = ACTIVE.max_bytes
MAX_CHARS = ACTIVE.max_chars
MAX_PAGES = ACTIVE.max_pages
MAX_STREAM_BYTES = 8 * 1024 * 1024
MAX_PARSER_OUTPUT_BYTES = 16 * 1024 * 1024
_PDF_LOCK = threading.RLock()

class _PdfLogFormatFilter(logging.Filter):
    def filter(self, record):
        try:
            record.getMessage()
        except (TypeError, ValueError, KeyError, IndexError):
            return False
        return True

def clean_text(text: str) -> str:
    text = unicodedata.normalize('NFC', text.replace('\r\n', '\n').replace('\r', '\n'))
    if '\x00' in text:
        raise ValueError('NUL bytes are not allowed')
    return '\n'.join(re.sub(r'[\t ]+', ' ', line).strip() for line in text.split('\n'))

@contextmanager
def bounded_pdf_decoding():
    """Limit allocation at decode seam, including object streams and arrays.

    Only unfiltered/Flate streams without predictors are admitted. The fixed
    subprocess is serial; a lock protects direct threaded parse_source callers.
    """
    import pypdf
    from pypdf import filters
    from pypdf.generic import ArrayObject, DictionaryObject, NullObject
    reader_logger = logging.getLogger('pypdf._reader')
    log_filter = _PdfLogFormatFilter()
    with _PDF_LOCK:
        original = filters.decode_stream_data
        array_limit = filters.MAX_ARRAY_BASED_STREAM_OUTPUT_LENGTH
        configuration = getattr(pypdf, 'Configuration', None)
        configured_array_limit = configuration.array_based_stream_maximum_output_length if configuration else None
        total = 0
        def decode(stream):
            nonlocal total
            codecs = stream.get('/Filter', [])
            if not isinstance(codecs, (list, ArrayObject)):
                codecs = [codecs]
            if len(codecs)>1 or any(str(c) not in {'/FlateDecode','/Fl'} for c in codecs):
                raise ValueError('PDF stream codec unsupported by bounded native extraction')
            data = stream._data
            if codecs:
                params = stream.get('/DecodeParms')
                if params is not None and not isinstance(params, NullObject):
                    if not isinstance(params, DictionaryObject):
                        raise ValueError('Malformed PDF decode parameters')
                    if params.get('/Predictor',1)!=1:
                        raise ValueError('PDF stream predictor unsupported by bounded native extraction')
                inflater = zlib.decompressobj()
                data = inflater.decompress(data, MAX_STREAM_BYTES+1)
                if len(data)>MAX_STREAM_BYTES or inflater.unconsumed_tail:
                    raise ValueError('PDF stream exceeds extraction budget')
                if not inflater.eof:
                    raise ValueError('PDF stream is truncated or invalid')
            if len(data)>MAX_STREAM_BYTES:
                raise ValueError('PDF stream exceeds extraction budget')
            total += len(data)
            if total>32*1024*1024:
                raise ValueError('PDF aggregate decoded stream budget exceeded')
            return data
        filters.decode_stream_data = decode
        if configuration:
            configuration.array_based_stream_maximum_output_length = MAX_STREAM_BYTES
        else:
            filters.MAX_ARRAY_BASED_STREAM_OUTPUT_LENGTH = MAX_STREAM_BYTES
        reader_logger.addFilter(log_filter)
        try:
            yield
        finally:
            reader_logger.removeFilter(log_filter)
            filters.decode_stream_data = original
            filters.MAX_ARRAY_BASED_STREAM_OUTPUT_LENGTH = array_limit
            if configuration:
                configuration.array_based_stream_maximum_output_length = configured_array_limit

def _pdf_pages(data):
    from pypdf import PdfReader
    from pypdf.errors import PyPdfError
    pages, statuses = [], []
    try:
        with bounded_pdf_decoding():
            reader = PdfReader(BytesIO(data), strict=True)
            if reader.is_encrypted:
                raise ValueError('Encrypted PDFs are not supported')
            if len(reader.pages)>MAX_PAGES:
                raise ValueError(f'PDF exceeds {MAX_PAGES} pages')
            total = 0
            for number, page in enumerate(reader.pages,1):
                from pypdf.generic import ArrayObject, ContentStream, DictionaryObject, NullObject, StreamObject
                raw_contents = page.get('/Contents')
                if raw_contents is not None:
                    raw_contents = raw_contents.get_object()
                    if isinstance(raw_contents, NullObject):
                        raw_contents = None
                    elif isinstance(raw_contents, ArrayObject):
                        for item in raw_contents:
                            if not isinstance(item.get_object(), (NullObject, StreamObject)):
                                raise ValueError('Malformed PDF page content array')
                    elif not isinstance(raw_contents, StreamObject):
                        raise ValueError('Malformed PDF page content stream')
                contents = page.get_contents() if raw_contents is not None else None
                if contents is not None:
                    if not isinstance(contents, ContentStream):
                        raise ValueError('Malformed PDF page content stream')
                    if len(contents.get_data())>MAX_STREAM_BYTES:
                        raise ValueError('PDF page content exceeds extraction budget')
                resources = page.get('/Resources')
                if resources is not None:
                    resources=resources.get_object()
                    if not isinstance(resources, DictionaryObject):
                        raise ValueError('Malformed PDF page resources')
                objects = resources.get('/XObject') if resources else None
                if objects is not None:
                    objects=objects.get_object()
                    if not isinstance(objects, DictionaryObject):
                        raise ValueError('Malformed PDF XObject resources')
                images = False
                if objects:
                    for reference in objects.values():
                        obj=reference.get_object()
                        if not isinstance(obj, StreamObject):
                            raise ValueError('Malformed PDF XObject stream')
                        if str(obj.get('/Subtype')) in {'/Image','/Form'}:
                            images=True
                if images:
                    raw=page.extract_text() or ''
                else:
                    seen_operation=False;inline_image=False
                    def observe_operation(operator,*unused):
                        nonlocal seen_operation,inline_image
                        seen_operation=True
                        if operator==b'INLINE IMAGE':inline_image=True
                    raw=page.extract_text(visitor_operand_before=observe_operation) or ''
                    # pypdf can return before visiting operations when a page has
                    # no resources. Inline images need no external resource entry.
                    # Inspect that skipped stream once; other pages reuse the text
                    # extractor's visit rather than parsing content a second time.
                    if not seen_operation and contents is not None:
                        inline_image=any(operator==b'INLINE IMAGE' for _,operator in contents.operations)
                    images=inline_image
                text = clean_text(raw)
                total += len(text)
                if total>MAX_CHARS:
                    raise ValueError('Extracted text exceeds budget')
                status = 'ocr_required' if images else ('native' if text.strip() else 'blank')
                statuses.append(dict(page=number,status=status,native_text_present=bool(text.strip()),complete=not images))
                pages.append((number,raw))
    except (PyPdfError, AttributeError, TypeError, IndexError, KeyError, OverflowError):
        raise ValueError('Malformed or unsupported PDF structure') from None
    return pages,statuses

def parse_source(data: bytes, filename: str) -> dict:
    from .source_admission import admit_source_path
    admit_source_path(filename)
    if not data or len(data)>MAX_BYTES:
        raise ValueError(f'Source must be nonempty and at most {MAX_BYTES // (1024*1024)} MiB')
    if not filename or '/' in filename or '\\' in filename or len(filename)>180 or any(ord(c)<32 for c in filename):
        raise ValueError('Use a filename without a directory path or controls')
    suffix = PurePosixPath(filename).suffix.lower()
    if suffix=='.xlsx':
        from .xlsx_sources import parse_xlsx
        result=parse_xlsx(data)
        validate_parsed_source(data,result)
        return result
    if suffix=='.json':
        from .json_sources import parse_json
        result=parse_json(data)
        validate_parsed_source(data,result)
        return result
    from .structured_sources import MEDIA,parse_delimited
    if suffix in MEDIA:
        result=parse_delimited(data,MEDIA[suffix])
        validate_parsed_source(data,result)
        return result
    if suffix=='.pdf':
        if not data.startswith(b'%PDF-'):
            raise ValueError('PDF signature does not match filename')
        pages,statuses = _pdf_pages(data)
        media = 'application/pdf'
    elif suffix in {'.txt','.md'}:
        pages=[(None,data.decode('utf-8-sig',errors='strict'))]
        statuses=[dict(page=None,status='native',complete=True,native_text_present=True)]
        media='text/markdown' if suffix=='.md' else 'text/plain'
    else:
        raise ValueError('Only UTF-8 TXT, Markdown, CSV, TSV, JSON, bounded XLSX, and text PDFs are supported')
    normalized=[(page,clean_text(text)) for page,text in pages]
    if sum(len(text) for _,text in normalized)>MAX_CHARS:
        raise ValueError('Extracted text exceeds budget')
    spans,mapping=[],[]
    global_line=0
    for page,raw in pages:
        for line,raw_line in enumerate(re.findall(r'[^\r\n]*(?:\r\n|\r|\n|$)',raw),1):
            global_line+=1
            value,offset_map=line_offset_map(raw_line)
            if value:
                locator=f'page:{page}:line:{line}' if page else f'line:{line}'
                spans.append(dict(locator=locator,global_line=global_line,text=value,page=page))
                mapping.append(dict(locator=locator,raw_text=raw_line,normalized_text=value,
                    offset_unit='unicode_codepoint',normalization='NFC/line-endings/space-collapse/trim-v1',
                    offset_map=offset_map))
    if not spans and not any(p['status']=='ocr_required' for p in statuses):
        raise ValueError('No extractable text; scanned PDFs require OCR, which is not enabled')
    if len(spans)>5000:
        raise ValueError('Source exceeds 5000 nonempty spans')
    chunks=[]
    for span in spans:
        for offset,text in iter_text_chunks(span['text']):
            chunks.append(dict(locator=span['locator'],offset=offset,end_offset=offset+len(text),text=text,
                sha256=hashlib.sha256(text.encode()).hexdigest()))
    if len(chunks)>5000:
        raise ValueError('Source exceeds 5000 chunks')
    warnings=['OCR disabled; extracted layout may differ from PDF visual layout'] if suffix=='.pdf' else []
    if any(not p['complete'] for p in statuses):
        warnings.append('INCOMPLETE: raster or form content requires OCR; answers cover extracted native text only')
    result=dict(original_sha256=hashlib.sha256(data).hexdigest(),media_type=media,
        raw_text='\n'.join(text for _,text in normalized),spans=spans,chunks=chunks,
        page_count=len(pages),pages=statuses,normalization_map=mapping,
        parser_version='nsai-bounded/3',warnings=warnings,complete=all(p['complete'] for p in statuses))
    validate_parsed_source(data,result)
    return result

def extraction_snapshot(native):
    """Keep the complete pre-OCR representation; it is never active evidence."""
    import json
    encoded=json.dumps(native,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
    if len(encoded)>MAX_PARSER_OUTPUT_BYTES:raise ValueError('Extraction snapshot exceeds envelope budget')
    return dict(schema='nsai.extraction-snapshot/1',kind='native-before-ocr',
                sha256=hashlib.sha256(encoded).hexdigest(),payload=native)


def _validate_extraction_history(data,parsed):
    history=parsed.get('extraction_history',[])
    if not isinstance(history,list) or len(history)>1:raise ValueError('Invalid extraction history bound')
    if not history:
        if parsed.get('parser_version') in {'nsai-bounded/2+ocr/3','nsai-bounded/3+ocr/4'} and any(page['status']=='ocr' for page in parsed['pages']):
            raise ValueError('Current OCR extraction omitted its native snapshot')
        return
    record=history[0]
    if parsed['media_type']!='application/pdf' or not isinstance(record,dict) or set(record)!={'schema','kind','sha256','payload'}:
        raise ValueError('Invalid extraction snapshot')
    native=record['payload']
    fields={'original_sha256','media_type','raw_text','spans','chunks','page_count','pages','normalization_map','parser_version','warnings','complete'}
    if not isinstance(native,dict) or set(native)!=fields or native['parser_version'] not in {'nsai-bounded/2','nsai-bounded/3'}:
        raise ValueError('Invalid native extraction snapshot shape')
    expected_native={'nsai-bounded/2+ocr/2':'nsai-bounded/2','nsai-bounded/2+ocr/3':'nsai-bounded/2',
                     'nsai-bounded/3+ocr/4':'nsai-bounded/3'}.get(parsed.get('parser_version'))
    if expected_native is not None and native['parser_version']!=expected_native:
        raise ValueError('Native/OCR extraction version mismatch')
    if record!=extraction_snapshot(native):raise ValueError('Extraction snapshot byte identity mismatch')
    validate_parsed_source(data,native)
    if native['media_type']!='application/pdf' or native['page_count']!=parsed['page_count']:
        raise ValueError('Extraction snapshot source/page mismatch')
    replaced={page['page'] for page in parsed['pages'] if page['status']=='ocr'}
    if not replaced or any(page['status'] not in {'native','blank','ocr_required'} for page in native['pages']):
        raise ValueError('Invalid native/OCR extraction selection')
    for field in ('spans','chunks','normalization_map'):
        def retained(item):
            match=re.fullmatch(r'page:([1-9][0-9]*):line:([1-9][0-9]*)',item['locator'])
            if match is None:raise ValueError('Invalid extraction snapshot locator')
            return int(match[1]) not in replaced
        if [item for item in native[field] if retained(item)]!=[item for item in parsed[field] if retained(item)]:
            raise ValueError('Unselected native extraction changed during OCR')


def _validate_ocr_words(parsed,spans,pages):
    """Validate the service envelope without parsing untrusted PDF bytes here."""
    import math
    import re
    words=parsed.get('ocr_words',[])
    if not isinstance(words,list) or len(words)>50000:raise ValueError('Invalid OCR word budget')
    ocr_pages={p['page']:p for p in pages if p['status']=='ocr'}
    if not words and not ocr_pages:return
    if parsed['media_type']!='application/pdf' or not ocr_pages:raise ValueError('OCR metadata requires an OCR PDF page')
    from .ocr_geometry import transform_box
    grouped={page:[] for page in ocr_pages}
    fields={'text','page','pixel_box','pdf_box','pixel_to_pdf','engine_score','engine_score_is_probability'}
    def vector(value,length):
        return isinstance(value,list) and len(value)==length and all(type(v) in {int,float} and math.isfinite(v) for v in value)
    for word in words:
        if not isinstance(word,dict) or set(word)!=fields:raise ValueError('Invalid OCR word fields')
        page=word['page'];text=word['text'];score=word['engine_score']
        if type(page) is not int or page not in ocr_pages or not isinstance(text,str) or not 1<=len(text)<=200 or not clean_text(text) or any(ord(c)<32 for c in text):
            raise ValueError('Invalid OCR word page or text')
        if type(score) not in {int,float} or not math.isfinite(score) or not 0<=score<=100 or word['engine_score_is_probability'] is not False:
            raise ValueError('Invalid OCR engine score')
        box,reported,transform=word['pixel_box'],word['pdf_box'],word['pixel_to_pdf']
        if not vector(box,4) or not vector(reported,4) or not vector(transform,6):raise ValueError('Invalid OCR geometry')
        x0,y0,x1,y1=box;a,b,c,d,e,f=transform
        if not (0<=x0<x1<=20000 and 0<=y0<y1<=20000 and x1*y1<=12000000):raise ValueError('OCR pixel geometry outside budget')
        scale=72/300
        matrices={(scale,0,0,-scale),(0,scale,scale,0),(-scale,0,0,scale),(0,-scale,-scale,0)}
        if ocr_pages[page].get('dpi')!=300 or (a,b,c,d) not in matrices or abs(e)>40000 or abs(f)>40000:
            raise ValueError('Unsupported OCR transform')
        expected=transform_box(transform,box)
        if any(not math.isclose(actual,wanted,rel_tol=1e-9,abs_tol=1e-7) for actual,wanted in zip(reported,expected)):
            raise ValueError('OCR transform custody mismatch')
        grouped[page].append(text)
    for page,texts in grouped.items():
        page_spans=[s for s in spans if s.get('page')==page and s.get('extraction')=='ocr']
        if not texts or not page_spans or any(not re.fullmatch(r'page:'+str(page)+r':line:[1-9][0-9]*',s['locator']) for s in page_spans):
            raise ValueError('OCR words lack source spans')
        normalize=lambda text:re.sub(r'\s+',' ',clean_text(text)).strip()
        if normalize(' '.join(texts))!=normalize(' '.join(s['text'] for s in page_spans)):
            raise ValueError('OCR word text does not match extracted source spans')


def validate_parsed_source(data: bytes, parsed: dict) -> dict:
    """Independent custody/shape/hash/offset validation for parser clients."""
    if not isinstance(parsed,dict) or parsed.get('original_sha256')!=hashlib.sha256(data).hexdigest():
        raise ValueError('Parser provenance mismatch')
    if len(json.dumps(parsed,ensure_ascii=False).encode())>MAX_PARSER_OUTPUT_BYTES:
        raise ValueError('Parser output exceeds envelope budget')
    from .structured_sources import MEDIA,validate_delimited
    if parsed.get('media_type') in MEDIA.values():return validate_delimited(data,parsed)
    if parsed.get('media_type')=='application/json':
        from .json_sources import validate_json
        return validate_json(data,parsed)
    if parsed.get('media_type')=='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        from .xlsx_sources import validate_xlsx
        return validate_xlsx(data,parsed)
    if 'structured_data' in parsed:raise ValueError('Structured evidence requires a supported structured media type')
    if not isinstance(parsed.get('raw_text'),str) or len(parsed['raw_text'])>MAX_CHARS:
        raise ValueError('Invalid parser text budget')
    if parsed.get('media_type') not in {'application/pdf','text/plain','text/markdown'}:
        raise ValueError('Invalid parser media type')
    spans,chunks,pages=parsed.get('spans'),parsed.get('chunks'),parsed.get('pages')
    if not isinstance(spans,list) or not 0<=len(spans)<=5000 or not isinstance(chunks,list) or not 0<=len(chunks)<=5000:
        raise ValueError('Invalid parser span/chunk bounds')
    if not isinstance(pages,list) or not 1<=len(pages)<=MAX_PAGES or len(pages)!=parsed.get('page_count'):
        raise ValueError('Invalid parser page coverage')
    if type(parsed.get('page_count')) is not int:raise ValueError('Invalid page count type')
    if parsed['media_type']=='application/pdf':
        if any(type(p.get('page')) is not int for p in pages if isinstance(p,dict)) or [p.get('page') for p in pages if isinstance(p,dict)]!=list(range(1,len(pages)+1)):
            raise ValueError('PDF page numbering does not cover original sequence')
    elif len(pages)!=1 or pages[0].get('page') is not None:raise ValueError('Text source cannot claim PDF pages')
    if any(not isinstance(p,dict) or p.get('status') not in {'native','blank','ocr','ocr_required','failed','unsupported'} or type(p.get('complete')) is not bool for p in pages):
        raise ValueError('Invalid parser page status')
    expected_pages=list(range(1,len(pages)+1)) if parsed['media_type']=='application/pdf' else [None]
    if [p.get('page') for p in pages]!=expected_pages or parsed.get('complete')!=all(p['complete'] for p in pages):
        raise ValueError('Invalid parser page identities or completeness')
    if any(p['complete'] and p['status'] not in {'native','blank','ocr'} for p in pages):
        raise ValueError('Incomplete parser page advertised as complete')
    if not spans and (chunks or not any(p['status']=='ocr_required' for p in pages)):
        raise ValueError('Empty parser text without an explicit OCR gap')
    if parsed['media_type']!='application/pdf' and parsed['raw_text']!=clean_text(data.decode('utf-8-sig',errors='strict')):
        raise ValueError('Parser text custody mismatch')
    by_locator={}
    for span in spans:
        if not isinstance(span,dict) or not isinstance(span.get('text'),str) or not span['text'] or not isinstance(span.get('locator'),str) or span['locator'] in by_locator:
            raise ValueError('Invalid parser span')
        by_locator[span['locator']]=span['text']
    mapping=parsed.get('normalization_map')
    if not isinstance(mapping,list) or len(mapping)!=len(spans):raise ValueError('Invalid normalization lineage')
    mapped={}
    for entry in mapping:
        if not isinstance(entry,dict) or entry.get('locator') in mapped or entry.get('locator') not in by_locator:
            raise ValueError('Invalid normalization locator')
        raw_text=entry.get('raw_text')
        normalized_text=entry.get('normalized_text')
        span_text=by_locator[entry['locator']]
        normalization=entry.get('normalization')
        if not isinstance(raw_text,str) or normalized_text!=span_text:
            raise ValueError('Normalization does not bind source span')
        if isinstance(normalization,str) and normalization.startswith('NFC/'):
            if clean_text(raw_text.rstrip('\r\n'))!=span_text:
                raise ValueError('Normalization does not bind source span')
            validate_line_offset_map(raw_text,normalized_text,entry.get('offset_map'))
        elif raw_text!=span_text or entry.get('offset_map')!=identity_offset_map(span_text):
            raise ValueError('Identity normalization does not bind source span')
        mapped[entry['locator']]=entry
    if parsed['media_type'] in {'text/plain','text/markdown'}:
        raw=data.decode('utf-8-sig',errors='strict')
        expected={f'line:{number}':line for number,line in enumerate(re.findall(r'[^\r\n]*(?:\r\n|\r|\n|$)',raw),1) if clean_text(line.rstrip('\r\n'))}
        if set(expected)!=set(by_locator) or any(mapped[key]['raw_text']!=line for key,line in expected.items()):
            raise ValueError('Parser spans do not bind original text')
    if sum(len(t) for t in by_locator.values())>MAX_CHARS:
        raise ValueError('Invalid parser aggregate text budget')
    intervals={locator:[] for locator in by_locator}
    for chunk in chunks:
        if not isinstance(chunk,dict):
            raise ValueError('Invalid parser chunk')
        text,offset=chunk.get('text'),chunk.get('offset')
        parent=by_locator.get(chunk.get('locator'))
        if not isinstance(text,str) or not 1<=len(text)<=1200 or type(offset) is not int or offset<0 or type(chunk.get('end_offset')) is not int or chunk['end_offset']!=offset+len(text) or parent is None or parent[offset:offset+len(text)]!=text or chunk.get('sha256')!=hashlib.sha256(text.encode()).hexdigest():
            raise ValueError('Parser chunk custody mismatch')
        intervals[chunk['locator']].append((offset,offset+len(text)))
    for locator,bounds in intervals.items():
        covered=0
        for start,end in sorted(bounds):
            if start>covered:raise ValueError('Parser chunk coverage has gaps')
            covered=max(covered,end)
        if covered!=len(by_locator[locator]):raise ValueError('Parser source span is not indexed completely')
    _validate_ocr_words(parsed,spans,pages)
    _validate_extraction_history(data,parsed)
    return parsed
