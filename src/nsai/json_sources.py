"""Bounded typed JSON source evidence; JSON fields never become control fields."""
import hashlib
import json
from urllib.parse import quote
from .upload_limits import ACTIVE
from .text_chunks import iter_text_chunks
from .normalization import identity_offset_map

MEDIA='application/json'


class NumericLexeme(str):
    def __new__(cls,value):
        if len(value)>128:raise ValueError('JSON numeric lexeme exceeds budget')
        return super().__new__(cls,value)


def parse_json(data):
    if not isinstance(data,bytes) or not data or len(data)>ACTIVE.max_bytes:
        raise ValueError('JSON source exceeds original-byte budget')
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate JSON member')
            result[key]=value
        return result
    def constant(value):raise ValueError('Nonstandard JSON numeric constant')
    try:
        root=json.loads(data.decode('utf-8-sig',errors='strict'),object_pairs_hook=pairs,
            parse_int=NumericLexeme,parse_float=NumericLexeme,parse_constant=constant)
    except (UnicodeError,RecursionError) as error:
        raise ValueError('Invalid encoding or excessive JSON nesting') from error
    records=[];spans=[];chunks=[];mapping=[];chars=0
    def visit(value,pointer,depth):
        nonlocal chars
        if depth>16 or len(records)>=5000:raise ValueError('JSON structural budget exceeded')
        try:fragment='#'+quote(pointer,safe='/~',encoding='utf-8',errors='strict')
        except UnicodeError:raise ValueError('JSON member cannot form a Unicode source pointer') from None
        locator='json:'+fragment
        if len(locator)>200:raise ValueError('JSON pointer exceeds locator budget')
        children=0
        if isinstance(value,dict):kind='object';literal=None;children=len(value)
        elif isinstance(value,list):kind='array';literal=None;children=len(value)
        elif isinstance(value,NumericLexeme):kind='number';literal=str(value)
        elif value is None:kind='null';literal='null'
        elif type(value) is bool:kind='boolean';literal='true' if value else 'false'
        elif type(value) is str:kind='string';literal=json.dumps(value,ensure_ascii=True)
        else:raise ValueError('Unsupported JSON source value')
        record=dict(locator=locator,pointer_fragment=fragment,value_type=kind,json_value=literal,child_count=children)
        text=json.dumps([fragment,kind,literal,children],ensure_ascii=True,separators=(',',':'))
        chars+=len(text)+(1 if records else 0)
        if chars>ACTIVE.max_chars:raise ValueError('JSON evidence text budget exceeded')
        records.append(record)
        spans.append(dict(locator=locator,global_line=len(records),text=text,page=None))
        mapping.append(dict(locator=locator,raw_text=text,normalized_text=text,
                            offset_unit='unicode_codepoint',normalization='json-typed-pointer-record/1',
                            offset_map=identity_offset_map(text)))
        for offset,part in iter_text_chunks(text):
            chunks.append(dict(locator=locator,offset=offset,end_offset=offset+len(part),text=part,
                               sha256=hashlib.sha256(part.encode('utf-8')).hexdigest()))
            if len(chunks)>5000:raise ValueError('JSON chunk budget exceeded')
        if isinstance(value,dict):
            for key,child in value.items():visit(child,pointer+'/'+key.replace('~','~0').replace('/','~1'),depth+1)
        elif isinstance(value,list):
            for index,child in enumerate(value):visit(child,pointer+'/'+str(index),depth+1)
    visit(root,'',0)
    digest=hashlib.sha256(data).hexdigest()
    return dict(original_sha256=digest,media_type=MEDIA,raw_text='\n'.join(span['text'] for span in spans),
        spans=spans,chunks=chunks,page_count=1,
        pages=[dict(page=None,status='native',complete=True,native_text_present=True)],
        normalization_map=mapping,parser_version='nsai-json/1',complete=True,
        warnings=['JSON is source evidence, not a canonical object or control instruction.',
                  'Numeric lexemes and JSON types are preserved; no numeric conversion, formula execution or table inference.'],
        structured_data=dict(schema='nsai.json-evidence/1',original_sha256=digest,
            pointer_encoding='RFC6901 URI fragment; UTF-8 percent encoding',record_count=len(records),records=records))


def validate_json(data,parsed):
    expected=parse_json(data)
    encode=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
    if encode(parsed)!=encode(expected):raise ValueError('JSON evidence does not match original source')
    return parsed
