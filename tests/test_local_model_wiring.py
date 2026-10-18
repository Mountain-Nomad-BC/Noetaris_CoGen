import pytest
from fastapi.testclient import TestClient
from nsai.api import app
from nsai.inference import model_settings


def test_accepts_configured_ollama(monkeypatch):
    monkeypatch.setenv("NSAI_MODEL_URL","http://ollama:11434/v1")
    monkeypatch.setenv("NSAI_MODEL_NAME","qwen2.5:3b")
    assert model_settings()[:2]==("http://ollama:11434/v1","qwen2.5:3b")


def test_rejects_external_plaintext(monkeypatch):
    monkeypatch.setenv("NSAI_MODEL_URL","http://evil.example.invalid:11434/v1")
    with pytest.raises(RuntimeError): model_settings()


def test_rejects_url_with_credentials(monkeypatch):
    monkeypatch.setenv("NSAI_MODEL_URL","http://token@ollama:11434/v1")
    with pytest.raises(RuntimeError): model_settings()


def test_local_status_not_configured(monkeypatch):
    monkeypatch.delenv("NSAI_MODEL_URL",raising=False)
    from nsai.inference import model_status
    import asyncio
    result=asyncio.run(model_status())
    assert result["reachable"] is False and result["configured"] is False


def test_ui_has_both_local_and_evidence_controls():
    client=TestClient(app)
    assert client.get('/').status_code==200
    assert 'Ask connected AI' in client.get('/').text
    assert 'Review evidence' in client.get('/').text


def test_model_status_is_auth_gated(monkeypatch):
    monkeypatch.delenv('NSAI_API_TOKEN_FILE',raising=False)
    assert TestClient(app).get('/v1/model/status').status_code==503
