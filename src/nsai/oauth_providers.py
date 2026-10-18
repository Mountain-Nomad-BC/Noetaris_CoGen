"""Fixed-provider OAuth transports. Account binding belongs to NSAI, never email.

No routes are activated here. Callers must supply a durable, single-use state
cache and browser-bound session before using Authlib's redirect/callback flow.
"""
from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

from .store import _secret


PROVIDERS = frozenset({'google', 'github'})


@dataclass(frozen=True)
class ProviderSettings:
    name: str
    client_id: str
    client_secret: str = field(repr=False)
    origin: str

    @property
    def callback(self):
        return self.origin + '/auth/' + self.name + '/callback'


def _https_origin(raw):
    """An operator-controlled HTTPS origin; never derive redirects from Host."""
    parsed = urlsplit(raw)
    if (not 1 <= len(raw) <= 250 or not raw.isascii()
            or any(ord(c) <= 32 or ord(c) >= 127 for c in raw)
            or parsed.scheme != 'https' or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.path or parsed.query or parsed.fragment
            or '\\' in raw or '%' in raw or raw.endswith(':')
            or raw != 'https://' + parsed.netloc):
        raise ValueError('OAuth requires an explicit HTTPS public origin')
    try:
        port=parsed.port
        if port is not None and not 1<=port<=65535:
            raise ValueError('Invalid HTTPS origin port')
    except ValueError:
        raise ValueError('Invalid HTTPS origin port') from None
    if not re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?', parsed.hostname):
        raise ValueError('Invalid OAuth public hostname')
    if any(not part or len(part) > 63 or part.startswith('-') or part.endswith('-')
           for part in parsed.hostname.split('.')):
        raise ValueError('Invalid OAuth public hostname')
    return 'https://' + parsed.hostname + (':'+str(port) if port not in {None,443} else '')


def public_origin():
    return _https_origin(os.getenv('NSAI_PUBLIC_ORIGIN',''))


def frontend_origin():
    api=public_origin()
    configured=os.getenv('NSAI_FRONTEND_ORIGIN','')
    if not configured:return api
    frontend=_https_origin(configured)
    if frontend==api:return frontend
    site=os.getenv('NSAI_DEPLOYMENT_SITE','')
    # Cross-site web.app/OCI-hostname cookies need separate design review. Keep
    # secure SameSite=Lax cookies and require an explicit owned same-site pair.
    if (not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?',site) or '.' not in site or
        urlsplit(api).hostname!='api.'+site or urlsplit(frontend).hostname not in {'app.'+site,site}):
        raise ValueError('Split-origin deployment requires an explicit owned app/API site')
    return frontend


def settings(name):
    if name not in PROVIDERS:
        raise ValueError('Unsupported OAuth provider')
    prefix = 'NSAI_OAUTH_' + name.upper()
    enabled = os.getenv(prefix + '_ENABLED', 'false')
    if enabled not in {'true', 'false'}:
        raise ValueError('Invalid OAuth activation setting')
    if enabled == 'false':
        return None
    origin = public_origin()
    client_id = os.getenv(prefix + '_CLIENT_ID', '')
    if not re.fullmatch(r'[a-zA-Z0-9._-]{1,250}', client_id):
        raise ValueError('Invalid OAuth client identifier')
    path = Path(os.getenv(prefix + '_CLIENT_SECRET_FILE', ''))
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError('Invalid OAuth client secret file')
    return ProviderSettings(name, client_id, _secret(str(path)), origin)


def client(config, *, cache):
    """Authlib owns PKCE, OAuth state, and OIDC signature/claims validation."""
    if cache is None:
        raise ValueError('A durable single-use OAuth state cache is required')
    from authlib.integrations.starlette_client import OAuth
    # Authlib debug logs include PKCE verifiers. Do not emit those in this app.
    logging.getLogger('authlib').setLevel(logging.WARNING)
    oauth = OAuth(cache=cache)
    common = dict(client_id=config.client_id, client_secret=config.client_secret,
                  client_kwargs=dict(code_challenge_method='S256', timeout=5,
                                     trust_env=False, follow_redirects=False,
                                     token_endpoint_auth_method='client_secret_post'))
    if config.name == 'google':
        oauth.register('google', **common,
                       authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
                       access_token_url='https://oauth2.googleapis.com/token',
                       issuer='https://accounts.google.com',
                       jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
                       id_token_signing_alg_values_supported=['RS256'])
        remote = oauth.create_client('google')
        remote.client_kwargs['scope'] = 'openid'
    elif config.name == 'github':
        oauth.register('github', **common,
                       authorize_url='https://github.com/login/oauth/authorize',
                       access_token_url='https://github.com/login/oauth/access_token',
                       api_base_url='https://api.github.com/',
                       access_token_params={'headers': {'Accept': 'application/json'}})
        remote = oauth.create_client('github')
        remote.client_kwargs['scope'] = 'read:user'
    else:
        raise ValueError('Unsupported OAuth provider')
    remote.framework.expires_in = 300
    return remote


def _google_subject(claims):
    """Only used after Authlib has verified the signed ID token and nonce."""
    if (not isinstance(claims, dict) or claims.get('iss') != 'https://accounts.google.com'
            or not isinstance(claims.get('sub'), str)
            or not re.fullmatch(r'[a-zA-Z0-9_-]{1,255}', claims['sub'])):
        raise ValueError('Provider identity is not verified')
    return claims['sub']


def _github_subject(profile):
    # Email and handle are mutable optional display data, never authentication.
    if (not isinstance(profile, dict) or profile.get('type') != 'User'
            or type(profile.get('id')) is not int or not 0 < profile['id'] < 2**63):
        raise ValueError('Provider identity is not verified')
    return str(profile['id'])


async def verified_subject(remote, request):
    """Consume server-side state, exchange code, then return only stable identity.

    Provider access/refresh tokens are transient and never returned to the UI or
    persisted by this module. No provider claims can assign an NSAI role.
    """
    token = await remote.authorize_access_token(request)
    if remote.name == 'google':
        # Starlette Authlib parses and validates the ID token before userinfo.
        from authlib.oidc.core import UserInfo
        if (not isinstance(token.get('id_token'), str) or not token['id_token']
                or not isinstance(token.get('userinfo'), UserInfo)):
            raise ValueError('Provider identity is not verified')
        return _google_subject(dict(token.get('userinfo') or {}))
    if remote.name != 'github':
        raise ValueError('Unsupported OAuth provider')
    profile = await remote.get('user', token=token)
    profile.raise_for_status()
    return _github_subject(profile.json())
