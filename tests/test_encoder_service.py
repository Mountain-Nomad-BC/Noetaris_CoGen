import pytest
from fastapi.testclient import TestClient
from nsai import encoder_service as encoder


@pytest.fixture
def client(tmp_path,monkeypatch):
    token=tmp_path/'encoder-token';token.write_text('owned-encoder-credential-'.ljust(48,'x'))
    monkeypatch.setenv('NSAI_ENCODER_TOKEN_FILE',str(token))
    async def must_not_start():pytest.fail('Invalid request started encoder child')
    monkeypatch.setattr(encoder,'_ready',must_not_start)
    with TestClient(encoder.app) as client:yield client,{'Authorization':'Bearer '+token.read_text()}


def test_service_authentication_precedes_body_parsing_and_child_creation(client):
    client,headers=client
    assert client.post('/encode',content=b'not json').status_code==401
    assert client.get('/identity').status_code==401
    assert client.get('/healthz').status_code==200
    assert client.get('/unexpected').status_code==404


@pytest.mark.parametrize('body',[b'{"texts":["a"],"texts":["b"]}',b'{"texts":[NaN]}',b'\xff'])
def test_invalid_or_ambiguous_service_json_is_rejected(client,body):
    client,headers=client
    assert client.post('/encode',headers={**headers,'Content-Type':'application/json'},content=body).status_code==422


def test_encoder_body_byte_limit_is_enforced_before_json_loading(client):
    client,headers=client
    assert client.post('/encode',headers=headers,content=b'x'*(1200*1024+1)).status_code==413


@pytest.mark.parametrize('texts',[[],['x']*9,[' '],['é'*70000]])
def test_batch_inventory_and_unicode_bytes_are_bounded(texts):
    with pytest.raises(ValueError):encoder.EncoderBatch(texts=texts)
