import base64
from collections import deque
import hashlib
import json

from fastapi.testclient import TestClient
import pytest
from nsai import api,oauth_accounts as accounts,oauth_http,security


@pytest.fixture
def browser(monkeypatch,tmp_path):
    for setting in [*security.FILES.values(),'NSAI_LOCAL_IDENTITIES_FILE',
                    'NSAI_OAUTH_GOOGLE_ENABLED','NSAI_OAUTH_GITHUB_ENABLED',
                    'NSAI_OAUTH_COOKIE_SECRET_FILE','K_SERVICE']:
        monkeypatch.delenv(setting,raising=False)
    key=tmp_path/'cookie-secret';key.write_text('cookie-signing-'.ljust(48,'x'))
    local=tmp_path/'local-token';local.write_text('local-role-'.ljust(48,'x'))
    monkeypatch.setenv('NSAI_API_TOKEN_FILE',str(local))
    monkeypatch.setenv('NSAI_OAUTH_COOKIE_SECRET_FILE',str(key))
    monkeypatch.setenv('NSAI_PUBLIC_ORIGIN','https://nsai.example')
    monkeypatch.setenv('NSAI_RATE_LIMIT_BACKEND','local')
    monkeypatch.setattr(oauth_http,'_events',deque())
    monkeypatch.setattr(api,'rate_window',deque())
    monkeypatch.setattr(accounts,'browser_epoch',lambda _:1)
    monkeypatch.setattr(accounts,'end_browser',lambda digest,credential=None:0)
    return TestClient(api.app,base_url='https://nsai.example'),key.read_text()


def signed_cookie(key,**fields):
    from itsdangerous import TimestampSigner
    data=base64.b64encode(json.dumps(fields).encode())
    return TimestampSigner(key,salt='nsai.browser-session.v1',digest_method=hashlib.sha256).sign(data).decode()


def test_disabled_oauth_configuration_needs_no_provider_or_database(monkeypatch):
    for setting in ['NSAI_OAUTH_COOKIE_SECRET_FILE','NSAI_OAUTH_GOOGLE_ENABLED','NSAI_OAUTH_GITHUB_ENABLED']:
        monkeypatch.delenv(setting,raising=False)
    response=TestClient(api.app).get('/auth/config')
    assert response.status_code==200
    assert response.json()==dict(providers={'github':False,'google':False},csrf=None)
    assert 'set-cookie' not in response.headers


def test_disabled_oauth_session_is_anonymous_without_cookie_or_database(monkeypatch):
    for setting in ['NSAI_OAUTH_COOKIE_SECRET_FILE','NSAI_OAUTH_GOOGLE_ENABLED','NSAI_OAUTH_GITHUB_ENABLED']:
        monkeypatch.delenv(setting,raising=False)
    monkeypatch.setattr(oauth_http,'_budget',lambda *_:pytest.fail('Disabled browser sessions need no signing secret or database'))
    response=TestClient(api.app).get('/auth/session')
    assert response.status_code==401
    assert response.json()=={'detail':'No browser login session'}
    assert 'set-cookie' not in response.headers


def test_secure_cookie_and_cross_origin_csrf_rejection(browser):
    client,_=browser
    response=client.get('/auth/config')
    cookie=response.headers['set-cookie'].lower()
    assert '__host-nsai-session=' in cookie and 'httponly' in cookie and 'secure' in cookie
    assert 'samesite=lax' in cookie and 'domain=' not in cookie and 'path=/' in cookie
    csrf=response.json()['csrf']
    assert client.post('/auth/logout').status_code==403
    assert client.post('/auth/logout',headers={'Origin':'https://attacker.example','X-CSRF-Token':csrf}).status_code==403
    assert client.post('/auth/logout',headers={'Origin':'https://nsai.example','X-CSRF-Token':csrf}).status_code==200


def test_cookie_authority_claims_ignored_and_private_content_still_withheld(browser,monkeypatch):
    client,key=browser
    actor='local-user-oauth-'+'a'*32
    account=dict(actor=actor,authority='provider',csrf_hash=accounts.token_hash('c'*43))
    monkeypatch.setattr(accounts,'_lookup_hash',lambda digest:account if digest==accounts.token_hash('t'*43) else None)
    client.cookies.set('__Host-nsai-session',signed_cookie(key,token='t'*43,csrf='c'*43,binding='b'*43,role='admin'))
    response=client.get('/v1/capabilities')
    assert response.status_code==200 and response.json()['identity']['role']=='operator'
    assert response.json()['content_access']['admitted'] is False
    assert client.get('/v1/documents').status_code==503
    assert client.post('/v1/chat',json={'question':'hello'}).status_code==403
    assert client.post('/v1/chat',json={'question':'hello'},headers={'Origin':'https://nsai.example','X-CSRF-Token':'c'*43}).status_code==503


