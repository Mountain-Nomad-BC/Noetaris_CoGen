"""Source-quoted mathematical candidates; no equation reconstruction or execution."""
import hashlib
import json
import re

MAX_SPANS=5000
MAX_INPUT_CHARS=200000
MAX_RECORDS=5000
MAX_JSON_BYTES=8*1024*1024
MAX_CANDIDATE_CHARS=4096
CONTEXT_CHARS=512
_SPECIAL=re.compile(r'[≤≥≈≠≡∝∈∉⊆⊂∑∏∫√∞±∂∇⊗×÷²³⁰¹⁴⁵⁶⁷⁸⁹]')
_FUNCTION=re.compile(r'\b(?:O|log|ln|sin|cos|tan|exp|max|min|argmax|argmin)\s*\(')
_ARITHMETIC=re.compile(r'(?:[\w)\]]\s+[+*/^−-]\s+[\w(\[]|[\w)\]][*/^][\w(\[]|\d\s*[+−-]\s*\w|\w\s*[+−-]\s*\d)')
_LABEL=re.compile(r'^\s*[([]\d{1,3}(?:\.\d{1,3})?[a-z]?[)\]]\s*$')
_LOCATOR=re.compile(r'^page:([1-9]\d*):line:([1-9]\d*)$')

def _hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def _signals(text):
    if re.fullmatch(r'https?://\S+',text):return []
    signals=[]
    if _SPECIAL.search(text):signals.append('unicode_math_notation')
    if _ARITHMETIC.search(text):signals.append('arithmetic_notation')
    if _FUNCTION.search(text):signals.append('function_notation')
    if re.search(r'[=<>]',text) and (signals or re.search(r'\d',text) or re.search(r'\b\w\s*\(',text) or re.search(r'(?<!\w)\w\s*[=<>]|[=<>]\s*\w(?!\w)',text)):
        signals.append('relation_notation')
    return signals

def extract_math(parsed,document_id,revision):
    """Extract bounded, uncertain source-line candidates from validated parser spans.

    Offsets are Unicode code points within the identified source span. Source
    integrity must already have been checked against original PDF bytes by the
    ingestion boundary. A candidate can contain prose: detection is not parsing.
    """
    if not isinstance(parsed,dict) or not isinstance(document_id,str) or not re.fullmatch(r'[a-f0-9]{32}',document_id):
        raise ValueError('Mathematical candidates require a document identity')
    if not isinstance(revision,str) or not 1<=len(revision)<=50:
        raise ValueError('Mathematical candidates require a bounded revision')
    digest=parsed.get('original_sha256')
    if not isinstance(digest,str) or not re.fullmatch(r'[a-f0-9]{64}',digest):raise ValueError('Original source SHA256 required')
    spans=parsed.get('spans')
    if not isinstance(spans,list) or len(spans)>MAX_SPANS:raise ValueError('Mathematical source span budget exceeded')
    lines=[];seen=set();total=0
    for span in spans:
        if not isinstance(span,dict) or not isinstance(span.get('text'),str) or not isinstance(span.get('locator'),str) or not 1<=len(span['locator'])<=200:
            raise ValueError('Invalid mathematical source span')
        if span['locator'] in seen:raise ValueError('Duplicate mathematical source locator')
        seen.add(span['locator']);total+=len(span['text'])
        if total>MAX_INPUT_CHARS:raise ValueError('Mathematical input text budget exceeded')
        match=_LOCATOR.fullmatch(span['locator']);page=int(match[1]) if match else None
        if span.get('page') is not None and (type(span['page']) is not int or span['page']!=page):raise ValueError('Source page and locator disagree')
        offset=0;span_hash=hashlib.sha256(span['text'].encode()).hexdigest()
        for raw in span['text'].splitlines(keepends=True):
            stripped=raw.strip();start=offset+len(raw)-len(raw.lstrip());end=start+len(stripped)
            if stripped:lines.append(dict(locator=span['locator'],page=page,span_sha256=span_hash,offset_start=start,offset_end=end,text=stripped))
            offset+=len(raw)
    records=[];detected=0;omitted=0;oversize=0
    for index,line in enumerate(lines):
        signals=_signals(line['text'])
        previous=lines[index-1] if index else None
        adjacent=bool(previous and _adjacent(previous,line))
        continuation=bool(adjacent and records and records[-1]['source']==previous and (re.match(r'^[+−*/^=]',line['text']) or previous['text'].rstrip().endswith(('=','+','−','*','/','^','(')) or _LABEL.fullmatch(line['text'])))
        if continuation:signals.append('possible_display_continuation')
        if not signals:continue
        detected+=1
        if len(line['text'])>MAX_CANDIDATE_CHARS:oversize+=1;omitted+=1;continue
        if len(records)>=MAX_RECORDS:omitted+=1;continue
        identifier=_hash(dict(schema='nsai-scientific-math/1',document_id=document_id,revision=revision,source_sha256=digest,source=line))
        context=[]
        for other in lines[max(0,index-1):index+2]:
            if other is line or other['page']!=line['page']:continue
            quoted=dict(other)
            if len(quoted['text'])>CONTEXT_CHARS:
                quoted['text']=quoted['text'][:CONTEXT_CHARS];quoted['offset_end']=quoted['offset_start']+CONTEXT_CHARS;quoted['context_truncated']=True
            context.append(quoted)
        records.append(dict(id=identifier,source=line,source_sha256=digest,document_id=document_id,revision=revision,
            detection_signals=sorted(set(signals)),context=context,continuation_of=records[-1]['id'] if continuation else None,
            continuation_group=records[-1]['continuation_group'] if continuation else identifier,
            representation='quoted_math_bearing_source_line_may_include_prose',status='unverified_math_candidate',review_required=True,
            confidence=dict(kind='heuristic_detection_only',probability=None,calibrated=False),latex=None,evaluation='not_attempted',generated_execution=False))
    result=dict(schema_version='nsai-scientific-math/1',document_id=document_id,revision=revision,original_sha256=digest,
        records=records,coverage=dict(source_spans=len(spans),source_lines=len(lines),candidate_regions_detected=detected,returned_records=len(records),omitted_records=omitted,oversize_candidates=oversize,truncated=bool(omitted),exhaustive=False,semantic_completeness='unknown'),
        status='partial_candidate' if omitted else 'candidate',processing_complete=not omitted,review_required=True,authority_granted=False,
        limitations=['Heuristic detection may miss formulas or include prose; zero candidates does not establish absence of mathematics',
            'Native PDF glyph order, ligatures, subscripts, superscripts, fractions and layout may be lost or incorrect',
            'OCR mathematical recognition is unsupported; source quotes are not verified mathematical notation',
            'No LaTeX reconstruction, symbolic evaluation, dimensional verification or mathematical correctness claim',
            'Offsets address extracted span text, not PDF byte offsets; original-byte integrity is the ingestion boundary responsibility'])
    if len(json.dumps(result,ensure_ascii=False,allow_nan=False).encode())>MAX_JSON_BYTES:
        raise ValueError('Mathematical artifact exceeds 8 MiB; extraction cannot be admitted as complete')
    return result

