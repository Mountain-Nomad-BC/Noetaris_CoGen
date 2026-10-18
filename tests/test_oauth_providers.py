import asyncio
import base64
import hashlib
import time
from urllib.parse import parse_qs, urlencode, urlsplit

import httpx
import pytest
from starlette.requests import Request

from nsai.oauth_providers import ProviderSettings, client, public_origin, settings, verified_subject


class AtomicCache:
    """Test-only state cache; production must use a PostgreSQL atomic consumer."""
    def __init__(self):
        self.data = {}

    async def set(self, key, value, expires_in):
        self.data[key] = value

    async def get(self, key):
        return self.data.pop(key, None)

    async def delete(self, key):
        self.data.pop(key, None)


def request(session, query=''):
    return Request(dict(type='http', method='GET', scheme='https', server=('nsai.example', 443),
                        path='/auth/callback', query_string=query.encode(), headers=[], session=session))


def configuration(name):
    return ProviderSettings(name, 'client-test', 's' * 40, 'https://nsai.example')


@pytest.mark.parametrize('origin', [
    '', 'http://nsai.example', 'https://nsai.example/', 'https://user@nsai.example',
    'https://nsai.example?x=1', 'https://nsai.example#x', 'https://nsai.example:0',
    'https://nsai.example:', 'https://nsai.example\\evil', 'https://nsai.example\n',
    'https://nsai..example', 'https://-nsai.example', 'https://nsai.example%2f.evil',
])
def test_untrusted_origin_rejected(monkeypatch, origin):
    monkeypatch.setenv('NSAI_PUBLIC_ORIGIN', origin)
    with pytest.raises(ValueError):
        public_origin()


def test_disabled_provider_needs_no_secret_or_transport(monkeypatch):
    monkeypatch.delenv('NSAI_OAUTH_GOOGLE_ENABLED', raising=False)
    assert settings('google') is None
    with pytest.raises(ValueError, match='Unsupported'):
        settings('attacker')


def test_default_https_port_and_host_case_are_canonical_for_browser_origin(monkeypatch):
    monkeypatch.setenv('NSAI_PUBLIC_ORIGIN','https://NSAI.EXAMPLE:443')
    assert public_origin()=='https://nsai.example'


def test_explicit_https_test_port_is_bound_into_callback_origin(monkeypatch):
    monkeypatch.setenv('NSAI_PUBLIC_ORIGIN','https://localhost:18443')
    assert public_origin()=='https://localhost:18443'


def test_enabled_configuration_hides_secret_and_pins_callback(monkeypatch, tmp_path):
    secret = tmp_path / 'provider-secret'
    secret.write_text('private-' + 's' * 40)
    monkeypatch.setenv('NSAI_PUBLIC_ORIGIN', 'https://nsai.example')
    monkeypatch.setenv('NSAI_OAUTH_GOOGLE_ENABLED', 'true')
    monkeypatch.setenv('NSAI_OAUTH_GOOGLE_CLIENT_ID', 'client-test')
    monkeypatch.setenv('NSAI_OAUTH_GOOGLE_CLIENT_SECRET_FILE', str(secret))
    result = settings('google')
    assert result.callback == 'https://nsai.example/auth/google/callback'
    assert result.client_secret not in repr(result)


@pytest.mark.parametrize('provider', ['google', 'github'])
def test_real_authlib_generates_s256_and_keeps_verifier_server_side(provider):
    async def run():
        cache = AtomicCache()
        session = {}
        config = configuration(provider)
        remote = client(config, cache=cache)
        response = await remote.authorize_redirect(request(session), config.callback)
        params = parse_qs(urlsplit(response.headers['location']).query)
        assert params['code_challenge_method'] == ['S256']
        assert params['redirect_uri'] == [config.callback]
        assert 'code_verifier' not in params
        assert 'client_secret' not in params
        import json
        stored = json.loads(next(iter(cache.data.values())))['data']
        expected = base64.urlsafe_b64encode(hashlib.sha256(stored['code_verifier'].encode()).digest()).rstrip(b'=').decode()
        assert params['code_challenge'] == [expected]
        assert stored['code_verifier'] not in str(session)
        if provider == 'google':
            assert params['nonce'] == [stored['nonce']]
        with pytest.raises(Exception):
            await verified_subject(remote, request({}, urlencode({'code': 'test', 'state': params['state'][0]})))
    asyncio.run(run())


