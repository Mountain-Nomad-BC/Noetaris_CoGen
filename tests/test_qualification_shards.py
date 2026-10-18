"""Scheduling cannot omit, duplicate or reclassify regression cases as passing."""
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import qualification_shards as q


def test_class_and_parameter_identity_retains_double_colon_inside_parameter():
    assert q.case_key('tests/test_example.py::TestExample::test_value[a::b]')==(
        'tests.test_example.TestExample','test_value[a::b]')


@pytest.mark.parametrize('workers',[0,3,True])
def test_worker_bound_is_explicit(workers):
    with pytest.raises(ValueError):q.partition(['tests/test_a.py::test_a'],workers)


def test_partition_retains_complete_files_and_every_collected_case():
    nodes=['tests/test_a.py::test_a','tests/test_a.py::test_b','tests/test_b.py::test_c','tests/test_c.py::test_d']
    groups=q.partition(nodes,2,{'tests/test_a.py':40,'tests/test_b.py':35,'tests/test_c.py':1})
    assert groups==[['tests/test_a.py'],['tests/test_b.py','tests/test_c.py']]


def xml(path,cases,skipped=0):
    suite=ET.Element('testsuite',tests=str(len(cases)),failures='0',errors='0',skipped=str(skipped))
    for index,(classname,name) in enumerate(cases):
        case=ET.SubElement(suite,'testcase',classname=classname,name=name)
        if index<skipped:ET.SubElement(case,'skipped')
    ET.ElementTree(suite).write(path,encoding='utf-8')


def test_equal_counts_cannot_hide_a_duplicated_and_missing_case(tmp_path):
    path=tmp_path/'worker.xml';xml(path,[('tests.test_a','test_a'),('tests.test_a','test_a')])
    verdict,_=q.coverage(['tests/test_a.py::test_a','tests/test_b.py::test_b'],[path])
    assert not verdict['exact'] and verdict['missing']==[('tests.test_b','test_b')]
    assert verdict['extra']==[('tests.test_a','test_a')]


def test_missing_worker_result_never_counts_as_complete(tmp_path):
    verdict,_=q.coverage(['tests/test_a.py::test_a'],[tmp_path/'absent.xml'])
    assert not verdict['exact'] and verdict['observed']==0


def test_summary_cannot_hide_a_skipped_case(tmp_path):
    path=tmp_path/'worker.xml';xml(path,[('tests.test_a','test_a')])
    root=ET.parse(path);ET.SubElement(root.getroot().find('testcase'),'skipped');root.write(path)
    verdict,_=q.coverage(['tests/test_a.py::test_a'],[path])
    assert not verdict['exact'] and not verdict['reported_counts_match_cases']


@pytest.mark.parametrize('skipped',[0,1])
def test_collection_and_workers_share_deadline_and_skips_fail_admission(tmp_path,monkeypatch,skipped):
    clock=SimpleNamespace(value=1000)
    monkeypatch.setattr(q,'time',SimpleNamespace(monotonic=lambda:clock.value))
    budgets=[]
    def run(command,**kwargs):
        if '--collect-only' in command:
            clock.value=1100
            return subprocess.CompletedProcess(command,0,'tests/test_a.py::test_a\ntests/test_b.py::test_b\n','')
        budgets.append(kwargs['timeout'])
        path=Path(next(arg.split('=',1)[1] for arg in command if arg.startswith('--junitxml=')))
        suffix='a' if command[-1]=='tests/test_a.py' else 'b'
        xml(path,[('tests.test_'+suffix,'test_'+suffix)],skipped if suffix=='a' else 0)
        return subprocess.CompletedProcess(command,0)
    monkeypatch.setattr(q.subprocess,'run',run)
    result=q.execute(tmp_path,tmp_path,{},workers=2)
    assert budgets==[1700,1700] and result['coverage_exact']
    assert result['exit_code']==(1 if skipped else 0)


@pytest.mark.parametrize('labels',[{'nsai.owner':'b'*32},None])
def test_cleanup_refuses_a_foreign_owner(tmp_path,labels):
    calls=[]
    def run(args,**kwargs):
        calls.append(args)
        if args[1]=='ps':return subprocess.CompletedProcess(args,0,b'nsai-test\n',b'')
        return subprocess.CompletedProcess(args,0,json.dumps([dict(Config=dict(Labels=labels))]).encode(),b'')
    with pytest.raises(RuntimeError,match='foreign'):q.cleanup_owned('a'*32,run=run)
    assert not any(args[1]=='rm' for args in calls)


def test_cleanup_cannot_report_success_when_inventory_is_unavailable():
    def run(args,**kwargs):return subprocess.CompletedProcess(args,1,b'',b'')
    with pytest.raises(RuntimeError,match='unavailable'):q.cleanup_owned('a'*32,run=run)
