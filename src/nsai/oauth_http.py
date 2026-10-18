"""Direct OAuth HTTP coordination. Canonical identity and content stay in NSAI."""
import asyncio
from collections import deque
import hashlib
import hmac
import os
from pathlib import Path
import re
import secrets
from threading import Lock
import time

from fastapi import APIRouter,HTTPException,Request
from fastapi.responses import JSONResponse,RedirectResponse
from pydantic import BaseModel,ConfigDict
from typing import Literal
from . import oauth_accounts as accounts,oauth_providers as providers,shared_rate_limit
from .oauth_state import PostgresStateCache
from .store import _secret

router=APIRouter(prefix='/auth')
_events=deque();_lock=Lock()


def enabled(name):
    value=os.getenv('NSAI_OAUTH_'+name.upper()+'_ENABLED','false')
    if value not in {'true','false'}:raise ValueError('Invalid OAuth activation setting')
    return value=='true'


def active():
    flags=[enabled(name) for name in sorted(providers.PROVIDERS)]
    return any(flags) or bool(os.getenv('NSAI_OAUTH_COOKIE_SECRET_FILE'))


def cookie_secret():
    providers.public_origin()
    path=Path(os.getenv('NSAI_OAUTH_COOKIE_SECRET_FILE',''))
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError('Invalid OAuth cookie signing secret')
    return _secret(str(path))


def validate_runtime():
    if os.getenv('NSAI_FRONTEND_ORIGIN'):providers.frontend_origin()
    if not active():return
    secret=cookie_secret()
    authentication_limits()
    for name in sorted(providers.PROVIDERS):
        config=providers.settings(name)
        if config is not None and secrets.compare_digest(config.client_secret,secret):
            raise ValueError('OAuth cookie and provider secrets must be distinct')


class BrowserSessions:
    def __init__(self,app):self.app=app

    async def __call__(self,scope,receive,send):
        if scope['type'] not in {'http','websocket'}:
            return await self.app(scope,receive,send)
        try:
            selected=active()
            if selected:
                from starlette.middleware.sessions import SessionMiddleware
                from itsdangerous import TimestampSigner
                secret=cookie_secret()
                middleware=SessionMiddleware(self.app,secret_key=secret,
                    session_cookie='__Host-nsai-session',max_age=86400,
                    same_site='lax',https_only=True)
                middleware.signer=TimestampSigner(secret,salt='nsai.browser-session.v1',digest_method=hashlib.sha256)
        except (ValueError,OSError,RuntimeError):
            if scope['type']=='websocket':return await send({'type':'websocket.close','code':1011})
            response=JSONResponse({'detail':'Authentication configuration unavailable'},503,
                                  headers={'Cache-Control':'no-store'})
            return await response(scope,receive,send)
        return await (middleware if selected else self.app)(scope,receive,send)


def request_credential(request):
    supplied=request.headers.get('Authorization')
    if supplied is not None:return supplied
    return browser_credential(request)


def browser_credential(request):
    token=request.scope.get('session',{}).get('token')
    return accounts.SessionCredential(token) if token is not None else None


def _browser(request):
    if not active() or 'session' not in request.scope:
        raise HTTPException(503,'Browser authentication is not configured')
    session=request.session
    if not isinstance(session.get('binding'),str) or not re.fullmatch(r'[a-zA-Z0-9_-]{43}',session['binding']):
        session['binding']=secrets.token_urlsafe(32)
    if not isinstance(session.get('csrf'),str) or not re.fullmatch(r'[a-zA-Z0-9_-]{43}',session['csrf']):
        session['csrf']=secrets.token_urlsafe(32)
    return session


def _origin_csrf(request):
    session=_browser(request)
    supplied=request.headers.get('X-CSRF-Token','')
    if (request.headers.get('Origin')!=providers.frontend_origin() or not supplied.isascii()
            or not secrets.compare_digest(supplied,session['csrf'])):
        raise HTTPException(403,'Browser origin or CSRF proof is invalid')


async def protect_mutation(request,credential):
    _origin_csrf(request)
    if not await asyncio.to_thread(accounts.csrf_matches,credential,request.headers.get('X-CSRF-Token')):
        raise HTTPException(403,'Login CSRF proof is invalid')


def _allow_local(digests,limits):
    now=time.monotonic()
    with _lock:
        while _events and _events[0][0]<=now-60:_events.popleft()
        if any(sum(keys[index]==digest for _,keys in _events)>=limit
               for index,(digest,limit) in enumerate(zip(digests,limits))):return False
        _events.append((now,tuple(digests)))
        return True


def authentication_limits():
    limits=[]
    for setting,default in [('NSAI_AUTH_REQUESTS_PER_MINUTE',60),('NSAI_AUTH_PEER_REQUESTS_PER_MINUTE',60),('NSAI_AUTH_BROWSER_REQUESTS_PER_MINUTE',20)]:
        raw=os.getenv(setting,str(default))
        if not re.fullmatch(r'[1-9][0-9]{0,3}',raw) or not 1<=int(raw)<=1000:
            raise ValueError('Invalid authentication request allowance')
        limits.append(int(raw))
    return limits


async def _budget(request):
    session=_browser(request);secret=cookie_secret().encode('ascii')
    peer=request.client.host if request.client else 'unknown'
    values=['global','peer:'+peer,'browser:'+session['binding']]
    digests=[hmac.new(secret,('nsai-auth:'+value).encode(),hashlib.sha256).hexdigest() for value in values]
    try:limits=authentication_limits()
    except ValueError:raise HTTPException(503,'Authentication allowance unavailable') from None
    try:
        allowed=(await asyncio.to_thread(shared_rate_limit.admit_auth,digests,limits)
                 if shared_rate_limit.backend()=='redis' else _allow_local(digests,limits))
    except (ValueError,RuntimeError,OSError,KeyError):
        raise HTTPException(503,'Authentication coordination unavailable') from None
    if not allowed:raise HTTPException(429,'Authentication request limit reached',headers={'Retry-After':'60'})


class StartInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    mode:Literal['login','signup','link']='login'


@router.get('/config')
async def configuration(request:Request):
    flags={name:enabled(name) for name in sorted(providers.PROVIDERS)}
    if not active():return dict(providers=flags,csrf=None)
    await _budget(request)
    digest=hashlib.sha256(request.session['binding'].encode()).hexdigest()
    epoch=await asyncio.to_thread(accounts.browser_epoch,digest)
    if request.session.get('epoch')!=epoch:request.session['epoch']=epoch
    return dict(providers=flags,csrf=request.session['csrf'])


@router.get('/session')
async def current_session(request:Request):
    if not active():
        raise HTTPException(401,'No browser login session')
    await _budget(request)
    credential=browser_credential(request)
    if not isinstance(credential,accounts.SessionCredential):raise HTTPException(401,'No browser login session')
    identity=await asyncio.to_thread(accounts.resolve,credential)
    if not await asyncio.to_thread(accounts.csrf_matches,credential,request.session['csrf']):
        raise HTTPException(401,'Browser login session changed')
    return dict(identity=identity,csrf=request.session['csrf'])


@router.post('/logout')
async def logout(request:Request):
    _origin_csrf(request);await _budget(request)
    credential=browser_credential(request)
    digest=hashlib.sha256(request.session['binding'].encode()).hexdigest()
    # Keep the signed binding on failure so a retry can revoke the same browser
    # sessions. Never claim logout or discard its revocation handle prematurely.
    await asyncio.to_thread(accounts.end_browser,digest,credential)
    request.session.clear()
    return dict(logged_out=True)


@router.post('/{provider}/start')
async def start(provider:str,body:StartInput,request:Request):
    _origin_csrf(request);await _budget(request)
    if provider not in providers.PROVIDERS:raise HTTPException(404,'OAuth provider unavailable')
    config=providers.settings(provider)
    if config is None:raise HTTPException(404,'OAuth provider unavailable')
    epoch=request.session.get('epoch')
    if type(epoch) is not int or epoch<1:raise HTTPException(409,'Refresh browser authentication before continuing')
    context=dict(mode=body.mode,browser_epoch=epoch)
    credential=request_credential(request)
    if body.mode=='link':
        from .security import resolve_principal
        identity=await asyncio.to_thread(resolve_principal,credential)
        if request.headers.get('X-NSAI-Expected-Actor')!=identity['actor']:
            raise HTTPException(401,'Account identity changed; reload before linking')
        try:
            context['proof']=await asyncio.to_thread(accounts.link_proof,identity,
                credential=credential if isinstance(credential,accounts.SessionCredential) else None)
        except PermissionError:
            raise HTTPException(403,'Linking requires a verified individual account') from None
    elif isinstance(credential,accounts.SessionCredential):
        try:await asyncio.to_thread(accounts.resolve,credential)
        except HTTPException as error:
            if error.status_code!=401:raise
            request.session.pop('token',None)
        else:raise HTTPException(409,'Sign out before switching accounts')
    binding=hashlib.sha256(request.session['binding'].encode()).hexdigest()
    cache=PostgresStateCache(binding,context=context)
    remote=providers.client(config,cache=cache)
    response=await remote.authorize_redirect(request,config.callback)
    return dict(authorization_url=response.headers['location'])


@router.get('/{provider}/callback')
async def callback(provider:str,request:Request):
    await _budget(request)
    if provider not in providers.PROVIDERS:raise HTTPException(404,'OAuth provider unavailable')
    config=providers.settings(provider)
    if config is None:raise HTTPException(404,'OAuth provider unavailable')
    query=request.query_params
    if (any(len(query.getlist(key))!=1 for key in query)
            or not re.fullmatch(r'[a-zA-Z0-9_-]{20,128}',query.get('state',''))
            or len(query.get('code',''))>2048 or len(query.get('error',''))>128
            or bool(query.get('code'))==bool(query.get('error'))):
        raise HTTPException(400,'Invalid OAuth callback')
    binding=hashlib.sha256(request.session['binding'].encode()).hexdigest()
    cache=PostgresStateCache(binding)
    remote=providers.client(config,cache=cache)
    try:
        if query.get('error'):
            state=await remote.framework.get_state_data(request.session,query['state'])
            await remote.framework.clear_state_data(request.session,query['state'])
            if state is None:raise ValueError('Invalid cancelled state')
            return RedirectResponse(providers.frontend_origin()+'/?auth=cancelled',303)
        subject=await providers.verified_subject(remote,request)
        context=(cache.consumed or {}).get('nsai_context',{})
        if context.get('mode') not in {'login','signup','link'}:raise ValueError('Missing login context')
        epoch=context.get('browser_epoch')
        if type(epoch) is not int or epoch<1:raise ValueError('Missing browser authentication epoch')
        result=await asyncio.to_thread(accounts.finish_login,provider,subject,context['mode'],
            proof=context.get('proof'),browser=accounts.BrowserProof(binding,epoch))
    except Exception:
        return RedirectResponse(providers.frontend_origin()+'/?auth=failed',303)
    browser_binding=request.session['binding']
    request.session.clear()
    request.session.update(token=result['token'],csrf=result['csrf'],binding=browser_binding,epoch=epoch)
    return RedirectResponse(providers.frontend_origin()+'/?auth=complete',303)
