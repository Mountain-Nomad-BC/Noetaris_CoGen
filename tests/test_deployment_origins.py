import pytest
from fastapi.testclient import TestClient
from nsai import oauth_providers,oauth_http
from nsai.api import app


@pytest.fixture
def split(monkeypatch):
    monkeypatch.setenv('NSAI_PUBLIC_ORIGIN','https://api.owned.example')
    monkeypatch.setenv('NSAI_FRONTEND_ORIGIN','https://app.owned.example')
    monkeypatch.setenv('NSAI_DEPLOYMENT_SITE','owned.example')
    return 'https://app.owned.example'


def test_api_callback_and_frontend_return_origin_are_independent(split):
    assert oauth_providers.frontend_origin()==split
    config=oauth_providers.ProviderSettings('google','id','x'*40,oauth_providers.public_origin())
    assert config.callback=='https://api.owned.example/auth/google/callback'


@pytest.mark.parametrize('frontend',['https://project.web.app','https://evil.example','https://app.owned.example/path',
    'https://app.owned.example.evil','http://app.owned.example','https://user@app.owned.example'])
def test_crosssite_and_nonorigin_configuration_cannot_activate(split,monkeypatch,frontend):
    monkeypatch.setenv('NSAI_FRONTEND_ORIGIN',frontend)
    with pytest.raises(ValueError):oauth_providers.frontend_origin()


def test_missing_owned_site_cannot_activate_split_origins(split,monkeypatch):
    monkeypatch.delenv('NSAI_DEPLOYMENT_SITE')
    with pytest.raises(ValueError):oauth_http.validate_runtime()


def test_exact_frontend_preflight_has_credentials_and_no_wildcard(split):
    with TestClient(app,base_url='https://api.owned.example') as client:
        response=client.options('/v1/chat',headers={'Origin':split,'Access-Control-Request-Method':'POST',
            'Access-Control-Request-Headers':'Content-Type,X-CSRF-Token,X-NSAI-Expected-Actor'})
    assert response.status_code==200
    assert response.headers['access-control-allow-origin']==split
    assert response.headers['access-control-allow-credentials']=='true'
    assert response.headers['vary']=='Origin'
    assert '*' not in response.headers['access-control-allow-headers']


@pytest.mark.parametrize('origin',['https://evil.example','null','https://app.owned.example.evil'])
def test_other_origins_preflight_is_denied(split,origin):
    with TestClient(app,base_url='https://api.owned.example') as client:
        response=client.options('/v1/chat',headers={'Origin':origin,'Access-Control-Request-Method':'POST'})
    assert response.status_code==400 and 'access-control-allow-origin' not in response.headers


def test_crossorigin_cors_does_not_authenticate_a_request(split,monkeypatch,tmp_path):
    token=tmp_path/'token';token.write_text('x'*64);monkeypatch.setenv('NSAI_API_TOKEN_FILE',str(token))
    with TestClient(app,base_url='https://api.owned.example') as client:
        response=client.get('/v1/integrations/status',headers={'Origin':split})
    assert response.status_code==401
    assert response.headers['access-control-allow-origin']==split


def test_local_bearer_header_is_not_enabled_by_crossorigin_preflight(split):
    with TestClient(app,base_url='https://api.owned.example') as client:
        response=client.options('/v1/chat',headers={'Origin':split,'Access-Control-Request-Method':'POST',
                                                  'Access-Control-Request-Headers':'Authorization'})
    assert response.status_code==400


def test_csrf_accepts_only_exact_frontend_not_callback_api_origin(split,monkeypatch):
    from starlette.requests import Request
    from fastapi import HTTPException
    monkeypatch.setattr(oauth_http,'_browser',lambda request:dict(csrf='c'*43))
    def request(origin):
        return Request(dict(type='http',method='POST',path='/auth/logout',query_string=b'',
            headers=[(b'origin',origin.encode()),(b'x-csrf-token',b'c'*43)]))
    oauth_http._origin_csrf(request(split))
    for origin in ['https://api.owned.example','https://evil.example']:
        with pytest.raises(HTTPException) as error:oauth_http._origin_csrf(request(origin))
        assert error.value.status_code==403


def test_browser_cookie_stays_host_only_secure_httponly_lax(split,monkeypatch,tmp_path):
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.applications import Starlette
    from starlette.routing import Route
    key=tmp_path/'cookie';key.write_text('x'*64)
    monkeypatch.setenv('NSAI_OAUTH_COOKIE_SECRET_FILE',str(key))
    async def endpoint(request):
        request.session['synthetic']='fixture-only'
        return JSONResponse({'ok':True})
    with TestClient(oauth_http.BrowserSessions(Starlette(routes=[Route('/',endpoint)])),base_url='https://api.owned.example') as client:
        response=client.get('/')
    cookie=response.headers['set-cookie'].lower()
    assert '__host-nsai-session=' in cookie and 'httponly' in cookie and 'secure' in cookie
    assert 'samesite=lax' in cookie and 'domain=' not in cookie and 'path=/' in cookie
