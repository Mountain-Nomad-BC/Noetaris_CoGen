"""Fail-closed deployment evidence and actual-runtime drift regressions."""
import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_deployment_stages import runtime_violations,assess_regression,assess_frontend_operations


def services():
    networks={'api':['data','parser','model','edge','encoder'],'db':['data'],
        'parser':['parser'],'llama-cpp':['model'],'encoder':['encoder'],'ui':['edge','front']}
    return [dict(service=name,running=True,health='healthy',read_only=True,
        user={'db':'70:70','ui':'101:101'}.get(name,'10001:10001'),privileged=False,
        cap_drop=['ALL'],cap_add=[],security_opt=['no-new-privileges:true'],memory=1024**3,
        nano_cpus=2*10**9,pids_limit=128,network_mode='owned_'+nets[0],
        pid_mode='',ipc_mode='private',devices=False,
        published_ports=[dict(container='8080/tcp',host_ip='127.0.0.1',host_port='8790')] if name=='ui' else [],
        networks=[dict(name=n,owned=True,internal=n!='front') for n in nets]) for name,nets in networks.items()]


def test_exact_six_service_runtime_passes():
    assert runtime_violations(services())==[]


@pytest.mark.parametrize('key,value',[
    ('read_only',False),('running',False),('health','unhealthy'),('user','0:0'),
    ('privileged',True),('cap_drop',[]),('cap_add',['SYS_ADMIN']),('security_opt',[]),
    ('security_opt',['no-new-privileges:true','seccomp=unconfined']),('memory',0),
    ('memory',9*1024**3),('nano_cpus',0),('pids_limit',-1),('network_mode','host'),
    ('network_mode','container:foreign'),('pid_mode','host'),('ipc_mode','host'),('devices',True),
    ('published_ports',[dict(container='8787/tcp',host_ip='127.0.0.1',host_port='8791')]),
])
def test_runtime_drift_denies_local_stage(key,value):
    runtime=services();runtime[0][key]=value
    assert runtime_violations(runtime)


@pytest.mark.parametrize('case',['egress','foreign','extra-network','missing-network','duplicate','missing',
                                  'wrong-ui-port','public-ui-port','no-ui-port'])
def test_membership_egress_and_exact_port_contract(case):
    runtime=services();api=runtime[0];ui=runtime[-1]
    if case=='egress':api['networks'][0]['internal']=False
    elif case=='foreign':api['networks'][0]['owned']=False
    elif case=='extra-network':api['networks'].append(dict(name='unexpected',owned=True,internal=True))
    elif case=='missing-network':api['networks'].pop()
    elif case=='duplicate':runtime.append(copy.deepcopy(api))
    elif case=='missing':runtime.pop()
    elif case=='wrong-ui-port':ui['published_ports'][0]['host_port']='8791'
    elif case=='public-ui-port':ui['published_ports'][0]['host_ip']='0.0.0.0'
    elif case=='no-ui-port':ui['published_ports']=[]
    assert runtime_violations(runtime)


def evidence(tmp_path):
    source={'src/app.py':'source','tests/test_app.py':'test'}
    identity=dict(images=dict(api='api-image',db='db-image'))
    receipt=dict(status='PASS_SCOPED',coverage_exact=True,source_unchanged=True,source_before=source,
        api_image='api-image',db_image='db-image',cleanup=dict(complete=True),
        counts=dict(tests=1,failures=0,errors=0,skipped=0),result=dict(exit_code=0,timed_out=False))
    (tmp_path/'collection.json').write_text(json.dumps(['tests/test_app.py::test_works']))
    (tmp_path/'tests.xml').write_text('<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0">'
        '<testcase classname="tests.test_app" name="test_works"/></testsuite></testsuites>')
    return source,identity,receipt


def test_current_exact_noskip_regression_passes(tmp_path):
    source,identity,receipt=evidence(tmp_path)
    (tmp_path/'receipt.json').write_text(json.dumps(receipt))
    assert assess_regression(tmp_path,identity,source)['status']=='PASS_SCOPED'


