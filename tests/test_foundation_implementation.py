import asyncio
import json
import httpx
import pytest
from fastapi import HTTPException
from nsai import inference
from nsai.models import conflict_groups,extract_claims,observe_statements
from nsai.memory import materialize_projection
from nsai.security import principal

def claim(value,identifier='a'):
    return dict(id=identifier,subject='pump-x',predicate='operating limit',value=value,document_id='source',locator='line:1',status='candidate')

@pytest.mark.parametrize('first,second',[('85C','185F'),('85C','85.0C'),('-40C','-40F'),('0C','32F')])
def test_exact_unit_equivalence(first,second):
    assert not conflict_groups([claim(first),claim(second,'b')])

def test_distinct_values_still_conflict():
    assert conflict_groups([claim('85C'),claim('85.01C','b')])

@pytest.mark.parametrize('value',['Bearer nonascii£','Bearer '+('x'*1025),'Bearer bad token','Basic token','Bearer '])
def test_bad_bearer_is_unauthorized(monkeypatch,value):
    monkeypatch.setenv('NSAI_API_TOKEN_FILE','not-read-for-malformed')
    with pytest.raises(HTTPException) as error:principal(value)
    assert error.value.status_code==401

def test_nonascii_api_has_security_headers(monkeypatch,tmp_path):
    from fastapi.testclient import TestClient
    from nsai.api import app,rate_window
    rate_window.clear()
    p=tmp_path/'token';p.write_text('x'*48);monkeypatch.setenv('NSAI_API_TOKEN_FILE',str(p))
    r=TestClient(app).get('/v1/capabilities',headers=[(b'authorization',b'Bearer \xff')])
    assert r.status_code==401 and r.headers['cache-control']=='no-store'

def test_observations_do_not_upgrade_negation_or_conditions():
    text='Pump-X operating limit is not 85 C\nIf hot, Pump-X operating limit is 85 C\nPump-X operating limit was 75 C\nWhat is the limit?'
    assert not extract_claims(text)
    assert [x['epistemic_state'] for x in observe_statements(text)]==['negated','conditional','historical','question']

def test_leading_condition_cannot_become_subject():
    assert not extract_claims('If Pump-X maximum operating temperature is 85 C')

def test_boolean_page_is_not_admitted():
    from nsai.api import Question
    with pytest.raises(ValueError):Question(question='x',pages=[True])

def test_invalid_utf8_auth_config_fails_closed(monkeypatch,tmp_path):
    p=tmp_path/'bad';p.write_bytes(b'\xff');monkeypatch.setenv('NSAI_API_TOKEN_FILE',str(p))
    with pytest.raises(HTTPException) as error:principal('Bearer validascii')
    assert error.value.status_code==503

def test_full_projection_envelope_budget():
    result=materialize_projection([dict(role='user',text='😀'*1000)],[],[],[],max_bytes=1024)
    assert len(json.dumps(result,sort_keys=True,ensure_ascii=False,allow_nan=False).encode())<=1024
    assert result['omitted']['working']==1

def test_initial_slices_are_counted_as_omissions():
    result=materialize_projection([dict(role='user',text='a') for _ in range(12)],[],[],[])
    assert result['omitted']['working']==4

def test_cited_numeric_fabrication_withheld():
    hits=[dict(text='Pump-X operating limit is 85 C')]
    assert not inference.factual_support('Pump-X operating limit is 75 C',hits)
    assert inference.factual_support('Pump-X operating limit is 185 F',hits)
    assert not inference.factual_support('Pump-Y operating limit is 85 C',hits)

def test_missing_model_secret_is_typed(monkeypatch,tmp_path):
    monkeypatch.setenv('NSAI_MODEL_URL','http://llama-cpp:8080/v1')
    monkeypatch.setenv('NSAI_MODEL_API_KEY_FILE',str(tmp_path/'missing'))
    assert asyncio.run(inference.model_status())['configured'] is False

def test_malformed_inventory_list(monkeypatch):
    monkeypatch.setenv('NSAI_MODEL_URL','http://llama-cpp:8080/v1')
    monkeypatch.delenv('NSAI_MODEL_API_KEY_FILE',raising=False)
    original=httpx.AsyncClient
    monkeypatch.setattr(inference.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(lambda r:httpx.Response(200,json=[])),**kw))
    assert asyncio.run(inference.model_status())['reachable'] is False

