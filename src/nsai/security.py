"""Local role authority remains active with central integration disabled."""
import os
import secrets
import re
from pathlib import Path
from typing import Annotated
from fastapi import Header, HTTPException, Depends
from pydantic import BaseModel, ConfigDict, Field
from .store import _secret
from urllib.parse import urlsplit

ROLES = {'operator':{'read','ingest','chat','propose'}, 'viewer':{'read'},
         'reviewer':{'read','review'}, 'admin':{'read','review','admin'}}
FILES = {'operator':'NSAI_API_TOKEN_FILE','viewer':'NSAI_VIEWER_TOKEN_FILE',
         'reviewer':'NSAI_REVIEWER_TOKEN_FILE','admin':'NSAI_ADMIN_TOKEN_FILE'}

def _local_identities():
    """Reload a bounded operator-owned registry; clients cannot select roles."""
    setting = os.getenv('NSAI_LOCAL_IDENTITIES_FILE')
    if not setting:
        return []
    from .assembly import strict_json
    path = Path(setting)
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError('Invalid identity registry path')
    with path.open('rb') as stream:
        raw = stream.read(65537)
    registry = strict_json(raw, max_bytes=65536, max_depth=4, max_items=5000)
    if (not isinstance(registry, dict) or set(registry) != {'schema_version','identities'}
            or registry['schema_version'] != 'nsai.local-identities/1'
            or not isinstance(registry['identities'], list)
            or not 1 <= len(registry['identities']) <= 1000):
        raise ValueError('Invalid identity registry')
    result=[]; seen=set()
    for entry in registry['identities']:
        if not isinstance(entry,dict) or set(entry) != {'actor','role','token_file'}:
            raise ValueError('Invalid local identity')
        actor=entry['actor']; role=entry['role']; filename=entry['token_file']
        if (not isinstance(actor,str) or not re.fullmatch(r'local-user-[a-z][a-z0-9_-]{0,63}',actor)
                or actor in seen or not isinstance(role,str) or role not in ROLES
                or not isinstance(filename,str) or not 1 <= len(filename) <= 4096):
            raise ValueError('Invalid local identity')
        secret_path=Path(filename)
        if not secret_path.is_absolute() or secret_path.is_symlink() or not secret_path.is_file():
            raise ValueError('Invalid local credential path')
        seen.add(actor)
        result.append((dict(actor=actor,role=role,permissions=sorted(ROLES[role]),identity_kind='local-user'),filename))
    return result


def principal(authorization: Annotated[str | None, Header()] = None):
    # HTTP middleware authenticates once, before binding the request context.
    # Pin the same identity across dependency execution and registry hot reloads.
    from .store import request_identity
    pinned=request_identity()
    if pinned is not None:return pinned
    return resolve_principal(authorization)


def resolve_principal(authorization):
    """Fresh credential/registry resolution, including before private release."""
    from .oauth_accounts import SessionCredential,resolve as resolve_session
    if isinstance(authorization,SessionCredential):return resolve_session(authorization)
    if not os.getenv('NSAI_API_TOKEN_FILE') and not os.getenv('NSAI_LOCAL_IDENTITIES_FILE'):
        from .oauth_http import active
        try:configured=active()
        except ValueError:raise HTTPException(503,'Authentication configuration is invalid') from None
        if not configured:raise HTTPException(503,'Authentication is not configured')
    if (not isinstance(authorization,str) or len(authorization)>1031 or
        not authorization.startswith('Bearer ') or not authorization.isascii()):
        raise HTTPException(401,'Unauthorized',headers={'WWW-Authenticate':'Bearer'})
    supplied = authorization[7:]
    if not 1<=len(supplied)<=1024 or any(ord(c)<=32 or ord(c)>=127 for c in supplied):
        raise HTTPException(401,'Unauthorized',headers={'WWW-Authenticate':'Bearer'})
    try:
        configured=_configured_credentials()
    except (OSError, RuntimeError, UnicodeError, ValueError):
        raise HTTPException(503,'Authentication configuration is invalid') from None
    # Resolve identity only after the entire configured role set is valid and unique.
    for identity, expected in configured:
        if secrets.compare_digest(expected, supplied.encode('ascii')):
            return identity
    raise HTTPException(401,'Unauthorized',headers={'WWW-Authenticate':'Bearer'})


def _configured_credentials():
    """Validate the entire existing authority before resolving/linking a user."""
    configured=[];identities=[]
    for role,setting in FILES.items():
        path=os.getenv(setting)
        if path:
            identities.append((dict(actor='local-'+role,role=role,permissions=sorted(ROLES[role])),path))
    identities.extend(_local_identities())
    for identity,path in identities:
        expected=_secret(path)
        if (not isinstance(expected,str) or not expected.isascii() or not 1<=len(expected)<=1024
                or any(ord(c)<=32 or ord(c)>=127 for c in expected)):
            raise ValueError('Invalid credential syntax')
        encoded=expected.encode('ascii')
        if any(secrets.compare_digest(encoded,previous) for _,previous in configured):
            raise ValueError('Duplicate configured credential')
        configured.append((identity,encoded))
    return configured

def require(permission):
    def check(identity=Depends(principal)):
        if permission not in identity['permissions']:
            raise HTTPException(403,'Role does not permit this operation')
        return identity
    return check

class CentralConfiguration(BaseModel):
    model_config = ConfigDict(extra='forbid')
    enabled: bool = False
    provider: str = Field(default='none',pattern=r'^(none|remy-rie|oidc)$')
    issuer: str | None = Field(default=None,max_length=250)

    def staged(self):
        if self.enabled:
            raise ValueError('Central activation requires separate authorization and a validated adapter')
        if self.issuer:
            parsed=urlsplit(self.issuer)
            if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError('Staged issuer must be an HTTPS identity URL without credentials/query/fragment')
        return self.model_dump()

class PolicyUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_revision: int = Field(ge=1)
    inference_enabled: bool
    daily_call_limit: int = Field(ge=1,le=1000)
    max_output_tokens: int = Field(ge=32,le=512)
    central_config: CentralConfiguration = Field(default_factory=CentralConfiguration)

def security_status():
    return dict(central_integration_enabled=False,central_adapter_state='staged-interface-only',
        local_authentication='active',roles={k:sorted(v) for k,v in ROLES.items()},project_scope='single local project',
        generated_code_execution='disabled',approvals='independent reviewer and optimistic revision',
        limitations=['Shared demo role tokens; production OIDC/TLS pending',
                    'No Linux Gremlin execution backend or arbitrary generated-code runner'])