def _adjacent(left,right):
    if left['locator']==right['locator']:return left['offset_end']<=right['offset_start']
    a=_LOCATOR.fullmatch(left['locator']);b=_LOCATOR.fullmatch(right['locator'])
    return bool(a and b and a[1]==b[1] and int(b[2])==int(a[2])+1)


_TEX_ENVIRONMENTS=('equation','equation*','align','align*','gather','gather*','multline','multline*','displaymath','eqnarray','eqnarray*','math')
_TEX_CODE=('verbatim','verbatim*','Verbatim','lstlisting','minted')

def _tex_skip(text,index):
    """Return the end of a comment/opaque code region, or None."""
    if text[index]=='%':
        end=text.find('\n',index);return len(text) if end<0 else end+1
    for name in _TEX_CODE:
        token='\\begin{'+name+'}'
        if text.startswith(token,index):
            end_token='\\end{'+name+'}';end=text.find(end_token,index+len(token))
            return len(text) if end<0 else end+len(end_token)
    if text.startswith('\\verb',index):
        after=index+5
        if after<len(text) and text[after]=='*':after+=1
        if after<len(text) and not text[after].isalnum() and not text[after].isspace():
            end=text.find(text[after],after+1);newline=text.find('\n',after+1)
            if end>=0 and (newline<0 or end<newline):return end+1
            return len(text) if newline<0 else newline+1
    return None

