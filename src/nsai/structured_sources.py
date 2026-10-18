"""Lossless bounded delimited evidence; values are never inferred or executed."""
import csv
import hashlib
import io
import json

from .upload_limits import ACTIVE
from .text_chunks import iter_text_chunks
from .normalization import identity_offset_map

MEDIA={'.csv':'text/csv','.tsv':'text/tab-separated-values'}
MAX_ROWS=2000
MAX_COLUMNS=100
MAX_CELLS=5000


def parse_delimited(data,media):
    if not isinstance(data,bytes) or not data or len(data)>ACTIVE.max_bytes:
        raise ValueError('Delimited source exceeds original-byte budget')
    if media not in MEDIA.values():raise ValueError('Unsupported delimited media')
    raw=data.decode('utf-8-sig',errors='strict')
    if '\x00' in raw:raise ValueError('NUL is not allowed in delimited sources')
    reader=csv.reader(io.StringIO(raw,newline=''),delimiter=',' if media=='text/csv' else '\t',strict=True)
    rows=[];spans=[];chunks=[];mapping=[];count=0;previous_line=0;chars=0
    try:
        for number,values in enumerate(reader,1):
            if number>MAX_ROWS or len(values)>MAX_COLUMNS:raise ValueError('Delimited row/column budget exceeded')
            count+=len(values)
            if count>MAX_CELLS:raise ValueError('Delimited cell budget exceeded')
            if any(len(value)>20000 for value in values):raise ValueError('Delimited cell text budget exceeded')
            locator=f'table:1:row:{number}'
            # JSON quoting preserves internal whitespace, empty strings, embedded
            # newlines and formula text. No header or numeric type is inferred.
            text=json.dumps(values,ensure_ascii=False,separators=(',',':'),allow_nan=False)
            chars+=len(text)
            if chars+number-1>ACTIVE.max_chars:raise ValueError('Delimited evidence text budget exceeded')
            rows.append(dict(locator=locator,record=number,physical_lines=[previous_line+1,reader.line_num],
                cells=[dict(locator=locator+f':column:{column}',column=column,value=value,value_type='text')
                       for column,value in enumerate(values,1)]))
            previous_line=reader.line_num
            spans.append(dict(locator=locator,global_line=number,text=text,page=None))
            mapping.append(dict(locator=locator,raw_text=text,normalized_text=text,
                                normalization='csv-decoded-record-json/1',offset_unit='unicode_codepoint',
                                offset_map=identity_offset_map(text)))
            for offset,part in iter_text_chunks(text):
                chunks.append(dict(locator=locator,offset=offset,end_offset=offset+len(part),text=part,
                                   sha256=hashlib.sha256(part.encode('utf-8')).hexdigest()))
                if len(chunks)>5000:raise ValueError('Delimited chunk budget exceeded')
    except csv.Error:
        raise ValueError('Malformed or oversized delimited record') from None
    if not rows:raise ValueError('Delimited source has no records')
    return dict(original_sha256=hashlib.sha256(data).hexdigest(),media_type=media,
        raw_text='\n'.join(span['text'] for span in spans),spans=spans,chunks=chunks,
        page_count=1,pages=[dict(page=None,status='native',complete=True,native_text_present=True)],
        normalization_map=mapping,parser_version='nsai-delimited/1',complete=True,
        warnings=['All cells remain text; no header, null, number, date, unit or formula evaluation is inferred.',
                  'Record widths may differ; blank records and empty cells are retained.'],
        structured_data=dict(schema='nsai.delimited-evidence/1',original_sha256=hashlib.sha256(data).hexdigest(),
            delimiter=',' if media=='text/csv' else '\t',encoding='utf-8-sig',header='unassigned',
            row_count=len(rows),cell_count=count,rows=rows))


def validate_delimited(data,parsed):
    # Independently reconstruct from original bytes. Reject omissions, changed
    # cells, fake completeness, foreign locators, extra authority and hash swaps.
    expected=parse_delimited(data,parsed.get('media_type'))
    encode=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
    if encode(parsed)!=encode(expected):raise ValueError('Delimited evidence does not match original source')
    return parsed
