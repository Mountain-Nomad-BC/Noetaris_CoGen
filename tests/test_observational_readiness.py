import importlib.util
from pathlib import Path
import pytest
import httpx

spec=importlib.util.spec_from_file_location('observational_readiness',Path(__file__).resolve().parents[1]/'scripts/verify_system.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def deny_network(monkeypatch):
    def forbidden(*args,**kwargs):
        pytest.fail('Network client constructed before admission')
    monkeypatch.setattr(module.httpx,'Client',forbidden)

def test_no_flag_performs_no_network(monkeypatch):
    deny_network(monkeypatch)
    with pytest.raises(SystemExit) as error:
        module.main([])
    assert error.value.code==2

@pytest.mark.parametrize('base',['http://example.org:8787','http://127.0.0.1:0','http://127.0.0.1:65536','http://127.0.0.1:notaport','http://user:secret@127.0.0.1:8787','https://127.0.0.1:8787','http://127.0.0.1:8787/path','http://127.0.0.1:8787?x=1','http://127.0.0.1'])
def test_invalid_target_rejected_before_network(monkeypatch,base):
    deny_network(monkeypatch)
    monkeypatch.setenv('NSAI_BASE_URL',base)
    with pytest.raises(SystemExit) as error:
        module.main(['--readiness-only'])
    assert error.value.code==2

@pytest.mark.parametrize('payload',[b'{broken',b'[]',b'\xff',b'x'*8193,b'{"status":"wrong"}'])
def test_invalid_bounded_responses_fail_cleanly(monkeypatch,tmp_path,payload):
    original=httpx.Client
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(200,content=payload)
    monkeypatch.setattr(module.httpx,'Client',lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs))
    monkeypatch.setattr(module,'ROOT',tmp_path)
    monkeypatch.setenv('NSAI_BASE_URL','http://127.0.0.1:8787')
    assert module.main(['--readiness-only'])==1
    assert len(calls)==2 and all(r.method=='GET' for r in calls)
    report=(tmp_path/'evidence/implementation/readiness-current.json').read_text()
    assert 'FAIL' in report and 'false' in report

def test_valid_observation_only_gets_health_and_readiness(monkeypatch,tmp_path):
    original=httpx.Client
    calls=[]
    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200,json={'status':'alive' if request.url.path=='/healthz' else 'ready'})
    monkeypatch.setattr(module.httpx,'Client',lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs))
    monkeypatch.setattr(module,'ROOT',tmp_path)
    monkeypatch.setenv('NSAI_BASE_URL','http://127.0.0.1:8787')
    assert module.main(['--readiness-only'])==0
    assert calls==['/healthz','/readyz']
