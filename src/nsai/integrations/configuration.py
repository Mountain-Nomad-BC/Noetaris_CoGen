"""Bounded, redacted partner setup checks; configuration is not commissioning."""
import os
import re
from pathlib import Path
from urllib.parse import urlsplit

from ..assembly import strict_json
from ..store import _secret

EVOLUS_BINDINGS=('application_id','workflow_id','agent_id','extractor_id')


def evolus_api_base(value):
    if not isinstance(value,str) or not 1<=len(value)<=500 or not value.isascii() or any(ord(c)<=32 for c in value):
        raise ValueError('Invalid Evolus endpoint')
    try:
        parsed=urlsplit(value);port=parsed.port
    except ValueError:raise ValueError('Invalid Evolus endpoint') from None
    if (parsed.scheme!='https' or not parsed.hostname or parsed.username is not None or parsed.password is not None or
        parsed.query or parsed.fragment or '\\' in value or '%' in value or
        (port is not None and not 1<=port<=65535) or
        re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?',parsed.hostname) is None or
        re.fullmatch(r'(?:/[A-Za-z0-9_-]*)*',parsed.path) is None):
        raise ValueError('Invalid Evolus endpoint')
    return value.rstrip('/')


def evolus_configuration(path):
    source=Path(path)
    with source.open('rb') as stream:
        raw=stream.read(16385)
    data=strict_json(raw,max_bytes=16384,max_depth=4,max_items=32)
    if not isinstance(data,dict) or set(data)!=set(EVOLUS_BINDINGS)|{'payload_schema_sha256','api_base'}:
        raise ValueError('Invalid Evolus binding fields')
    evolus_api_base(data['api_base'])
    for field in EVOLUS_BINDINGS:
        if not isinstance(data[field],str) or re.fullmatch(r'[A-Za-z0-9_-]{1,128}',data[field]) is None:
            raise ValueError('Invalid Evolus binding identity')
    if not isinstance(data['payload_schema_sha256'],str) or re.fullmatch(r'[a-f0-9]{64}',data['payload_schema_sha256']) is None:
        raise ValueError('Evolus payload schema requires an exact digest')
    return data


def credential_present(path):
    if not path:return False
    try:_secret(path)
    except (OSError,UnicodeError,RuntimeError,ValueError):return False
    return True


def evolus_setup(config_path=None,key_file=None):
    config_path=os.getenv('NSAI_EVOLUS_CONFIG_FILE','') if config_path is None else config_path
    key_file=os.getenv('NSAI_EVOLUS_API_KEY_FILE','') if key_file is None else key_file
    configured=False;missing=[]
    if not config_path:missing.append('Evolus binding configuration')
    else:
        try:evolus_configuration(config_path);configured=True
        except (OSError,UnicodeError,ValueError,TypeError):missing.append('Verified HTTPS endpoint, application/workflow/agent/extractor bindings and payload schema digest')
    credential=credential_present(key_file)
    if not credential:missing.append('Readable server-side Evolus credential')
    return dict(provider='evolus',configuration_ready=configured and credential,
        status='CONFIGURED_NOT_COMMISSIONED' if configured and credential else 'NOT_CONFIGURED',
        bindings_configured=configured,credential_configured=credential,commissioned=False,
        dispatch_enabled=False,missing=missing,
        next_step='Verify the bound workflow payload/output schema, allowance, source-export authorization and durable execution accounting in the Evolus workspace')


def integration_setup():
    return dict(schema_version='integration-setup/1',partners=[evolus_setup(),
        dict(provider='amd',credential_configured=credential_present(os.getenv('NSAI_AMD_API_KEY_FILE','')),
             commissioned=False,dispatch_enabled=False,
             next_step='Commission the AMD serving target, tokenizer, allowance and controlled source export'),
        dict(provider='openrouter',credential_configured=credential_present(os.getenv('NSAI_OPENROUTER_API_KEY_FILE','')),
             commissioned=False,dispatch_enabled=False,
             next_step='Qualify exact free Gemma routes, tokenizer, availability and controlled source export')])
