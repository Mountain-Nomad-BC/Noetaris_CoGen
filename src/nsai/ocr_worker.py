"""Fixed, isolated English printed-text OCR. No generated executable content."""
from __future__ import annotations
import base64
import csv
import hashlib
from io import StringIO,BytesIO
import json
import math
from pathlib import Path
import subprocess
import tempfile
import time
from .upload_limits import ACTIVE
from .ocr_geometry import page_geometry,transform_box
from .ingestion import parse_source,clean_text,validate_parsed_source,bounded_pdf_decoding,MAX_PARSER_OUTPUT_BYTES,MAX_CHARS
from .text_chunks import iter_text_chunks
from .normalization import line_offset_map

MAX_PIXELS=12_000_000
PAGE_SECONDS=10
JOB_SECONDS=120
DPI=300

def _command(arguments,deadline):
    remaining=deadline-time.monotonic()
    if remaining<=0:
        raise ValueError('OCR job deadline exceeded')
    try:
        # Tools write bounded files in an owned tmpfs. No payload on logs.
        process=subprocess.run(arguments,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,timeout=min(PAGE_SECONDS,remaining),check=False,
            env={'PATH':'/usr/bin:/bin','OMP_THREAD_LIMIT':'1','LANG':'C.UTF-8'})
    except subprocess.TimeoutExpired:
        raise ValueError('OCR page deadline exceeded') from None
    if process.returncode:
        raise ValueError('OCR fixed tool failed')

def _read_tsv(path,page_number,width,height):
    if path.stat().st_size>2*1024*1024:
        raise ValueError('OCR TSV exceeds budget')
    # Tesseract emits literal quotation glyphs, not CSV-escaped fields.
    rows=csv.DictReader(StringIO(path.read_text(encoding='utf-8')),delimiter='\t',quoting=csv.QUOTE_NONE)
    lines={};words=[]
    for row in rows:
        if row.get('level')!='5' or not (row.get('text') or '').strip():
            continue
        if len(words)>=10000:
            raise ValueError('OCR word budget exceeded')
        if len(row['text'])>200 or any(ord(c)<32 for c in row['text']):
            raise ValueError('OCR word text exceeds supported page grammar')
        x,y,w,h=[int(row[key]) for key in ('left','top','width','height')]
        score=float(row['conf'])
        if min(x,y,w,h)<0 or min(w,h)<=0 or x+w>width or y+h>height or not math.isfinite(score) or not 0<=score<=100:
            raise ValueError('OCR invalid geometry or engine score')
        key=(row['block_num'],row['par_num'],row['line_num'])
        lines.setdefault(key,[]).append(row['text'])
        words.append(dict(text=row['text'],pixel_box=[x,y,x+w,y+h],engine_score=score,
            engine_score_is_probability=False,page=page_number))
    raw='\n'.join(' '.join(values) for values in lines.values())
    return raw,words

def validate_original_geometry(data,parsed):
    """Original-byte geometry verification belongs only in the isolated worker."""
    from pypdf import PdfReader
    with bounded_pdf_decoding():
        reader=PdfReader(BytesIO(data),strict=True)
        if reader.is_encrypted or len(reader.pages)!=parsed['page_count']:
            raise ValueError('OCR source page custody mismatch')
        geometries={page['page']:page_geometry(reader.pages[page['page']-1])
                    for page in parsed['pages'] if page['status']=='ocr'}
    for word in parsed.get('ocr_words',[]):
        geometry=geometries[word['page']]
        if tuple(word['pixel_to_pdf'])!=geometry.pixel_to_pdf:
            raise ValueError('OCR original transform mismatch')
        box=word['pixel_box']
        if box[2]>geometry.pixels[0] or box[3]>geometry.pixels[1]:
            raise ValueError('OCR pixel geometry outside source raster')
        expected=transform_box(geometry.pixel_to_pdf,box)
        left,bottom,right,top=geometry.crop
        if not (left<=expected[0]<expected[2]<=right and bottom<=expected[1]<expected[3]<=top):
            raise ValueError('OCR word outside original crop')
        if any(not math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-7) for a,b in zip(expected,word['pdf_box'])):
            raise ValueError('OCR original box mismatch')


