"""Data-health reports discover defects while retaining source bytes."""
import json
from nsai.source_health import inspect_file
import pytest


def write(tmp_path,name,raw):
    path=tmp_path/name;path.write_bytes(raw);return path


def test_jsonl_duplicate_ids_active_heads_and_mixed_families(tmp_path):
    records=[dict(record_family='claim',id='c1',active_head=True,scope_id='s1'),
             dict(record_family='claim',id='c1',active_head=True,scope_id='s1'),
             dict(record_family='observation',id='o1')]
    raw=b'\n'.join(json.dumps(row).encode() for row in records)+b'\n'
    path=write(tmp_path,'source.jsonl',raw);result=inspect_file(path)
    assert {r['code'] for r in result['issues']}=={'duplicate_record_id','duplicate_active_head','mixed_record_families'}
    assert result['physical_lines']==3 and result['records']==3 and result['original_unchanged']
    assert path.read_bytes()==raw


def test_malformed_record_duplicate_json_keys_and_blank_lines_are_not_skipped(tmp_path):
    raw=b'{"id":"a","id":"b"}\n\n{"id":"c"}\nnot json\n'
    result=inspect_file(write(tmp_path,'source.jsonl',raw))
    assert result['records']==1 and [i['line'] for i in result['issues']]==[1,2,4]
    assert result['schema_status'].startswith('unclassified')


def test_graph_duplicates_and_orphan_endpoints_are_identified(tmp_path):
    value=dict(nodes=[dict(id='n1'),dict(id='n1')],edges=[dict(id='e1',source_id='n1',target_id='missing')])
    result=inspect_file(write(tmp_path,'graph.json',json.dumps(value).encode()))
    assert {i['code'] for i in result['issues']}=={'duplicate_graph_node','unresolved_graph_endpoint'}


def test_named_excluded_tree_is_readable_for_audit_without_promotion(tmp_path):
    folder=tmp_path/'NSAI_MASTER_CORPUS_REBUILD';folder.mkdir();path=write(folder,'bad.json',b'{"x":1,"x":2}')
    with pytest.raises(ValueError,match='Duplicate JSON key'):inspect_file(path)
    assert path.read_bytes()==b'{"x":1,"x":2}'


def test_issue_budget_reports_incompleteness_instead_of_false_clean_status(tmp_path):
    result=inspect_file(write(tmp_path,'flood.jsonl',b'bad\n'*1005))
    assert len(result['issues'])==1000 and result['omitted_issues']==5 and result['audit_complete'] is False


def test_empty_and_bare_carriage_return_are_not_extra_jsonl_records(tmp_path):
    assert inspect_file(write(tmp_path,'empty.jsonl',b''))['issues'][0]['code']=='empty_jsonl'
    result=inspect_file(write(tmp_path,'bad.jsonl',b'{}\r{}\n'))
    assert result['records']==0 and result['physical_lines']==1