@pytest.mark.parametrize('tokens,expected',[(100,True),(4632,False)])
def test_actual_token_admission_before_generation(monkeypatch,tokens,expected):
    monkeypatch.setenv('NSAI_MODEL_URL','http://llama-cpp:8080/v1');monkeypatch.delenv('NSAI_MODEL_API_KEY_FILE',raising=False)
    original=httpx.AsyncClient
    def respond(request):
        if request.url.path=='/props':return httpx.Response(200,json={'default_generation_settings':{'n_ctx':4096}})
        if request.url.path=='/apply-template':return httpx.Response(200,json={'prompt':'templated system + question + history + evidence'})
        if request.url.path=='/tokenize':return httpx.Response(200,json={'tokens':list(range(tokens))})
        raise AssertionError('Admission must not generate or reserve')
    monkeypatch.setattr(inference.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(respond),**kw))
    body=dict(messages=[dict(role='user',content='question')],max_tokens=256)
    if expected:assert asyncio.run(inference.admit_source_request(body))['total_tokens']==tokens+320
    else:
        with pytest.raises(ValueError):asyncio.run(inference.admit_source_request(body))


@pytest.mark.parametrize('failure_path,response,match',[
    ('/props',{'default_generation_settings':True},'Invalid model properties'),
    ('/props',{'default_generation_settings':[]},'Invalid model properties'),
    ('/apply-template',[],'Invalid model prompt template'),
    ('/tokenize',{'tokens':[True]},'Invalid tokenizer response'),
],ids=['scalar-properties','array-properties','array-template','boolean-token-id'])
def test_malformed_tokenizer_admission_responses_are_typed_and_never_generate(monkeypatch,failure_path,response,match):
    monkeypatch.setenv('NSAI_MODEL_URL','http://llama-cpp:8080/v1')
    monkeypatch.delenv('NSAI_MODEL_API_KEY_FILE',raising=False)
    calls=[]
    original=httpx.AsyncClient
    def respond(request):
        calls.append(request.url.path)
        if request.url.path=='/props':
            body=response if failure_path=='/props' else {'default_generation_settings':{'n_ctx':4096}}
        elif request.url.path=='/apply-template':
            body=response if failure_path=='/apply-template' else {'prompt':'templated prompt'}
        elif request.url.path=='/tokenize':
            body=response if failure_path=='/tokenize' else {'tokens':[1]}
        else:raise AssertionError('Token admission must not generate')
        return httpx.Response(200,json=body)
    monkeypatch.setattr(inference.httpx,'AsyncClient',lambda **kwargs:original(
        transport=httpx.MockTransport(respond),**kwargs))
    with pytest.raises(ValueError,match=match):
        asyncio.run(inference.admit_source_request(dict(messages=[dict(role='user',content='q')],max_tokens=64)))
    assert '/chat/completions' not in calls


def test_ranked_out_conflict_still_found(monkeypatch):
    from nsai import api
    monkeypatch.setattr(api,'library_retrieve',lambda *a,**kw:[dict(id='a',document_id='source',locator='line:1',text='85C',title='manual',revision='1',original_sha256='b'*64)])
    claims=[claim('85C'),dict(claim('75C','b'),document_id='other',locator='line:99')]
    monkeypatch.setattr(api.workflows,'claim_context',lambda *a,**kw:[r for r in claims if not kw['document_ids'] or r['document_id'] in kw['document_ids']])
    monkeypatch.setattr(api.workflows,'source',lambda *a:dict(revision='1'))
    assert api.evidence('pump')[2]
    assert not api.evidence('pump',document_ids=['source'])[2]

def test_capability_projection_contract_consumable_by_browser():
    from nsai.capabilities import registry
    for item in registry():
        assert isinstance(item['evidence'],list)
        assert isinstance(item['routes'],list) and isinstance(item['permissions'],list)
        assert item['authority_granted'] is False

def test_verification_asset_requires_authenticated_evidence_route():
    from fastapi.testclient import TestClient
    from nsai.api import app
    client=TestClient(app)
    for path in ('/assets/verification.json','/assets/%2e/verification.json',
        '/assets/x/%2e%2e/verification.json','/assets//verification.json',
        '/assets/VERIFICATION.JSON','/assets/verification.json::$DATA'):
        for method in ('get','head'):
            response=getattr(client,method)(path)
            assert response.status_code==404
            assert response.headers['cache-control']=='no-store'
    assert client.get('/assets/app.js').status_code==200
    quote=client.get('/assets/pdf-quotes.mjs')
    assert quote.status_code==200 and 'javascript' in quote.headers['content-type']
    canvas=client.get('/assets/pdf-canvas.mjs')
    assert canvas.status_code==200 and 'javascript' in canvas.headers['content-type']
    for name in ('pdf.mjs','pdf.worker.mjs'):
        assert client.get('/assets/pdfjs/'+name).status_code==200
