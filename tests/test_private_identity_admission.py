"""Per-user credentials cannot fall through to legacy shared-project content."""
import json
import pytest
from fastapi.testclient import TestClient
from nsai import api


@pytest.mark.parametrize('kind,admitted',[('local-user',False),('legacy-role',True)])
def test_capabilities_describe_content_admission_without_opening_routes(monkeypatch,kind,admitted):
    identity=dict(actor='local-user-alice' if kind=='local-user' else 'local-operator',
        role='operator',permissions=['read','ingest','chat','propose'],identity_kind=kind)
    monkeypatch.setattr(api,'principal',lambda *_:identity)
    monkeypatch.setattr(api,'resolve_principal',lambda *_:identity)
    monkeypatch.setattr(api,'rate_window',__import__('collections').deque())
    client=TestClient(api.app)
    response=client.get('/v1/capabilities')
    assert response.status_code==200 and response.headers['cache-control']=='no-store'
    assert response.json()['content_access']['admitted'] is admitted
    if not admitted:
        assert response.json()['content_access']['reason']
        assert client.get('/v1/documents').status_code==503


@pytest.mark.parametrize('method,path',[
    ('GET','/v1/documents'),('GET','/v1/claims'),('GET','/v1/search?q=private'),
    ('POST','/v1/chat'),('POST','/v1/reason'),('GET','/v1/learning'),
    ('GET','/v1/audit'),('GET','/v1/memory/'+'a'*32),
    ('GET','/v1/knowledge/'+'a'*32),('GET','/v1/knowledge/'+'a'*32+'/formulas'),
    ('GET','/v1/sources/'+'a'*32+'/original'),('HEAD','/v1/sources/'+'a'*32+'/original'),
    ('GET','/v1/governed/records'),('GET','/v1/submission/evidence'),
])
def test_local_user_is_withheld_from_unintegrated_private_routes(monkeypatch,method,path):
    monkeypatch.setattr(api,'principal',lambda *_:dict(actor='local-user-alice',role='operator',
        permissions=['read','ingest','chat','propose'],identity_kind='local-user'))
    response=TestClient(api.app).request(method,path)
    assert response.status_code==503
    assert response.headers['cache-control']=='no-store'
    if method!='HEAD':assert 'not yet admitted' in response.json()['detail']


def test_real_registry_principal_cannot_inherit_shared_project_content(tmp_path,monkeypatch):
    from nsai.security import FILES
    for setting in FILES.values():monkeypatch.delenv(setting,raising=False)
    credential=tmp_path/'alice-token';credential.write_text('a'*48,encoding='utf-8')
    registry=tmp_path/'identities.json'
    registry.write_text(json.dumps(dict(schema_version='nsai.local-identities/1',identities=[
        dict(actor='local-user-alice',role='operator',token_file=str(credential.resolve()))])),encoding='utf-8')
    monkeypatch.setenv('NSAI_LOCAL_IDENTITIES_FILE',str(registry.resolve()))
    with TestClient(api.app) as client:
        response=client.get('/v1/documents',headers={'Authorization':'Bearer '+'a'*48})
    assert response.status_code==503 and 'not yet admitted' in response.json()['detail']
