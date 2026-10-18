import asyncio
import pytest
from nsai import store
from nsai.oauth_state import PostgresStateCache


@pytest.mark.parametrize('binding', ['', None, 'a'*63, 'g'*64, 'A'*64])
def test_browser_binding_validation(binding):
    with pytest.raises(ValueError):
        PostgresStateCache(binding)


def test_auth_state_cannot_upgrade_an_existing_request_principal(monkeypatch):
    monkeypatch.setattr(store, 'connect', lambda: pytest.fail('Principal reached auth service database'))
    cache = PostgresStateCache('b'*64)
    with store.identity_context(dict(actor='local-user-alice', role='operator')):
        with pytest.raises(PermissionError):
            asyncio.run(cache.get('_state_google_' + 'a'*32))


def test_unbounded_or_invalid_state_rejected_before_database(monkeypatch):
    monkeypatch.setattr(store, 'connect', lambda: pytest.fail('Invalid state reached database'))
    cache = PostgresStateCache('b'*64)
    with pytest.raises(ValueError):
        asyncio.run(cache.get('_state_attacker_' + 'a'*32))
    with pytest.raises(ValueError):
        asyncio.run(cache.set('_state_google_' + 'a'*32, 'x', expires_in=3600))
    with pytest.raises(ValueError):
        asyncio.run(cache.set('_state_google_' + 'a'*32, 'x'*8193, expires_in=300))
