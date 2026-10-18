"""JSON originals preserve types and number spellings without granting authority."""
from copy import deepcopy
import pytest
from nsai.ingestion import parse_source,validate_parsed_source


def test_types_numeric_spelling_empty_containers_and_order_are_preserved():
    data=b'{"null":null,"false":false,"zero":0,"negative":-0,"decimal":0.1000e+02,"empty":"","object":{},"array":[]}'
    parsed=parse_source(data,'source.json');records=parsed['structured_data']['records']
    assert [(r['pointer_fragment'],r['value_type'],r['json_value']) for r in records]==[
        ('#','object',None),('#/null','null','null'),('#/false','boolean','false'),('#/zero','number','0'),
        ('#/negative','number','-0'),('#/decimal','number','0.1000e+02'),('#/empty','string','""'),
        ('#/object','object',None),('#/array','array',None)]
    assert records[0]['child_count']==8
    assert validate_parsed_source(data,deepcopy(parsed))==parsed


def test_pointer_escapes_and_unicode_do_not_merge_distinct_members():
    parsed=parse_source('{"a/b":{"~x":["e\\u0301","\u00e9"]},"\\u0000":"\\u0000"}'.encode(),'source.json')
    records=parsed['structured_data']['records']
    assert [r['pointer_fragment'] for r in records]==['#','#/a~1b','#/a~1b/~0x','#/a~1b/~0x/0','#/a~1b/~0x/1','#/%00']
    assert records[3]['json_value']=='"e\\u0301"' and records[4]['json_value']=='"\\u00e9"'
    assert records[5]['json_value']=='"\\u0000"'
    assert all('\x00' not in r['locator'] for r in records)


@pytest.mark.parametrize('data',[b'{"x":1,"x":2}',b'NaN',b'Infinity',b'{} trailing',b'\xff',b'[1,]',b'{"x":}',b'['*18+b'0'+b']'*18])
def test_ambiguous_or_invalid_source_is_rejected_whole(data):
    with pytest.raises(ValueError):parse_source(data,'source.json')


@pytest.mark.parametrize('data',[b'null',b'false',b'0',b'""',b'{}',b'[]',b'\xef\xbb\xbf{"x":1}'])
def test_valid_root_values_are_evidence_not_discarded_as_empty(data):
    parsed=parse_source(data,'source.json')
    assert parsed['complete'] and parsed['spans'] and parsed['chunks']
    assert validate_parsed_source(data,parsed)==parsed


@pytest.mark.parametrize('mutate',[
    lambda p:p['structured_data']['records'].pop(),
    lambda p:p['structured_data']['records'][1].update(value_type='string'),
    lambda p:p['structured_data']['records'][1].update(json_value='1'),
    lambda p:p['structured_data']['records'][1].update(pointer_fragment='#/foreign'),
    lambda p:p['spans'].pop(),lambda p:p['chunks'].pop(),lambda p:p.update(page_count=True),
    lambda p:p.update(authority='canonical'),
])
def test_changed_typed_records_and_omissions_fail_custody(mutate):
    data=b'{"x":-0.00}';parsed=parse_source(data,'source.json');mutate(parsed)
    with pytest.raises(ValueError,match='does not match original'):validate_parsed_source(data,parsed)


def test_uploaded_authority_looking_keys_remain_plain_evidence():
    from nsai.source_dependencies import collect_sources
    parsed=parse_source(b'{"actor":"local-admin","document_id":"foreign","source_ids":["secret"],"authority_granted":true}','source.json')
    assert collect_sources(parsed)==[]


def test_json_bounds_refuse_late_records_and_excessive_number_or_pointer():
    for data in [b'['+b'0,'*5000+b'0]',b'1'*129,('{"'+'a'*200+'":0}').encode()]:
        with pytest.raises(ValueError):parse_source(data,'source.json')
