"""Every registered private API method must deny before database or model work."""
import re
import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from nsai import api,store

PRIVATE_METHODS = [(route.path,method) for route in api.app.routes
                   if isinstance(route,APIRoute) and route.path.startswith('/v1/')
                   for method in sorted(route.methods)]


@pytest.mark.parametrize('path,method',PRIVATE_METHODS)
def test_every_private_method_denies_anonymous_before_backend_work(tmp_path,monkeypatch,path,method):
    token=tmp_path/'synthetic-role-token'
    token.write_text('original-test-token-not-a-real-credential',encoding='ascii')
    monkeypatch.setenv('NSAI_API_TOKEN_FILE',str(token))
    monkeypatch.setenv('NSAI_CENTRAL_SECURITY_ENABLED','false')
    calls=[]
    def forbidden(*args,**kwargs):
        calls.append(True)
        raise AssertionError('Anonymous request reached database')
    monkeypatch.setattr(store,'connect',forbidden)
    target=re.sub(r'\{[^{}]+\}','a'*32,path)
    with TestClient(api.app) as client:
        response=client.request(method,target,json={} if method in ('POST','PUT','PATCH') else None)
    assert response.status_code==401
    assert response.headers['cache-control']=='no-store'
    assert response.headers['www-authenticate']=='Bearer'
    assert calls==[]
