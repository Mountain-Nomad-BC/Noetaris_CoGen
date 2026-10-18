import asyncio
import pytest
from starlette.responses import StreamingResponse
from nsai import api,store
from fastapi import HTTPException

IDENTITY=dict(actor='local-user-alice',role='operator',identity_kind='local-user',
              permissions=['chat','ingest','propose','read'])


def run(monkeypatch,*,fresh=None,denied=False,body=b'PRIVATE_CANARY'):
    events=[]
    async def stream():
        events.append('serialize')
        yield body
    def resolve(token):
        assert token=='Bearer synthetic-token'
        events.append('fresh-authentication')
        if isinstance(fresh,Exception):raise fresh
        return IDENTITY if fresh is None else fresh
    def authorize(sources):
        events.append(('current-policy',sources))
        if denied:raise LookupError('Owned revoked-source fixture')
    monkeypatch.setattr(api,'resolve_principal',resolve)
    monkeypatch.setattr(api,'reauthorize_response_sources',authorize)
    async def request():
        with store.identity_context(IDENTITY):
            store._request_sources.get().add(['private-source'])
            return await api.protect_private_response(StreamingResponse(stream()),'Bearer synthetic-token',IDENTITY)
    return asyncio.run(request()),events


def test_private_body_is_released_only_after_fresh_identity_and_policy_check(monkeypatch):
    response,events=run(monkeypatch)
    assert response.status_code==200 and response.body==b'PRIVATE_CANARY'
    assert events==['serialize','fresh-authentication',('current-policy',['private-source'])]


def test_revocation_after_serialization_withholds_every_original_byte(monkeypatch):
    response,events=run(monkeypatch,denied=True)
    assert response.status_code==404 and b'PRIVATE_CANARY' not in response.body
    assert events[-1]==('current-policy',['private-source'])


@pytest.mark.parametrize('fresh',[{**IDENTITY,'role':'viewer'},
                                 HTTPException(401,'Unauthorized')])
def test_role_change_or_deleted_credential_withholds_private_body(monkeypatch,fresh):
    response,events=run(monkeypatch,fresh=fresh)
    assert response.status_code==401 and b'PRIVATE_CANARY' not in response.body
    assert not any(isinstance(e,tuple) for e in events)


def test_response_allocation_is_bounded_before_authorization_or_release(monkeypatch):
    response,events=run(monkeypatch,body=b'x'*(32*1024*1024+1))
    assert response.status_code==503 and len(response.body)<200
    assert events==['serialize']