def extract_latex_math(data,filename='source.tex',*,pdf_sha256,source_archive_sha256,document_id,revision):
    """Quote delimited author TeX without expanding it or claiming PDF alignment.

    A bounded forward scanner skips comments, verbatim/code environments and
    escaped delimiters. It is deliberately not a TeX interpreter.
    """
    if not isinstance(data,bytes) or len(data)>2*1024*1024:raise ValueError('TeX source must be bounded bytes')
    if not isinstance(filename,str) or not 1<=len(filename)<=180 or '/' in filename or '\\' in filename or not filename.lower().endswith('.tex') or any(ord(c)<32 for c in filename):raise ValueError('TeX filename must be a plain bounded .tex basename')
    if any(not isinstance(value,str) or not re.fullmatch(r'[a-f0-9]{64}',value) for value in (pdf_sha256,source_archive_sha256)):raise ValueError('PDF and archive SHA256 provenance required')
    if not isinstance(document_id,str) or not re.fullmatch(r'[a-f0-9]{32}',document_id) or not isinstance(revision,str) or not 1<=len(revision)<=50:raise ValueError('TeX document identity and revision required')
    try:text=data.decode('utf-8')
    except UnicodeError as error:raise ValueError('TeX source must be UTF-8; no guessed transcoding') from error
    if len(text)>1000000:raise ValueError('TeX character budget exceeded')
    digest=hashlib.sha256(data).hexdigest();records=[];gaps=[];index=0;skipped=0;omitted=0;detected=0
    while index<len(text):
        skip=_tex_skip(text,index)
        if skip is not None:
            for name in _TEX_CODE:
                opening_code='\\begin{'+name+'}'
                if text.startswith(opening_code,index) and text.find('\\end{'+name+'}',index+len(opening_code))<0:
                    if len(gaps)<100:gaps.append(dict(offset_start=index,reason='unclosed_opaque_code_region',environment=name))
                    omitted+=1
            skipped+=1;index=skip;continue
        opening=closing=kind=None
        for left,right,label in [('$$','$$','display_dollar'),('$','$','inline_dollar'),('\\(','\\)','inline_parenthesis'),('\\[','\\]','display_bracket')]:
            if text.startswith(left,index):opening,closing,kind=left,right,label;break
        if opening is None:
            for name in _TEX_ENVIRONMENTS:
                token='\\begin{'+name+'}'
                if text.startswith(token,index):opening,closing,kind=token,'\\end{'+name+'}','environment:'+name;break
        if opening is None:
            index+=2 if text[index]=='\\' and index+1<len(text) else 1
            continue
        start=index;cursor=index+len(opening);end=None
        while cursor<len(text):
            skip=_tex_skip(text,cursor)
            if skip is not None:skipped+=1;cursor=skip;continue
            if text.startswith(closing,cursor):end=cursor+len(closing);break
            cursor+=2 if text[cursor]=='\\' and cursor+1<len(text) else 1
        if end is None:
            if len(gaps)<100:gaps.append(dict(offset_start=start,reason='unclosed_math_delimiter',delimiter=opening))
            omitted+=1;break
        detected+=1;raw=text[start:end]
        if len(raw)>MAX_CANDIDATE_CHARS or len(records)>=MAX_RECORDS:
            omitted+=1
        else:
            source=dict(locator=f'source-tex:{filename}:chars:{start}-{end}',page=None,filename=filename,offset_start=start,offset_end=end,offset_unit='unicode_codepoint',span_sha256=digest,text=raw)
            identity=dict(document_id=document_id,revision=revision,pdf_sha256=pdf_sha256,source_archive_sha256=source_archive_sha256,source_file_sha256=digest,source=source)
            records.append(dict(id=_hash(identity),document_id=document_id,revision=revision,source_sha256=pdf_sha256,source=source,
                source_archive_sha256=source_archive_sha256,source_file_sha256=digest,source_kind='author_source_tex_not_pdf',
                pdf_alignment='not_verified',representation='quoted_author_tex_with_delimiters',latex=raw,delimiter_kind=kind,
                status='unverified_math_candidate',review_required=True,confidence=dict(kind='delimiter_detection_only',probability=None,calibrated=False),evaluation='not_attempted',generated_execution=False))
        index=end
    result=dict(schema_version='nsai-source-tex-math/1',document_id=document_id,revision=revision,pdf_sha256=pdf_sha256,
        source_archive_sha256=source_archive_sha256,source_file_sha256=digest,filename=filename,records=records,
        status='partial_candidate' if omitted else 'candidate',review_required=True,authority_granted=False,processing_complete=not omitted,
        coverage=dict(candidate_regions_detected=detected,returned_records=len(records),omitted_records=omitted,skipped_comment_or_code_regions=skipped,unsupported_regions=gaps,exhaustive=False),
        limitations=['Author source is supplemental evidence, not proof of PDF text, page positions or rendered equivalence',
            'No TeX execution, includes, macro expansion, conditional evaluation, bibliography or external resource loading',
            'Only explicit supported delimiters/environments are scanned; macros and other constructs may hide mathematical content',
            'Comments and verbatim/code regions are deliberately skipped for detection; original quoted math may retain comments',
            'UTF-8 codepoint offsets address the separately hashed TeX file, not PDF bytes; archive authenticity is verified by the importer',
            'No symbolic evaluation, LaTeX safety for rendering, dimensional validation or mathematical correctness claim'])
    if len(json.dumps(result,ensure_ascii=False,allow_nan=False).encode())>MAX_JSON_BYTES:raise ValueError('TeX mathematical artifact exceeds 8 MiB; cannot admit as complete')
    return result