@pytest.mark.parametrize('case',['source','test-source','image','skip','cleanup','case-missing',
    'forged-counts','timeout','exit','failed-verdict','changing-source'])
def test_stale_failed_incomplete_or_forged_regression_cannot_pass(tmp_path,case):
    source,identity,receipt=evidence(tmp_path)
    if case=='source':source={**source,'src/app.py':'changed'}
    elif case=='test-source':source={**source,'tests/test_app.py':'changed'}
    elif case=='image':identity['images']['api']='new-image'
    elif case=='skip':
        receipt['counts']['skipped']=1
        p=tmp_path/'tests.xml';p.write_text(p.read_text().replace('skipped="0"','skipped="1"').replace('/>','><skipped/></testcase>'))
    elif case=='cleanup':receipt['cleanup']['complete']=False
    elif case=='case-missing':(tmp_path/'collection.json').write_text(json.dumps(['tests/test_app.py::test_other']))
    elif case=='forged-counts':receipt['counts']['tests']=2
    elif case=='timeout':receipt['result']['timed_out']=True
    elif case=='exit':receipt['result']['exit_code']=1
    elif case=='failed-verdict':receipt['status']='INCOMPLETE_OR_FAILED'
    elif case=='changing-source':receipt['source_unchanged']=False
    (tmp_path/'receipt.json').write_text(json.dumps(receipt))
    assert assess_regression(tmp_path,identity,source)['status']=='NEEDS_CURRENT_RUN'


def browser_receipt():
    roles={'operator':{'read'},'viewer':{'read'},'reviewer':{'read','review'},'admin':{'read','review','admin'}}
    pages={'developers':('read','/v1/capabilities'),'models':('read','/v1/model/status'),'integrations':('read','/v1/integrations/status'),
        'analytics':('admin','/v1/admin/resources'),'observability':('admin','/v1/admin/resources'),
        'audit':('review','/v1/audit'),'governance':('admin','/v1/admin/security'),'settings':('admin','/v1/admin/security')}
    checks=[];responses=[]
    for role,permissions in roles.items():
        for page,(permission,path) in pages.items():
            allowed=permission in permissions
            checks.append(dict(role=role,page=page,allowed=allowed,passed=True,
                               **(dict(live_rows=3) if allowed else dict(explicit_permission_denial=True))))
            if allowed:responses.append(dict(role=role,path=path,status=200))
    return dict(status='PASS_SCOPED',identity={'image':'current'},identity_unchanged=True,
                checks=checks,page_errors=[],api_responses=responses)


def test_complete_current_four_role_browser_receipt_is_required():
    assert assess_frontend_operations(browser_receipt(),{'image':'current'})['status']=='PASS_SCOPED'


@pytest.mark.parametrize('case',['missing-page','duplicate','stale-image','permission','empty-rows',
    'denial-missing','runtime-error','server-error','no-api-proof','changed-runtime'])
def test_frontend_html_or_partial_success_cannot_grant_operations_pass(case):
    receipt=browser_receipt()
    if case=='missing-page':receipt['checks'].pop()
    elif case=='duplicate':receipt['checks'][-1]=receipt['checks'][0]
    elif case=='stale-image':receipt['identity']['image']='old'
    elif case=='permission':receipt['checks'][0]['allowed']=False
    elif case=='empty-rows':receipt['checks'][0]['live_rows']=0
    elif case=='denial-missing':next(c for c in receipt['checks'] if not c['allowed'])['explicit_permission_denial']=False
    elif case=='runtime-error':receipt['page_errors']=['exception']
    elif case=='server-error':receipt['api_responses'][0]['status']=500
    elif case=='no-api-proof':receipt['api_responses']=[]
    elif case=='changed-runtime':receipt['identity_unchanged']=False
    assert assess_frontend_operations(receipt,{'image':'current'})['status']=='NEEDS_CURRENT_RUN'
