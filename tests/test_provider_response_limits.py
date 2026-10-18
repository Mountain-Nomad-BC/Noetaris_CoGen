import asyncio
import gzip

import httpx
import pytest

from nsai import inference


class ObservedStream(httpx.AsyncByteStream):
    def __init__(self, blocks):
        self.blocks=blocks
        self.read=False
        self.closed=False

    async def __aiter__(self):
        self.read=True
        for block in self.blocks:
            yield block

    async def aclose(self):
        self.closed=True


def request(stream, *, headers=None, maximum=128):
    async def run():
        seen={}
        def respond(req):
            seen.update(req.headers)
            return httpx.Response(200,headers=headers or {},stream=stream)
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            value=await inference._bounded_json(client,'GET','http://localhost/test',headers={},maximum=maximum)
        return value,seen
    return asyncio.run(run())


@pytest.mark.parametrize('encoding',['gzip','br','deflate','gzip, identity','unknown'])
def test_encoded_response_rejected_before_body_consumption(encoding):
    stream=ObservedStream([gzip.compress(b'"'+b'x'*1_000_000+b'"')])
    with pytest.raises(ValueError,match='encoding'):
        request(stream,headers={'Content-Encoding':encoding})
    assert stream.read is False and stream.closed is True


@pytest.mark.parametrize('length',['129','-1','many','1, 2','9'*100])
def test_oversized_or_invalid_declared_length_rejected_before_read(length):
    stream=ObservedStream([b'{}'])
    with pytest.raises(ValueError,match='length'):
        request(stream,headers={'Content-Length':length})
    assert stream.read is False and stream.closed is True


def test_identity_json_stream_is_bounded_and_negotiated():
    stream=ObservedStream([b'{"value":',b'42}'])
    value,headers=request(stream,headers={'Content-Encoding':'identity'})
    assert value=={'value':42}
    assert headers['accept-encoding']=='identity'
    assert stream.closed is True


@pytest.mark.parametrize('body',[b'[]',b'null',b'{"data":"not-a-list"}',b'{'],
                         ids=['array-envelope','null-envelope','wrong-model-list-shape','malformed-json'])
def test_model_status_contains_invalid_provider_envelopes(monkeypatch,body):
    monkeypatch.setenv('NSAI_MODEL_URL','http://localhost:8080/v1')
    original=httpx.AsyncClient
    monkeypatch.setattr(inference.httpx,'AsyncClient',lambda **kwargs:original(
        transport=httpx.MockTransport(lambda request:httpx.Response(200,content=body)),**kwargs))
    result=asyncio.run(inference.model_status())
    assert result['configured'] is True
    assert result['reachable'] is False
    assert result['model_loaded'] is False
    assert result['reason']=='Model API unavailable or invalid response'


def test_model_status_missing_credential_is_a_bounded_configuration_failure(monkeypatch,tmp_path):
    monkeypatch.setenv('NSAI_MODEL_URL','http://localhost:8080/v1')
    monkeypatch.setenv('NSAI_MODEL_API_KEY_FILE',str(tmp_path/'missing-key'))
    result=asyncio.run(inference.model_status())
    assert result==dict(configured=False,reachable=False,model_loaded=False,model=None,
                        provider='none',reason='Model credential unavailable or invalid')


@pytest.mark.parametrize('body',[b'[]',b'null',b'{"choices":[]}',b'{"choices":[null]}',
                                b'{"choices":[{"message":null}]}'],
                         ids=['array-completion','null-completion','empty-choices','null-choice','null-message'])
def test_invalid_completion_envelopes_become_generic_service_unavailable(monkeypatch,body):
    from fastapi import HTTPException
    from nsai.api import translate_error

    monkeypatch.setenv('NSAI_MODEL_URL','http://localhost:8080/v1')
    original=httpx.AsyncClient
    monkeypatch.setattr(inference.httpx,'AsyncClient',lambda **kwargs:original(
        transport=httpx.MockTransport(lambda request:httpx.Response(200,content=body)),**kwargs))
    with pytest.raises(RuntimeError,match='Invalid model completion envelope') as failure:
        asyncio.run(inference.generate_from_sources('question',[]))
    with pytest.raises(HTTPException) as response:
        translate_error(failure.value)
    assert response.value.status_code==503
    assert response.value.detail=='Service unavailable'
    assert body.decode(errors='replace') not in response.value.detail


def test_chunked_stream_exceeding_budget_is_closed():
    stream=ObservedStream([b'"',b'x'*128,b'"'])
    with pytest.raises(ValueError,match='budget'):request(stream)
    assert stream.closed is True


def test_retired_candidate_generation_never_opens_provider(monkeypatch):
    monkeypatch.setattr(inference,'model_settings',lambda:pytest.fail('Retired path read provider credentials'))
    with pytest.raises(RuntimeError,match='retired'):
        asyncio.run(inference.generate_from_candidates('question',[]))


def test_invalid_model_port_is_a_typed_configuration_error(monkeypatch):
    monkeypatch.setenv('NSAI_MODEL_URL','http://localhost:not-a-port/v1')
    with pytest.raises(RuntimeError,match='URL'):inference.model_settings()


def test_model_credential_uses_bounded_reader(monkeypatch,tmp_path):
    monkeypatch.setenv('NSAI_MODEL_URL','http://localhost:8080/v1')
    key=tmp_path/'key';key.write_bytes(b'x'*2048)
    monkeypatch.setenv('NSAI_MODEL_API_KEY_FILE',str(key))
    monkeypatch.setattr(type(key),'read_text',lambda *a,**kw:pytest.fail('Oversized credential was read'))
    with pytest.raises(RuntimeError,match='credential'):inference.model_settings()


def test_slow_response_deadline_closes_active_stream():
    class Slow(ObservedStream):
        async def __aiter__(self):
            self.read=True
            await asyncio.sleep(5)
            yield b'{}'
    stream=Slow([])
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,stream=stream))) as client:
            with pytest.raises(TimeoutError):
                await inference._bounded_json(client,'GET','http://localhost/test',headers={},deadline=.02)
    asyncio.run(run())
    assert stream.read and stream.closed


def test_cancelling_active_response_closes_provider_stream():
    async def run():
        started=asyncio.Event()
        class Waiting(ObservedStream):
            async def __aiter__(self):
                started.set()
                await asyncio.Future()
                yield b'{}'
        stream=Waiting([])
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,stream=stream))) as client:
            task=asyncio.create_task(inference._bounded_json(client,'GET','http://localhost/test',headers={}))
            await asyncio.wait_for(started.wait(),timeout=1)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):await task
        assert stream.closed
    asyncio.run(run())
