"""Real NSAI HTTP/PG OAuth flows; only the external Google transport is synthetic."""
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
from threading import Event
import time
from urllib.parse import parse_qs,urlsplit
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient
from joserfc import jwt
from joserfc.jwk import RSAKey
from nsai import api,oauth_accounts as accounts,oauth_providers as providers,security,store,workflow_store as workflows

def secret(name,value):
    path=Path('/tmp/'+name);path.write_text(value);return str(path)

for setting in [*security.FILES.values(),'NSAI_LOCAL_IDENTITIES_FILE']:os.environ.pop(setting,None)
origin='https://nsai.example'
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',
    NSAI_DB_PASSWORD_FILE=secret('db-password','x'*48),NSAI_API_TOKEN_FILE=secret('local-role','o'*48),
    NSAI_PUBLIC_ORIGIN=origin,NSAI_OAUTH_COOKIE_SECRET_FILE=secret('cookie-key','k'*48),
    NSAI_OAUTH_GOOGLE_ENABLED='true',NSAI_OAUTH_GOOGLE_CLIENT_ID='fixture-google-client',
    NSAI_OAUTH_GOOGLE_CLIENT_SECRET_FILE=secret('google-key','g'*48),NSAI_OAUTH_GITHUB_ENABLED='false',
    NSAI_RATE_LIMIT_BACKEND='local',NSAI_AUTH_REQUESTS_PER_MINUTE='1000',
    NSAI_AUTH_PEER_REQUESTS_PER_MINUTE='1000',NSAI_AUTH_BROWSER_REQUESTS_PER_MINUTE='1000')
key=RSAKey.generate_key(2048);key.ensure_kid();codes={};token_calls=[]
real_client=providers.client

def google_transport(request):
    if request.url.host=='www.googleapis.com':return httpx.Response(200,json={'keys':[key.as_dict(private=False)]})
    assert request.url.host=='oauth2.googleapis.com'
    form=parse_qs(request.content.decode());record=codes[form['code'][0]]
    challenge=base64.urlsafe_b64encode(hashlib.sha256(form['code_verifier'][0].encode()).digest()).rstrip(b'=').decode()
    assert challenge==record['challenge'] and form['client_secret']==['g'*48]
    token_calls.append(record['subject']);now=int(time.time())
    claims=dict(iss='https://accounts.google.com',sub=record['subject'],aud='fixture-google-client',
                iat=now,exp=now+300,nonce=record['nonce'],email_verified=True)
    return httpx.Response(200,json=dict(access_token='synthetic-provider-access',token_type='bearer',
        id_token=jwt.encode({'alg':'RS256','kid':key.kid},claims,key)))

def provider_client(config,*,cache):
    remote=real_client(config,cache=cache)
    remote.client_kwargs['transport']=httpx.MockTransport(google_transport)
    return remote
providers.client=provider_client

def begin(client,mode,subject,*,actor=None,bearer=None):
    config=client.get('/auth/config');assert config.status_code==200
    headers={'Origin':origin,'X-CSRF-Token':config.json()['csrf']}
    if actor:headers['X-NSAI-Expected-Actor']=actor
    if bearer:headers['Authorization']='Bearer '+bearer
    response=client.post('/auth/google/start',json={'mode':mode},headers=headers)
    assert response.status_code==200,response.text
    url=response.json()['authorization_url'];params=parse_qs(urlsplit(url).query)
    assert urlsplit(url).netloc=='accounts.google.com'
    assert params['code_challenge_method']==['S256'] and (not actor or actor not in url)
    code=uuid4().hex;codes[code]=dict(subject=subject,nonce=params['nonce'][0],challenge=params['code_challenge'][0])
    return dict(code=code,state=params['state'][0]),config.json()['csrf']

def complete(client,pending):
    result=client.get('/auth/google/callback',params=pending,follow_redirects=False)
    assert result.status_code==303
    return result.headers['location']

def session(client):
    result=client.get('/auth/session');assert result.status_code==200,result.text
    return result.json()

