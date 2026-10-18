"""Local vLLM protocol and source-export boundary; no live provider calls."""
import asyncio
import json

import httpx
import pytest

from nsai import inference


def configure(monkeypatch,url='http://vllm:8000/v1'):
    monkeypatch.setenv('NSAI_MODEL_URL',url)
    monkeypatch.setenv('NSAI_MODEL_NAME','google/gemma-local')
    monkeypatch.setenv('NSAI_MODEL_CONTEXT_TOKENS','4096')
    monkeypatch.delenv('NSAI_MODEL_API_KEY_FILE',raising=False)
    monkeypatch.delenv('NSAI_MODEL_TOKENIZER',raising=False)


def body():
    return dict(model='google/gemma-local',messages=[dict(role='user',content='Synthetic question')],
                max_tokens=128,response_format={'type':'json_schema'})


def transport(monkeypatch,mutate=None):
    requests=[];original=httpx.AsyncClient
    def respond(request):
        assert request.method=='POST' and request.url.path=='/tokenize'
        payload=json.loads(request.content);requests.append(payload)
        assert payload['model']=='google/gemma-local'
        if 'messages' in payload:
            assert payload['add_generation_prompt'] is True
            assert payload['add_special_tokens'] is False
            result=dict(count=100,max_model_len=8192,tokens=list(range(100)))
        else:
            assert payload['add_special_tokens'] is True
            assert json.loads(payload['prompt'])=={'type':'json_schema'}
            result=dict(count=20,max_model_len=8192,tokens=list(range(20)))
        if mutate:mutate(result,len(requests))
        return httpx.Response(200,json=result)
    monkeypatch.setattr(inference.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(respond),**kw))
    return requests


def test_vllm_chat_template_and_schema_overhead_are_counted(monkeypatch):
    configure(monkeypatch);requests=transport(monkeypatch)
    result=asyncio.run(inference.admit_source_request(body()))
    assert result['prompt_tokens']==120 and result['total_tokens']==312
    assert result['context_tokens']==4096 and result['tokenizer_adapter']=='vllm'
    assert result['admitted'] is True and len(requests)==2


def test_vllm_admitted_generation_keeps_source_support_guard(monkeypatch):
    configure(monkeypatch)
    hit=dict(id='a'*32,document_id='b'*32,text='Pump-X operating limit is 85 C.',
             revision='1',locator='line:1',title='Synthetic',original_sha256='c'*64)
    calls=[];original=httpx.AsyncClient
    def respond(request):
        calls.append(request.url.path)
        payload=json.loads(request.content)
        if request.url.path=='/tokenize':
            return httpx.Response(200,json=dict(count=4,max_model_len=4096,tokens=[1,2,3,4]))
        assert request.url.path=='/v1/chat/completions'
        assert payload['model']=='google/gemma-local'
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(
            dict(answer=hit['text'],citation_ids=[hit['id']]))}}]})
    monkeypatch.setattr(inference.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(respond),**kw))
    prepared=inference.prepare_source_request('What is Pump-X operating limit?',[hit],max_tokens=128)
    admission=asyncio.run(inference.admit_source_request(prepared))
    result=asyncio.run(inference.generate_from_sources('What is Pump-X operating limit?',[hit],
                     prepared=prepared,admission=admission))
    assert result['mode']=='model_unverified' and result['answer_verified'] is False
    assert result['citations'][0]['document_id']==hit['document_id']
    assert result['token_admission']==admission
    assert calls==['/tokenize','/tokenize','/v1/chat/completions']


@pytest.mark.parametrize('change',[
    {'model':'wrong-model'},{'max_tokens':True},{'max_tokens':0},{'max_tokens':4097},
])
def test_invalid_admission_request_never_opens_transport(monkeypatch,change):
    configure(monkeypatch);request=body();request.update(change)
    monkeypatch.setattr(inference.httpx,'AsyncClient',lambda **kw:pytest.fail('Invalid admission opened transport'))
    with pytest.raises(ValueError):asyncio.run(inference.admit_source_request(request))