def test_github_code_exchange_verifies_numeric_subject_and_rejects_replay():
    async def run():
        cache = AtomicCache()
        session = {}
        config = configuration('github')
        remote = client(config, cache=cache)
        calls = []

        def transport(req):
            calls.append(req)
            if req.url.host == 'github.com':
                body = parse_qs(req.content.decode())
                assert body['code_verifier'] and body['redirect_uri'] == [config.callback]
                assert body['client_secret'] == [config.client_secret]
                return httpx.Response(200, json={'access_token': 'provider-test', 'token_type': 'bearer'})
            assert req.headers['authorization'] == 'Bearer provider-test'
            if req.url.path == '/user':
                return httpx.Response(200, json={'id': 12345, 'login': 'mutable-name', 'type': 'User'})
            pytest.fail('Sign-in must not request private email metadata')

        remote.client_kwargs['transport'] = httpx.MockTransport(transport)
        response = await remote.authorize_redirect(request(session), config.callback)
        state = parse_qs(urlsplit(response.headers['location']).query)['state'][0]
        query = urlencode({'code': 'code-test', 'state': state})
        assert await verified_subject(remote, request(session, query)) == '12345'
        assert len(calls) == 2
        with pytest.raises(Exception):
            await verified_subject(remote, request(session, query))
        assert len(calls) == 2
    asyncio.run(run())


@pytest.mark.parametrize('mutation', ['valid', 'nonce', 'audience', 'issuer', 'expired', 'unverified', 'unsigned', 'signature'])
def test_google_signed_identity_validation(mutation):
    async def run():
        from joserfc import jwt
        from joserfc.jwk import RSAKey
        key = RSAKey.generate_key(2048)
        key.ensure_kid()
        cache = AtomicCache()
        session = {}
        config = configuration('google')
        remote = client(config, cache=cache)
        response = await remote.authorize_redirect(request(session), config.callback)
        params = parse_qs(urlsplit(response.headers['location']).query)
        now = int(time.time())
        claims = dict(iss='https://accounts.google.com', sub='stable-google-id', aud=config.client_id,
                      iat=now, exp=now+300, nonce=params['nonce'][0], email_verified=True)
        if mutation == 'nonce': claims['nonce'] = 'wrong'
        if mutation == 'audience': claims['aud'] = 'other-client'
        if mutation == 'issuer': claims['iss'] = 'https://attacker.example'
        if mutation == 'expired': claims['exp'] = now-3600
        if mutation == 'unverified': claims['email_verified'] = False
        encoded = jwt.encode({'alg': 'RS256', 'kid': key.kid}, claims, key)
        if mutation == 'signature':
            encoded = jwt.encode({'alg': 'RS256', 'kid': key.kid}, claims, RSAKey.generate_key(2048))

        def transport(req):
            if req.url.host == 'www.googleapis.com':
                return httpx.Response(200, json={'keys': [key.as_dict(private=False)]})
            assert req.url.host == 'oauth2.googleapis.com'
            token = dict(access_token='provider-test', token_type='bearer', id_token=encoded)
            if mutation == 'unsigned':
                token.pop('id_token')
                token['userinfo'] = claims
            return httpx.Response(200, json=token)

        remote.client_kwargs['transport'] = httpx.MockTransport(transport)
        callback = request(session, urlencode({'code': 'code-test', 'state': params['state'][0]}))
        if mutation in {'valid', 'unverified'}:
            assert await verified_subject(remote, callback) == 'stable-google-id'
        else:
            with pytest.raises(Exception):
                await verified_subject(remote, callback)
    asyncio.run(run())


def test_github_stable_identity_does_not_require_email():
    from nsai.oauth_providers import _github_subject
    assert _github_subject({'type': 'User', 'id': 9007199254740993, 'email': None}) == '9007199254740993'
    with pytest.raises(ValueError):
        _github_subject({'type': 'User', 'id': True})


def test_google_verified_subject_does_not_require_profile_claims():
    from nsai.oauth_providers import _google_subject
    assert _google_subject({'iss': 'https://accounts.google.com', 'sub': 'stable-subject'}) == 'stable-subject'
