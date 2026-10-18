"""Original, source-preserving provisional document structure; no domain dictionaries."""
import hashlib
import json
import re
import unicodedata

VERSION = 'nsai.document-units/1'


def checksum(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()).hexdigest()


def assemble_document_units(document_id, revision, source_sha256, spans):
    if not isinstance(document_id,str) or not re.fullmatch('[a-f0-9]{32}',document_id):
        raise ValueError('Invalid document identity')
    if not isinstance(source_sha256,str) or not re.fullmatch('[a-f0-9]{64}',source_sha256):
        raise ValueError('Invalid source digest')
    if not isinstance(revision,str) or not 1<=len(revision)<=200 or not isinstance(spans,list) or len(spans)>10000:
        raise ValueError('Invalid unit envelope')
    source = dict(document_id=document_id,revision=revision,source_sha256=source_sha256)
    units=[];seen=set();total=0;headings=[]
    for span in spans:
        if not isinstance(span,dict):
            raise ValueError('Invalid source span')
        text,locator = span.get('text'),span.get('locator')
        if not isinstance(text,str) or len(text)>32768 or not isinstance(locator,str) or not 1<=len(locator)<=200 or locator in seen:
            raise ValueError('Invalid or duplicate source span')
        seen.add(locator);total+=len(text.encode('utf-8'))
        if total>4*1024*1024:
            raise ValueError('Document units source budget exceeded')
        page=span.get('page')
        if page is not None and (type(page) is not int or not 1<=page<=1000):
            raise ValueError('Invalid source page')
        stripped=text.strip();signals=[]
        if '\ufffd' in text:signals.append('replacement-character-present')
        if any(unicodedata.category(char)=='Cc' and char not in '\n\r\t' for char in text):signals.append('control-character-present')
        if any(unicodedata.category(char)=='Cf' for char in text):signals.append('format-character-present')
        # Math-like tokens are preserved; they do not imply OCR corruption.
        math_like=bool(re.search(r'[=∫∑√≤≥±]|\\(?:frac|sum|int)\b',stripped))
        if math_like:signals.append('math-like-wording')
        numbered=re.match(r'^(\d{1,2}(?:\.\d{1,2}){0,4})[.)]?\s+([^\W\d_].*)$',stripped,re.UNICODE)
        markdown=re.match(r'^(#{1,6})\s+\S',stripped)
        short_title=bool(stripped and len(stripped)<=100 and len(stripped.split())<=12 and sum(c.isalpha() for c in stripped)>=8 and stripped.isupper())
        heading=bool(not math_like and '\n' not in stripped and (numbered or markdown or short_title))
        level=None
        if heading:
            kind='heading_candidate'
            level=len(markdown[1]) if markdown else len(numbered[1].split('.')) if numbered else 1
        elif not stripped:
            kind='unknown'
        elif '\t' in text and text.count('\t')>=2 or stripped.count('|')>=3:
            kind='table_candidate';signals.append('delimiter-layout-only')
        elif not math_like and re.match(r'^(?:[-*•]|\d{1,3}[.)])\s+\S',stripped):
            kind='list_item_candidate'
        else:
            kind='paragraph_candidate'
        identity=checksum(dict(schema=VERSION,source=source,locator=locator,text=text))
        if heading:
            while headings and headings[-1][0]>=level:headings.pop()
        parent=headings[-1][1] if headings else None
        units.append(dict(id=identity,kind=kind,text=text,source=source,locator=locator,page=page,
            char_start=0,char_end=len(text),span_sha256=hashlib.sha256(text.encode()).hexdigest(),
            section_candidate_id=parent,heading_level_candidate=level,quality_signals=signals,
            quality_verified=False,confidence_probability=None,state='candidate',authority_granted=False))
        if heading:headings.append((level,identity))
    result=dict(schema_version=VERSION,source=source,units=units,source_spans=len(spans),source_utf8_bytes=total,
        processing_complete=True,state='candidate',authority_granted=False,
        limitations=['Unit types and section hierarchy are provisional formatting heuristics.',
                    'No table reconstruction, reading-order correction, OCR quality score or scientific interpretation is implied.',
                    'No original text is normalized, silently discarded or promoted to canon.'])
    result['artifact_sha256']=checksum(result)
    if len(json.dumps(result,ensure_ascii=False,allow_nan=False).encode())>16*1024*1024:
        raise ValueError('Document units output budget exceeded')
    return result