def test_revocation_is_rechecked_before_response_release(browser,monkeypatch):
    client,key=browser
    states=[dict(actor='local-user-oauth-'+'a'*32,authority='provider'),None]
    monkeypatch.setattr(accounts,'_lookup_hash',lambda _:states.pop(0))
    client.cookies.set('__Host-nsai-session',signed_cookie(key,token='t'*43,csrf='c'*43,binding='b'*43))
    response=client.get('/v1/capabilities')
    assert response.status_code==401 and 'identity' not in response.json()


def test_invalid_cookie_cannot_authenticate(browser):
    client,_=browser
    client.cookies.set('__Host-nsai-session','forged-admin-cookie')
    assert client.get('/v1/capabilities').status_code==401


def test_oauth_only_deployment_reports_invalid_cookie_as_unauthorized(browser,monkeypatch):
    client,_=browser
    monkeypatch.delenv('NSAI_API_TOKEN_FILE')
    client.cookies.set('__Host-nsai-session','forged-or-expired-cookie')
    assert client.get('/v1/capabilities').status_code==401


def test_logout_revokes_browser_cookie_even_with_separate_bearer_header(browser,monkeypatch):
    client,key=browser
    revoked=[]
    monkeypatch.setattr(accounts,'end_browser',lambda digest,credential=None:revoked.append(credential.token) or 1)
    client.cookies.set('__Host-nsai-session',signed_cookie(key,token='t'*43,csrf='c'*43,binding='b'*43))
    response=client.post('/auth/logout',headers={'Origin':'https://nsai.example','X-CSRF-Token':'c'*43,'Authorization':'Bearer separate-local-role'})
    assert response.status_code==200 and revoked==['t'*43]


def test_failed_logout_keeps_revocation_handle_for_retry(browser,monkeypatch):
    client,key=browser
    def unavailable(*args):raise RuntimeError('Owned storage outage')
    monkeypatch.setattr(accounts,'end_browser',unavailable)
    cookie=signed_cookie(key,token='t'*43,csrf='c'*43,binding='b'*43)
    client.cookies.set('__Host-nsai-session',cookie)
    headers={'Origin':'https://nsai.example','X-CSRF-Token':'c'*43}
    response=client.post('/auth/logout',headers=headers)
    assert response.status_code==503 and client.cookies.get('__Host-nsai-session')==cookie
    monkeypatch.setattr(accounts,'end_browser',lambda *args:1)
    assert client.post('/auth/logout',headers=headers).status_code==200


def test_expected_actor_is_a_restriction_and_never_an_identity_selector(browser,monkeypatch):
    client,key=browser
    actor='local-user-oauth-'+'a'*32
    monkeypatch.setattr(accounts,'_lookup_hash',lambda _:dict(actor=actor,authority='provider'))
    client.cookies.set('__Host-nsai-session',signed_cookie(key,token='t'*43,csrf='c'*43,binding='b'*43))
    assert client.get('/v1/capabilities',headers={'X-NSAI-Expected-Actor':'local-user-bob'}).status_code==401
    response=client.get('/v1/capabilities',headers={'X-NSAI-Expected-Actor':actor})
    assert response.status_code==200 and response.headers['X-NSAI-Actor']==actor


def test_browser_authentication_requests_have_a_separate_bounded_allowance(browser):
    client,_=browser
    for _ in range(20):assert client.get('/auth/config').status_code==200
    response=client.get('/auth/config')
    assert response.status_code==429 and response.headers['retry-after']=='60'


def test_withheld_and_rejected_api_attempts_still_observe_ordinary_user_rate_limit(browser,monkeypatch):
    client,key=browser
    monkeypatch.setenv('NSAI_REQUESTS_PER_MINUTE','1')
    monkeypatch.setattr(accounts,'_lookup_hash',lambda _:dict(actor='local-user-oauth-'+'a'*32,authority='provider'))
    client.cookies.set('__Host-nsai-session',signed_cookie(key,token='t'*43,csrf='c'*43,binding='b'*43))
    assert client.get('/v1/capabilities').status_code==200
    assert client.get('/v1/documents').status_code==429
