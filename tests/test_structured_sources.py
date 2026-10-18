"""Original-custody and no-coercion boundaries for business source records."""
from copy import deepcopy
import hashlib
import pytest
from nsai.ingestion import parse_source,validate_parsed_source
from nsai.structured_sources import parse_delimited


def test_csv_preserves_distinct_values_blank_rows_and_multiline_locations():
    data=b'\xef\xbb\xbfName,Name,Amount\r\n"a,b","x\r\ny",001\r\n,0,\r\n\r\n"=SUM(A1:A2)","  spaced  ",null\r\n'
    parsed=parse_source(data,'business.csv')
    table=parsed['structured_data'];rows=table['rows']
    assert table['row_count']==5 and table['cell_count']==12
    assert [cell['value'] for cell in rows[1]['cells']]==['a,b','x\r\ny','001']
    assert rows[1]['physical_lines']==[2,3]
    assert [cell['value'] for cell in rows[2]['cells']]==['','0','']
    assert rows[3]['cells']==[]
    assert [cell['value'] for cell in rows[4]['cells']]==['=SUM(A1:A2)','  spaced  ','null']
    assert rows[4]['cells'][1]['locator']=='table:1:row:5:column:2'
    assert table['header']=='unassigned'
    assert table['original_sha256']==hashlib.sha256(data).hexdigest()
    assert validate_parsed_source(data,deepcopy(parsed))==parsed


def test_tsv_delimiter_and_unicode_are_not_guessed_or_normalized():
    data='e\u0301\t\u00e9\t1,234\n'.encode()
    parsed=parse_source(data,'data.TSV')
    assert [cell['value'] for cell in parsed['structured_data']['rows'][0]['cells']]==['e\u0301','\u00e9','1,234']
    assert len(parsed['spans'])==1
    assert parsed['media_type']=='text/tab-separated-values'


@pytest.mark.parametrize('mutate',[
    lambda p:p['structured_data']['rows'][1]['cells'][0].update(value='tampered'),
    lambda p:p['structured_data']['rows'].pop(),
    lambda p:p['spans'].pop(),
    lambda p:p['chunks'].pop(),
    lambda p:p.update(complete=False),
    lambda p:p.update(page_count=True),
    lambda p:p.update(authority='canonical'),
    lambda p:p['structured_data']['rows'][1]['cells'][0].update(locator='foreign:cell'),
])
def test_api_validation_refuses_changed_or_missing_structured_evidence(mutate):
    data=b'name,value\na,0\n';parsed=parse_source(data,'a.csv');mutate(parsed)
    with pytest.raises(ValueError,match='does not match original'):validate_parsed_source(data,parsed)


@pytest.mark.parametrize('data',[b'',b'\xff,2',b'a\x00,b',b'"unterminated,2'])
def test_invalid_encoding_and_ambiguous_records_are_rejected_whole(data):
    with pytest.raises(ValueError):parse_source(data,'a.csv')


def test_bounds_refuse_whole_source_without_truncation():
    for data in [b'a\n'*2001,(','.join(['a']*101)).encode(),('x'*20001).encode()]:
        with pytest.raises(ValueError):parse_delimited(data,'text/csv')


def test_long_cell_chunks_cover_entire_exact_serialized_record():
    data=('"'+('x'*5000)+'",\n').encode();parsed=parse_source(data,'long.csv')
    assert ''.join(chunk['text'] for chunk in parsed['chunks'])==parsed['spans'][0]['text']
    assert validate_parsed_source(data,parsed)==parsed


def test_ordinary_text_cannot_smuggle_structured_authority():
    parsed=parse_source(b'ordinary text','a.txt');parsed['structured_data']={'authority':'canonical'}
    with pytest.raises(ValueError,match='supported structured media'):validate_parsed_source(b'ordinary text',parsed)


@pytest.mark.parametrize('name,data',[('a.csv',b'a,b\r\n,0\r\n'),('a.tsv','name\tvalue\n\u00e9\t001\n'.encode()),('a.json',b'{"zero":0,"missing":null,"false":false,"decimal":-0.100e+2,"empty":[]}')])
def test_real_parser_subprocess_preserves_structured_records(monkeypatch,tmp_path,name,data):
    import base64
    from pathlib import Path
    from fastapi.testclient import TestClient
    from nsai.parser import app
    secret=tmp_path/'token';secret.write_text('synthetic-delimited-parser-token-0123456789',encoding='utf-8')
    monkeypatch.setenv('NSAI_PARSER_TOKEN_FILE',str(secret))
    monkeypatch.setenv('PYTHONPATH',str(Path(__file__).resolve().parents[1]/'src'))
    with TestClient(app) as client:
        response=client.post('/parse',headers={'Authorization':'Bearer '+secret.read_text(encoding='utf-8')},
            json=dict(filename=name,data=base64.b64encode(data).decode()))
        assert response.status_code==200,response.text[:300]
        assert response.json()==parse_source(data,name)
