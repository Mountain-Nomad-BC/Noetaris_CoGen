import asyncio
import httpx
import pytest


def test_retired_candidate_api_has_explicit_compatibility_error(monkeypatch):
    from nsai import inference
    def forbidden(*args,**kwargs):pytest.fail('Retired candidate API opened transport')
    monkeypatch.setattr(inference.httpx,'AsyncClient',forbidden)
    with pytest.raises(RuntimeError,match='source-bound application workflow'):
        asyncio.run(inference.generate_from_candidates('What is the limit?',[]))


def test_model_status_queries_model_inventory(monkeypatch):
    from nsai import inference
    monkeypatch.setenv('NSAI_MODEL_URL','http://llama-cpp:8080/v1')
    monkeypatch.setenv('NSAI_MODEL_NAME','local-qualified-fixture')
    monkeypatch.delenv('NSAI_MODEL_API_KEY_FILE',raising=False)
    original=httpx.AsyncClient
    def respond(request):
        assert request.method=='GET' and str(request.url)=='http://llama-cpp:8080/v1/models'
        assert request.headers['accept-encoding']=='identity'
        return httpx.Response(200,json={'data':[{'id':'local-qualified-fixture'}]})
    monkeypatch.setattr(inference.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(respond),**kw))
    result=asyncio.run(inference.model_status())
    assert result['model_loaded'] and result['reachable']