@pytest.mark.parametrize('field,value',[
    ('count',True),('count',99),('count',-1),('tokens',[True]*100),('tokens',[-1]*100),
    ('tokens',None),('max_model_len',True),('max_model_len',100),('max_model_len',1048577),
])
def test_malformed_vllm_response_is_rejected_before_generation(monkeypatch,field,value):
    configure(monkeypatch);requests=transport(monkeypatch,lambda result,index:result.update({field:value}))
    with pytest.raises(ValueError,match='Invalid vLLM tokenizer'):
        asyncio.run(inference.admit_source_request(body()))
    assert len(requests)==1


def test_vllm_context_change_between_counts_fails(monkeypatch):
    configure(monkeypatch)
    transport(monkeypatch,lambda result,index:result.update(max_model_len=4096) if index==2 else None)
    with pytest.raises(ValueError,match='context changed'):
        asyncio.run(inference.admit_source_request(body()))


def test_vllm_uses_actual_server_limit_and_reserves_output(monkeypatch):
    configure(monkeypatch);transport(monkeypatch,lambda result,index:result.update(max_model_len=512))
    request=body();request['max_tokens']=400
    with pytest.raises(ValueError,match='token budget'):
        asyncio.run(inference.admit_source_request(request))


@pytest.mark.parametrize('funding',['free','amd-credits','evolus-credits'])
@pytest.mark.parametrize('operation',['admit','generate'])
def test_funding_label_cannot_authorize_source_export(monkeypatch,funding,operation):
    configure(monkeypatch,'https://remote.example.invalid/v1')
    monkeypatch.setenv('NSAI_MODEL_FUNDING',funding)
    monkeypatch.setattr(inference.httpx,'AsyncClient',lambda **kw:pytest.fail('Private source reached remote transport'))
    with pytest.raises(RuntimeError,match='commissioned export and accounting'):
        asyncio.run(inference.admit_source_request(body()) if operation=='admit' else
                    inference.generate_from_sources('Private question',[],prepared=body(),admission={'admitted':True}))


def test_vllm_cannot_skip_admission_on_named_service_or_loopback(monkeypatch):
    for endpoint in ['http://vllm:8000/v1','http://127.0.0.1:8000/v1']:
        configure(monkeypatch,endpoint);monkeypatch.setenv('NSAI_MODEL_TOKENIZER','vllm')
        monkeypatch.setattr(inference.httpx,'AsyncClient',lambda **kw:pytest.fail('Unadmitted generation opened transport'))
        with pytest.raises(ValueError,match='requires token admission'):
            asyncio.run(inference.generate_from_sources('q',[],prepared=body()))


@pytest.mark.parametrize('change',['endpoint','model','adapter','request','empty'])
def test_admission_binds_provider_endpoint_model_adapter_and_request(monkeypatch,change):
    configure(monkeypatch);transport(monkeypatch)
    request=body();admission=asyncio.run(inference.admit_source_request(request))
    if change=='endpoint':monkeypatch.setenv('NSAI_MODEL_URL','http://vllm:8001/v1')
    elif change=='model':admission['model']='other'
    elif change=='adapter':monkeypatch.setenv('NSAI_MODEL_TOKENIZER','llamacpp')
    elif change=='request':request['messages'][0]['content']='Changed question'
    elif change=='empty':admission={}
    monkeypatch.setattr(inference.httpx,'AsyncClient',lambda **kw:pytest.fail('Stale admission opened generation transport'))
    with pytest.raises(ValueError,match='Stale token admission'):
        asyncio.run(inference.generate_from_sources('q',[],prepared=request,admission=admission))


def test_default_model_is_gemma_and_explicit_local_alias_is_preserved(monkeypatch):
    configure(monkeypatch);monkeypatch.delenv('NSAI_MODEL_NAME')
    assert inference.model_settings()[1]=='google/gemma-3-1b-it'
    monkeypatch.setenv('NSAI_MODEL_NAME','nsai-local-gemma')
    assert inference.model_settings()[1]=='nsai-local-gemma'


@pytest.mark.parametrize('name',['','bad model','bad\nmodel','x'*257])
def test_invalid_model_identity_is_a_configuration_failure(monkeypatch,name):
    configure(monkeypatch);monkeypatch.setenv('NSAI_MODEL_NAME',name)
    with pytest.raises(RuntimeError,match='model identity'):inference.model_settings()
