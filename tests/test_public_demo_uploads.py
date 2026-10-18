from collections import deque
import pytest
from fastapi.testclient import TestClient
from nsai import api


@pytest.fixture
def public_demo(monkeypatch, tmp_path):
    for key in ['NSAI_LOCAL_IDENTITIES_FILE', 'NSAI_OAUTH_COOKIE_SECRET_FILE', 'NSAI_OAUTH_GOOGLE_ENABLED', 'NSAI_OAUTH_GITHUB_ENABLED']:
        monkeypatch.delenv(key, raising=False)
    secret = tmp_path / 'api-credential'
    secret.write_text('owned-demo-test-credential-'.ljust(48, 'x'))
    monkeypatch.setenv('NSAI_API_TOKEN_FILE', str(secret))
    monkeypatch.setenv('NSAI_PUBLIC_DEMO', 'true')
    monkeypatch.setattr(api, 'rate_window', deque())
    monkeypatch.setattr(api.store, 'store_document', lambda *a: pytest.fail('Unacknowledged content reached storage'))
    return TestClient(api.app), {'Authorization': 'Bearer ' + secret.read_text()}


@pytest.mark.parametrize('ack', [None, '', 'true', 'old-version'])
def test_public_json_upload_requires_current_restrictions_before_storage(public_demo, ack):
    client, headers = public_demo
    body = {'title': 'Public synthetic fixture', 'text': 'Synthetic text'}
    if ack is not None:
        body['upload_ack'] = ack
    response = client.post('/v1/documents', json=body, headers=headers)
    assert response.status_code == 428


def test_public_multipart_upload_requires_ack_before_parser(public_demo):
    client, headers = public_demo
    response = client.post('/v1/files', files={'file': ('source.txt', b'Public synthetic fixture')}, headers=headers)
    assert response.status_code == 428


def test_current_ack_is_not_a_source_or_identity_authorization(public_demo):
    client, _ = public_demo
    response = client.post('/v1/documents', json={'title': 'Source', 'text': 'Text', 'upload_ack': 'public-demo-2026-10-17'})
    assert response.status_code == 401


def test_current_ack_reaches_existing_ingestion_boundary(public_demo, monkeypatch):
    client, headers = public_demo
    monkeypatch.setattr(api.store, 'store_document', lambda title, text, version, actor: {'actor': actor, 'accepted': True})
    response = client.post('/v1/documents', json={'title': 'Source', 'text': 'Public synthetic text', 'upload_ack': 'public-demo-2026-10-17'}, headers=headers)
    assert response.status_code == 200
    assert response.json() == {'actor': 'local-operator', 'accepted': True}