def extract_ocr(data: bytes,filename: str, *, language='eng'):
    if language!='eng':
        raise ValueError('Only printed English OCR is supported')
    if not filename.lower().endswith('.pdf'):
        raise ValueError('OCR accepts original PDF bytes only')
    result=parse_source(data,filename)
    import copy
    native_before_ocr=copy.deepcopy(result)
    from pypdf import PdfReader
    geometries={}
    with bounded_pdf_decoding():
        reader=PdfReader(BytesIO(data),strict=True)
        for number,page in enumerate(reader.pages,1):
            try:geometries[number]=page_geometry(page)
            except ValueError as error:
                if 'pixel budget' in str(error):raise
                geometries[number]=str(error)
    deadline=time.monotonic()+JOB_SECONDS
    pages=result['pages'];ocr_lines={};ocr_words=[]
    with tempfile.TemporaryDirectory(prefix='nsai-ocr-') as folder:
        directory=Path(folder);original=directory/'original.pdf';original.write_bytes(data)
        for status in pages:
            if status['status']!='ocr_required':continue
            page_deadline=min(deadline,time.monotonic()+PAGE_SECONDS)
            number=status['page'];geometry=geometries[number]
            if isinstance(geometry,str):
                status.update(status='unsupported',complete=False,reason=geometry);continue
            pixels=geometry.pixels;prefix=directory/'page'
            try:
                _command(['/usr/bin/pdftoppm','-f',str(number),'-l',str(number),'-singlefile','-gray','-r',str(DPI),'-cropbox',str(original),str(prefix)],page_deadline)
                image=prefix.with_suffix('.pgm')
                if image.stat().st_size>MAX_PIXELS+65536:
                    raise ValueError('OCR raster file exceeds budget')
                _command(['/usr/bin/tesseract',str(image),str(prefix),'-l','eng','--oem','1','--psm','3','tsv'],page_deadline)
                raw,words=_read_tsv(prefix.with_suffix('.tsv'),number,*pixels)
                if not raw.strip():
                    status.update(status='failed',complete=False,reason='No printed text recognized');continue
                for word in words:
                    word['pixel_to_pdf']=list(geometry.pixel_to_pdf)
                    word['pdf_box']=transform_box(geometry.pixel_to_pdf,word['pixel_box'])
                ocr_words.extend(words);ocr_lines[number]=raw
                status.update(status='ocr',complete=True,quality='uncalibrated',language='eng',dpi=DPI,
                    supported_content='printed English; handwriting, languages and formulas unsupported')
            except (ValueError,OSError) as error:
                status.update(status='failed',complete=False,reason=str(error))
    if ocr_lines:
        from .ingestion import extraction_snapshot
        result['extraction_history']=[extraction_snapshot(native_before_ocr)]
        result['warnings'].append('OCR is the active page extraction; the complete pre-OCR native extraction is retained separately for inspection and recovery.')
        replaced=set(ocr_lines)
        result['spans']=[s for s in result['spans'] if s['page'] not in replaced]
        result['chunks']=[c for c in result['chunks'] if int(c['locator'].split(':')[1]) not in replaced]
        result['normalization_map']=[m for m in result['normalization_map'] if int(m['locator'].split(':')[1]) not in replaced]
        for number,raw in ocr_lines.items():
            for line,raw_line in enumerate(raw.split('\n'),1):
                text,offset_map=line_offset_map(raw_line)
                if not text:continue
                locator=f'page:{number}:line:{line}'
                result['spans'].append(dict(locator=locator,global_line=line,text=text,page=number,extraction='ocr'))
                result['normalization_map'].append(dict(locator=locator,raw_text=raw_line,normalized_text=text,offset_unit='unicode_codepoint',normalization='NFC/line-endings/space-collapse/trim-v1',offset_map=offset_map))
                for offset,chunk in iter_text_chunks(text):
                    result['chunks'].append(dict(locator=locator,offset=offset,end_offset=offset+len(chunk),text=chunk,sha256=hashlib.sha256(chunk.encode()).hexdigest()))
        result['spans'].sort(key=lambda span:(span['page'],int(span['locator'].split(':')[-1])))
        result['raw_text']='\n'.join(s['text'] for s in result['spans'])
    result.update(complete=all(p['complete'] for p in pages),ocr_words=ocr_words,parser_version='nsai-bounded/3+ocr/4')
    result['warnings'].append('OCR is unverified extraction; engine scores are not probabilities. Quality gates uncalibrated. Formulas, handwriting and other languages unsupported.')
    # Allow failed-only output as an explicit withheld receipt, not source evidence.
    if result['spans']:
        validate_parsed_source(data,result)
        validate_original_geometry(data,result)
    if len(json.dumps(result,ensure_ascii=False).encode())>MAX_PARSER_OUTPUT_BYTES:
        raise ValueError('OCR envelope exceeds budget')
    return result

def main():
    import resource,sys
    resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
    resource.setrlimit(resource.RLIMIT_CPU,(110,110))
    resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024*1024,64*1024*1024))
    resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
    payload=json.loads(sys.stdin.buffer.read(ACTIVE.request_bytes+1))
    result=extract_ocr(base64.b64decode(payload['data'],validate=True),payload['filename'],language=payload.get('language','eng'))
    sys.stdout.buffer.write(json.dumps(result,ensure_ascii=False).encode())

if __name__=='__main__':main()
