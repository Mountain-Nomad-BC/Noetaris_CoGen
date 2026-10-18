"""Canonical provider bindings and opaque sessions in the existing authority."""
from dataclasses import dataclass, field
import hashlib
import os
import re
import secrets
from uuid import uuid4

from fastapi import HTTPException
from . import store


@dataclass(frozen=True)
class SessionCredential:
    token: str = field(repr=False)


@dataclass(frozen=True)
class BrowserProof:
    digest: str
    epoch: int


def browser_epoch(digest):
    _service()
    if not isinstance(digest,str) or not re.fullmatch(r'[a-f0-9]{64}',digest):
        raise ValueError('Invalid browser binding')
    with store.connect() as conn:
        return conn.execute('SELECT nsai_oauth_browser_epoch(%s)',(digest,)).fetchone()[0]


def token_hash(token):
    if not isinstance(token,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{43}',token):
        raise ValueError('Invalid opaque login credential')
    return hashlib.sha256(token.encode('ascii')).hexdigest()


def _service():
    if store.request_identity() is not None:
        raise PermissionError('Login mutation requires authentication service context')


def _lookup_hash(digest):
    if not isinstance(digest,str) or not re.fullmatch(r'[a-f0-9]{64}',digest):
        raise ValueError('Invalid login credential digest')
    with store.connect() as conn:
        return conn.execute('SELECT nsai_oauth_session_resolve(%s)',(digest,)).fetchone()[0]


def _identity(account):
    from .security import ROLES, _configured_credentials
    configured=_configured_credentials()
    if account['authority']=='registry':
        for identity,_ in configured:
            if identity.get('identity_kind')=='local-user' and identity['actor']==account['actor']:
                return identity
        raise HTTPException(401,'Login session is unavailable')
    if account['authority']!='provider':
        raise HTTPException(401,'Login session is unavailable')
    if any(identity['actor']==account['actor'] for identity,_ in configured):
        raise HTTPException(503,'Conflicting canonical account authority')
    return dict(actor=account['actor'],role='operator',permissions=sorted(ROLES['operator']),identity_kind='local-user')


def resolve(credential):
    if not isinstance(credential,SessionCredential):
        raise ValueError('Expected a server-selected session credential')
    try:account=_lookup_hash(token_hash(credential.token))
    except ValueError:raise HTTPException(401,'Login session is unavailable') from None
    if account is None:raise HTTPException(401,'Login session is unavailable')
    try:return _identity(account)
    except (OSError,RuntimeError,UnicodeError,ValueError):
        raise HTTPException(503,'Authentication configuration is invalid') from None


def link_proof(identity, *, credential=None):
    """Internal proof metadata; never put it in provider query parameters."""
    if identity.get('identity_kind')!='local-user':
        raise PermissionError('Link an individual account, not a shared role')
    if credential is not None:
        current=resolve(credential)
        if current!=identity:raise PermissionError('Authentication changed')
        return dict(kind='session',actor=identity['actor'],digest=token_hash(credential.token))
    from .security import _configured_credentials
    for current,secret in _configured_credentials():
        if current==identity:
            return dict(kind='registry',actor=current['actor'],digest=hashlib.sha256(secret).hexdigest())
    raise PermissionError('Local account is unavailable')


def verify_link(proof):
    _service()
    if (not isinstance(proof,dict) or set(proof)!={'kind','actor','digest'}
            or not isinstance(proof['actor'],str)
            or not re.fullmatch(r'local-user-[a-z][a-z0-9_-]{0,63}',proof['actor'])
            or not isinstance(proof['digest'],str) or not re.fullmatch(r'[a-f0-9]{64}',proof['digest'])):
        raise PermissionError('Invalid account linking proof')
    if proof['kind']=='session':
        account=_lookup_hash(proof['digest'])
        if account is None or account['actor']!=proof['actor']:
            raise PermissionError('Linking authentication expired')
        _identity(account)  # Refresh local registry authority where applicable.
        return 'link-'+account['authority'],account['actor']
    if proof['kind']=='registry':
        from .security import _configured_credentials
        for identity,secret in _configured_credentials():
            if (identity.get('identity_kind')=='local-user' and identity['actor']==proof['actor']
                    and secrets.compare_digest(hashlib.sha256(secret).hexdigest(),proof['digest'])):
                return 'link-registry',identity['actor']
    raise PermissionError('Linking authentication changed')


def finish_login(provider,subject,mode,*,proof=None,browser=None):
    """Only call after the provider transport has verified state and identity."""
    _service()
    if mode not in {'login','signup','link'}:raise ValueError('Invalid login mode')
    target='local-user-oauth-'+uuid4().hex if mode=='signup' else None
    if mode=='link':mode,target=verify_link(proof)
    elif proof is not None:raise ValueError('Unexpected account link proof')
    hours=os.getenv('NSAI_OAUTH_SESSION_HOURS','12')
    if not re.fullmatch(r'[1-9][0-9]?',hours) or not 1<=int(hours)<=24:
        raise ValueError('Invalid login session lifetime')
    token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(32)
    from .workflow_store import audit
    with store.connect() as conn:
        if browser is not None:
            if (not isinstance(browser,BrowserProof) or type(browser.epoch) is not int or browser.epoch<1
                    or not re.fullmatch(r'[a-f0-9]{64}',browser.digest)):
                raise ValueError('Invalid browser login proof')
            conn.execute('SELECT nsai_oauth_browser_assert(%s,%s)',(browser.digest,browser.epoch))
        account=conn.execute('SELECT nsai_oauth_bind(%s,%s,%s,%s)',(provider,subject,mode,target)).fetchone()[0]
        if browser is None:
            conn.execute('SELECT nsai_oauth_session_create(%s,%s,%s,%s)',
                         (token_hash(token),token_hash(csrf),account['actor'],int(hours)))
        else:
            conn.execute('SELECT nsai_oauth_session_create(%s,%s,%s,%s,%s,%s)',
                         (token_hash(token),token_hash(csrf),account['actor'],int(hours),browser.digest,browser.epoch))
        if proof is not None:
            if verify_link(proof)!=(mode,target):raise PermissionError('Linking authentication changed')
        # Authentication runs as the service, before any user request binding.
        # Preserve the existing audit RLS; do not impersonate the new user.
        audit(conn,'legacy-service','oauth.authenticated',
              dict(provider=provider,action=mode,account_actor=account['actor']))
    return dict(token=token,csrf=csrf,identity=_identity(account))


def csrf_matches(credential,csrf):
    try:account=_lookup_hash(token_hash(credential.token));digest=token_hash(csrf)
    except (ValueError,AttributeError):return False
    return account is not None and secrets.compare_digest(account['csrf_hash'],digest)


def revoke(credential):
    digest=token_hash(credential.token)
    from .workflow_store import audit
    with store.connect() as conn:
        account=conn.execute('SELECT nsai_oauth_session_resolve(%s)',(digest,)).fetchone()[0]
        if account is None:return False
        changed=conn.execute('SELECT nsai_oauth_session_revoke(%s)',(digest,)).fetchone()[0]
        if changed:
            identity=store.request_identity()
            audit(conn,identity['actor'] if identity else 'legacy-service',
                  'oauth.logged-out',dict(account_actor=account['actor']))
        return changed


def end_browser(digest,credential=None):
    _service()
    from .workflow_store import audit
    with store.connect() as conn:
        changed=conn.execute('SELECT nsai_oauth_browser_cancel(%s)',(digest,)).fetchone()[0]
        # Older service-created sessions without a browser association are
        # revoked explicitly as well; no other device's sessions are changed.
        if credential is not None:
            conn.execute('SELECT nsai_oauth_session_revoke(%s)',(token_hash(credential.token),))
        audit(conn,'legacy-service','oauth.browser-signed-out',dict(revoked_sessions=changed))
    return changed
