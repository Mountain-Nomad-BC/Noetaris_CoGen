import importlib.util
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('stack_identity',ROOT/'scripts/qualify_local_stack.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def fixture():
    identity=dict(run_id='owned-stack-1234',source_sha256='a'*64,image_digest='sha256:'+'b'*64,effective_config_sha256='c'*64,producer_sha256='d'*64)
    receipt=dict(status='PASS',cases=[dict(pass_=True)],cleanup_complete=True,sources_before={'src/a.py':'a'*64},sources_after={'src/a.py':'a'*64},identity_capture_complete=True)
    return identity,receipt

def test_final_scoped_admission_not_release():
    identity,receipt=fixture()
    result=module.stack_envelope(json.dumps(receipt).encode(),identity)
    assert result['admission']['status']=='PASS_SCOPED'
    assert result['certification'] is False and result['release_approval'] is False

@pytest.mark.parametrize('change',[dict(status='FAIL'),dict(cases=[]),dict(cases=[dict(pass_=False)]),dict(cases=[dict(pass_=1)]),dict(cleanup_complete=False),dict(identity_capture_complete=False),dict(sources_after={'src/a.py':'changed'})])
def test_failure_incomplete_cleanup_source_drift_denied(change):
    identity,receipt=fixture();receipt.update(change)
    result=module.stack_envelope(json.dumps(receipt).encode(),identity)
    assert result['receipt']['status']=='FAIL' and result['receipt']['exit_code']==1
    assert result['admission']['status']=='UNVERIFIED'

@pytest.mark.parametrize('field',['image_digest','effective_config_sha256','source_sha256','producer_sha256','run_id'])
def test_mismatched_expected_identity_rejected(field):
    identity,receipt=fixture();raw=json.dumps(receipt).encode()
    result=module.stack_envelope(raw,identity)
    expected=dict(identity);expected[field]='changed'
    assert module.admit_receipt(result['receipt'],raw,expected)['status']=='UNVERIFIED'

@pytest.mark.parametrize('change',[dict(exit_code=1),dict(exit_code=False),dict(captured_at=(datetime.now(timezone.utc)-timedelta(days=2)).isoformat())])
def test_false_exit_or_stale_sidecar_rejected(change):
    identity,receipt=fixture();raw=json.dumps(receipt).encode()
    envelope=module.stack_envelope(raw,identity)['receipt'];envelope.update(change)
    assert module.admit_receipt(envelope,raw,identity)['status']=='UNVERIFIED'

def test_body_tamper_denied():
    identity,receipt=fixture();raw=json.dumps(receipt).encode()
    envelope=module.stack_envelope(raw,identity)['receipt']
    assert module.admit_receipt(envelope,raw+b' ',identity)['status']=='UNVERIFIED'

def test_runtime_policy_omits_private_sources_environment_and_names():
    data={'Image':'sha256:'+'f'*64,'Config':{'User':'10001','Env':['PASSWORD=private-credential'],'Cmd':['uvicorn','nsai.api:app','private-command-argument']},'HostConfig':{'Memory':10,'NanoCpus':20,'PidsLimit':30},'Mounts':[{'Source':'C:/private-source','Destination':'/run/secrets/api_token','Type':'bind','RW':False}]}
    policy=module.public_runtime_policy(data,['internal'])
    raw=json.dumps(policy)
    assert 'private-' not in raw and 'PASSWORD' not in raw and 'Source' not in raw
    assert policy['mounts']==[dict(destination='/run/secrets/api_token',readonly=True,type='bind')]
    changed=json.loads(json.dumps(data));changed['HostConfig']['Memory']=11
    assert module.identity_hash(policy)!=module.identity_hash(module.public_runtime_policy(changed,['internal']))

def test_sidecar_written_after_final_raw_receipt_and_no_docker(monkeypatch,tmp_path):
    identity,receipt=fixture()
    stack=object.__new__(module.Stack)
    stack.output=tmp_path;stack.run_id=identity['run_id'];stack.before=receipt['sources_before'];stack.api_image=identity['image_digest'];stack.receipt=receipt
    stack.save()
    monkeypatch.setattr(module,'command',lambda *args,**kwargs:pytest.fail('Sidecar must not access Docker'))
    stack.save_identity()
    sidecar=json.loads((tmp_path/'identity.json').read_text())
    assert sidecar['receipt']['evidence_sha256']==module.hashlib.sha256((tmp_path/'receipt.json').read_bytes()).hexdigest()

@pytest.mark.parametrize('change,expected',[(dict(),0),(dict(identity_capture_complete=False),1),(dict(cleanup_complete=False),1),(dict(status='FAIL'),1)])
def test_main_exit_matches_final_qualification(monkeypatch,tmp_path,change,expected):
    identity,receipt=fixture();receipt.update(change)
    raw=json.dumps(receipt).encode()
    sidecar=module.stack_envelope(raw,identity);sidecar['identity']=identity
    (tmp_path/'receipt.json').write_bytes(raw)
    (tmp_path/'identity.json').write_text(json.dumps(sidecar))
    class FakeStack:
        def __init__(self,*args):
            self.output=tmp_path;self.receipt=receipt;self.cases=receipt['cases']
        def execute(self):
            pass
    monkeypatch.setattr(module,'Stack',FakeStack)
    monkeypatch.setattr(sys,'argv',['qualify_local_stack.py','--output',str(tmp_path)])
    assert module.main()==expected

def test_cli_propagates_main_exit():
    import ast
    tree=ast.parse((ROOT/'scripts/qualify_local_stack.py').read_text())
    guard=tree.body[-1]
    assert isinstance(guard,ast.If) and isinstance(guard.body[0],ast.Raise)
    assert isinstance(guard.body[0].exc,ast.Call) and guard.body[0].exc.func.id=='SystemExit'
