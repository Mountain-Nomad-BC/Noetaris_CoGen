import asyncio
import httpx
import pytest
from nsai.integrations import evolus


def setup_client(tmp_path,monkeypatch,respond):
    key=tmp_path/'evolus';key.write_text('synthetic-'+('x'*40))
    original=httpx.AsyncClient
    def client(**kwargs):
        assert kwargs['trust_env'] is False and kwargs['follow_redirects'] is False
        return original(transport=httpx.MockTransport(respond),**kwargs)
    monkeypatch.setattr(evolus.httpx,'AsyncClient',client)
    return evolus.EvolusClient(key_file=str(key),application_id='owned-fixture',workflow_id='review-spec',api_base='https://evolus.example.invalid/api/v1')


def test_exact_workflow_application_binding_and_bounded_response(tmp_path,monkeypatch):
    def respond(request):
        assert request.url=='https://evolus.example.invalid/api/v1/workflows/review-spec/execute'
        assert request.headers['X-Application-Id']=='owned-fixture'
        assert request.headers['X-ApiKey']=='synthetic-'+('x'*40)
        assert request.content==b'{"text":"Synthetic source"}'
        return httpx.Response(200,json={'execution_id':'fixture-only'})
    client=setup_client(tmp_path,monkeypatch,respond)
    assert asyncio.run(client.execute_workflow('review-spec',{'text':'Synthetic source'}))=={'execution_id':'fixture-only'}


@pytest.mark.parametrize('payload',[[],{'text':'x'*262145},{'number':float('nan')},{'nest':[[[[[[[[[[[[[[[[[[1]]]]]]]]]]]]]]]]]]}])
def test_invalid_payload_never_contacts_partner(tmp_path,monkeypatch,payload):
    client=setup_client(tmp_path,monkeypatch,lambda _:pytest.fail('Invalid payload reached Evolus'))
    with pytest.raises(ValueError):asyncio.run(client.execute_workflow('review-spec',payload))


@pytest.mark.parametrize('response',[
    httpx.Response(302,headers={'location':'https://untrusted.example/'}),
    httpx.Response(200,content=b'x',headers={'content-length':'1048577'}),
    httpx.Response(200,json=['unexpected']),
])
def test_redirect_oversize_and_nonobject_responses_rejected(tmp_path,monkeypatch,response):
    client=setup_client(tmp_path,monkeypatch,lambda _:response)
    with pytest.raises((httpx.HTTPStatusError,ValueError,RuntimeError)):
        asyncio.run(client.execute_workflow('review-spec',{}))


def test_unconfigured_workflow_cannot_reuse_partner_credentials(tmp_path,monkeypatch):
    client=setup_client(tmp_path,monkeypatch,lambda _:pytest.fail('Unconfigured workflow contacted partner'))
    with pytest.raises(ValueError):asyncio.run(client.execute_workflow('other-workflow',{}))