with TestClient(api.app,base_url=origin) as alice,TestClient(api.app,base_url=origin) as bob,TestClient(api.app,base_url=origin) as other_device:
    pending,_=begin(alice,'signup','provider-alice');assert complete(alice,pending).endswith('auth=complete')
    initial_cookie=alice.cookies.get('__Host-nsai-session');assert 'synthetic-provider-access' not in initial_cookie
    first=session(alice);actor=first['identity']['actor']
    assert first['identity']['role']=='operator' and actor.startswith('local-user-oauth-')
    caps=alice.get('/v1/capabilities',headers={'X-NSAI-Expected-Actor':actor})
    assert caps.status_code==200 and caps.headers['X-NSAI-Actor']==actor
    assert caps.json()['content_access']['admitted'] is False
    assert alice.get('/v1/documents').status_code==503
    assert alice.post('/v1/chat',json={'question':'not a generation'}).status_code==403
    pending,_=begin(bob,'signup','provider-bob');assert complete(bob,pending).endswith('auth=complete')
    bob_actor=session(bob)['identity']['actor'];assert actor!=bob_actor
    pending,_=begin(other_device,'login','provider-alice');assert complete(other_device,pending).endswith('auth=complete')
    assert session(other_device)['identity']['actor']==actor

    # A state from another browser cannot redeem even a valid signed code.
    pending,_=begin(alice,'link','provider-alice',actor=actor)
    before=len(token_calls)
    assert complete(bob,pending).endswith('auth=failed') and len(token_calls)==before
    assert complete(alice,pending).endswith('auth=complete')
    pending,_=begin(alice,'link','provider-bob',actor=actor)
    assert complete(alice,pending).endswith('auth=failed')
    assert session(alice)['identity']['actor']==actor and session(bob)['identity']['actor']==bob_actor
    latest_cookie=alice.cookies.get('__Host-nsai-session')

    # Logout revokes both browser-local login generations, not other devices.
    config=alice.get('/auth/config').json()
    assert alice.post('/auth/logout',headers={'Origin':origin,'X-CSRF-Token':config['csrf']}).status_code==200
    for captured in [initial_cookie,latest_cookie]:
        with TestClient(api.app,base_url=origin) as replay:
            replay.cookies.set('__Host-nsai-session',captured)
            assert replay.get('/v1/capabilities').status_code==401
    assert session(other_device)['identity']['actor']==actor
    assert session(bob)['identity']['actor']==bob_actor

# Explicit local linking preserves existing owner and hot-reloads its role.
registry_path=Path('/tmp/local-identities.json');local_token=secret('individual-local','r'*48)
registry=dict(schema_version='nsai.local-identities/1',identities=[dict(actor='local-user-alice',role='operator',token_file=local_token)])
registry_path.write_text(json.dumps(registry));os.environ['NSAI_LOCAL_IDENTITIES_FILE']=str(registry_path)
with TestClient(api.app,base_url=origin) as local:
    pending,_=begin(local,'link','local-provider-alice',actor='local-user-alice',bearer='r'*48)
    assert complete(local,pending).endswith('auth=complete')
    assert session(local)['identity']['actor']=='local-user-alice'
    registry['identities'][0]['role']='viewer';registry_path.write_text(json.dumps(registry))
    assert session(local)['identity']['permissions']==['read']
    with store.identity_context(session(local)['identity']):
        with store.connect() as conn:assert conn.execute("SELECT owner_scope FROM documents WHERE id='private'").fetchone()[0]=='local-user-alice'

# Force a genuine overlapping callback commit/logout at the PostgreSQL row lock.
prepared=Event();release=Event();original_audit=workflows.audit
def held_audit(conn,actor,event,details):
    if event=='oauth.authenticated' and details.get('action')=='signup':
        prepared.set();assert release.wait(10),'Callback synchronization deadline'
    return original_audit(conn,actor,event,details)
with TestClient(api.app,base_url=origin) as racing,TestClient(api.app,base_url=origin) as cancelling:
    pending,csrf=begin(racing,'signup','racing-provider-user')
    cancelling.cookies.set('__Host-nsai-session',racing.cookies.get('__Host-nsai-session'))
    workflows.audit=held_audit
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            callback=pool.submit(complete,racing,pending)
            assert prepared.wait(10),'Callback never reached transaction gate'
            logout=pool.submit(cancelling.post,'/auth/logout',headers={'Origin':origin,'X-CSRF-Token':csrf})
            deadline=time.monotonic()+5;blocked=False
            with store.connect() as conn:
                while time.monotonic()<deadline:
                    conn.execute('SELECT pg_stat_clear_snapshot()')
                    blocked=conn.execute("SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE usename=current_user AND pid<>pg_backend_pid() AND wait_event_type='Lock' AND query LIKE 'SELECT nsai_oauth_browser_cancel%')").fetchone()[0]
                    if blocked:break
                    time.sleep(.02)
            assert blocked,'Logout did not overlap the held callback transaction'
            release.set()
            assert callback.result(timeout=10).endswith('auth=complete')
            assert logout.result(timeout=10).status_code==200
    finally:release.set();workflows.audit=original_audit
    assert racing.get('/v1/capabilities').status_code==401

with store.connect() as conn:assert conn.execute('SELECT nsai_daily_inference_count()').fetchone()[0]==0
assert workflows.audit_report()['valid'] is True
print(json.dumps(dict(status='PASS_SCOPED',real_http_and_postgres=True,synthetic_external_provider_only=True,
    signup_login_link_logout=True,pkce_signed_oidc=True,cross_browser_state_denied=True,
    account_takeover_denied=True,browser_cookie_replay_denied=True,other_devices_preserved=True,
    local_owner_and_roles_preserved=True,inflight_callback_logout_race=True,auth_generations=0,
    audit_chain_valid=True,private_content_gate_closed=True)))
