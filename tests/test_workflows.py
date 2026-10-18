import hashlib
from dataclasses import replace
from io import BytesIO
import pytest
from fastapi.testclient import TestClient
from nsai.ingestion import parse_source
from nsai.security import CentralConfiguration
from nsai.vendor.px_memory_plan import build_memory_query_plan, validate_memory_query_plan
from nsai.vendor.remy_manifest import TurnBurnManifest, TurnBurnManifestDocument

def text_pdf(text='Pump-X maximum operating temperature is 75 C'):
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
    writer=PdfWriter(); page=writer.add_blank_page(width=612,height=792)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    stream=DecodedStreamObject(); stream.set_data(f'BT /F1 12 Tf 72 720 Td ({text}) Tj ET'.encode())
    page[NameObject('/Contents')]=writer._add_object(stream)
    out=BytesIO(); writer.write(out); return out.getvalue()

def test_real_pdf_source_hash_and_page_locator():
    data=text_pdf(); result=parse_source(data,'manual.pdf')
    assert result['original_sha256']==hashlib.sha256(data).hexdigest()
    assert result['spans'][0]['locator']=='page:1:line:1'
    assert not {'bbox','geometry','rect','quad_points'}&result['spans'][0].keys()
    assert not {'bbox','geometry','rect','quad_points'}&result['chunks'][0].keys()
    assert '75 C' in result['spans'][0]['text']
    assert result['chunks'][0]['sha256']==hashlib.sha256(result['chunks'][0]['text'].encode()).hexdigest()

@pytest.mark.parametrize('filename,data',[('../secret.txt',b'hello'),('secret.zip',b'PK'),('a.pdf',b'not a PDF'),('a.txt',b'\xff'),('a.txt',b'a\x00b'),('a.txt',b''),('a.txt',b'x'*(2*1024*1024+1))],ids=['path','archive','signature','encoding','nul','empty','size'])
def test_reject_unsafe_sources(filename,data):
    with pytest.raises((ValueError,UnicodeError)): parse_source(data,filename)

def test_normalization_keeps_original_hash_and_chunk_offsets():
    data=('Heading\r\nPump-X\tmaximum operating temperature is 85 C\r\n'+'x'*2500).encode()
    r=parse_source(data,'manual.md')
    assert r['original_sha256']==hashlib.sha256(data).hexdigest()
    assert r['spans'][1]['locator']=='line:2'
    assert all(len(c['text'])<=1200 for c in r['chunks'])
    assert [c['offset'] for c in r['chunks'] if c['locator']=='line:3']==[0,1200,2400]

def plan():
    return build_memory_query_plan(project_id='local',subject_id='task',actor_id='human',agent_id='assistant',binding_ids=['claim'],
        memory_classes=['knowledge'],tiers=['canon'],max_items=12,max_bytes=16000,max_tokens=4000,trust_floor=1,
        max_age_seconds=86400,conflict_policy='quarantine',provenance_required=True,writeback_policy='proposal_only',
        source_revision='revision-one',dependency_revisions={'schema':'1'})

def test_px_plan_deterministic_and_stale_revision_rejected():
    assert plan()==plan()
    assert validate_memory_query_plan(plan(),current_source_revision='revision-two')['valid'] is False
    assert validate_memory_query_plan(replace(plan(),max_items=999))['valid'] is False

def test_px_plan_never_allows_direct_writeback():
    assert validate_memory_query_plan(replace(plan(),writeback_policy='direct'))['valid'] is False

def test_remy_manifest_integration_preserves_provenance():
    m=TurnBurnManifest(index_name='local',documents=[TurnBurnManifestDocument(source_id='abc',title='Synthetic',text='Source',metadata={'original_sha256':'a'*64})])
    assert TurnBurnManifest.model_validate_json(m.model_dump_json()).documents[0].metadata['original_sha256']=='a'*64

def test_central_activation_and_insecure_issuer_rejected():
    with pytest.raises(ValueError): CentralConfiguration(enabled=True).staged()
    with pytest.raises(ValueError): CentralConfiguration(issuer='http://remote').staged()
    with pytest.raises(ValueError): CentralConfiguration(issuer='https://user:password@remote').staged()
    assert CentralConfiguration(provider='remy-rie',issuer='https://staged.example').staged()['enabled'] is False

@pytest.fixture
def client(monkeypatch,tmp_path):
    from nsai.api import app,rate_window
    rate_window.clear()
    for role,var in [('operator','NSAI_API_TOKEN_FILE'),('viewer','NSAI_VIEWER_TOKEN_FILE'),('reviewer','NSAI_REVIEWER_TOKEN_FILE'),('admin','NSAI_ADMIN_TOKEN_FILE')]:
        path=tmp_path/(role+'.txt'); path.write_text(role.ljust(48,'x'));monkeypatch.setenv(var,str(path))
    return TestClient(app)

def headers(role): return {'Authorization':'Bearer '+role.ljust(48,'x')}

@pytest.mark.parametrize('role,path,method,body',[
    ('operator','/v1/admin/security','GET',None),('viewer','/v1/documents','POST',{'title':'test','text':'source','version':'1'}),
    ('operator','/v1/review/claim','POST',{'decision':'accept','expected_revision':1,'rationale':'This is a valid rationale'}),
    ('reviewer','/v1/reason','POST',{'question':'Pump-X'})])
def test_role_escalation_denied_before_storage(client,role,path,method,body):
    assert client.request(method,path,headers=headers(role),json=body).status_code==403

def test_unknown_authority_fields_rejected(client):
    response=client.post('/v1/documents',headers=headers('operator'),json={'title':'t','text':'x','verified':True})
    assert response.status_code==422

def test_all_roles_denied_generated_execution(client):
    for role in ('operator','viewer','reviewer','admin'):
        assert client.post('/v1/execute',headers=headers(role)).status_code==403

def test_oversized_body_rejected_without_parser_or_database(client):
    response=client.post('/v1/documents',headers=headers('operator'),content=b'x'*2_200_001)
    assert response.status_code==413 and response.headers['cache-control']=='no-store'
    assert response.headers['x-frame-options']=='DENY'

def test_wrong_token_denied(client):
    assert client.get('/v1/claims',headers={'Authorization':'Bearer wrong'}).status_code==401

def test_rate_limit_is_bounded(client):
    from nsai.api import rate_window
    import time
    rate_window.extend([(time.monotonic(),'local-operator')]*120)
    response=client.get('/v1/capabilities',headers=headers('operator'))
    assert response.status_code==429 and response.headers['x-content-type-options']=='nosniff'
    rate_window.clear()

def test_central_environment_flag_fails_closed(client,monkeypatch):
    monkeypatch.setenv('NSAI_CENTRAL_SECURITY_ENABLED','true')
    assert client.get('/v1/capabilities',headers=headers('admin')).status_code==503
