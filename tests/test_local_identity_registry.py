"""Synthetic registry/credentials; no real runtime configuration is accessed."""
import json
import pytest
from fastapi import HTTPException
from nsai import security


@pytest.fixture
def registry(tmp_path,monkeypatch):
    for setting in security.FILES.values():monkeypatch.delenv(setting,raising=False)
    monkeypatch.delenv('NSAI_LOCAL_IDENTITIES_FILE',raising=False)
    entries=[];tokens={}
    for name in ['alice','bob']:
        token=(name+'-synthetic-credential-').ljust(48,'x')
        path=tmp_path/(name+'.txt');path.write_text(token,encoding='utf-8')
        entries.append(dict(actor='local-user-'+name,role='operator',token_file=str(path)))
        tokens[name]=token
    payload=dict(schema_version='nsai.local-identities/1',identities=entries)
    path=tmp_path/'identities.json'
    def write(value=None):
        path.write_text(json.dumps(payload if value is None else value),encoding='utf-8')
    write();monkeypatch.setenv('NSAI_LOCAL_IDENTITIES_FILE',str(path))
    return payload,path,tokens,write


def rejected(token,status=503):
    with pytest.raises(HTTPException) as error:security.principal('Bearer '+token)
    assert error.value.status_code==status
    assert token not in error.value.detail


def test_same_role_users_have_distinct_stable_actors_and_no_groups(registry):
    payload,path,tokens,write=registry
    alice=security.principal('Bearer '+tokens['alice']);bob=security.principal('Bearer '+tokens['bob'])
    assert alice==dict(actor='local-user-alice',role='operator',permissions=sorted(security.ROLES['operator']),identity_kind='local-user')
    assert alice['actor']!=bob['actor'] and alice['permissions']==bob['permissions']
    assert 'groups' not in alice


@pytest.mark.parametrize('mutation',[
    lambda p:p.update(schema_version=1),
    lambda p:p.update(extra=True),
    lambda p:p.update(identities=[]),
    lambda p:p.update(identities=[None]),
    lambda p:p['identities'][1].update(actor='local-user-alice'),
    lambda p:p['identities'][1].update(actor='local-admin'),
    lambda p:p['identities'][1].update(role='root'),
    lambda p:p['identities'][1].update(role=[]),
    lambda p:p['identities'][1].update(groups=['administrators']),
    lambda p:p['identities'][1].update(token_file='relative.txt'),
    lambda p:p['identities'][1].update(token_file=None),
    lambda p:p.update(identities=p['identities']*501),
])
def test_malformed_registry_fails_closed_before_early_match(registry,mutation):
    payload,path,tokens,write=registry;mutation(payload);write()
    rejected(tokens['alice'])


@pytest.mark.parametrize('raw',[b'{"schema_version":1,"schema_version":2}',b'NaN',b'\xff',b' '*65537],ids=['duplicate-key','nonfinite','invalid-utf8','oversized'])
def test_registry_encoding_duplicate_keys_and_size_are_bounded(registry,raw):
    payload,path,tokens,write=registry;path.write_bytes(raw);rejected(tokens['alice'])


def test_missing_registry_fails_configuration(registry):
    payload,path,tokens,write=registry;path.unlink();rejected(tokens['alice'])


@pytest.mark.parametrize('value',['missing','invalid','collision'])
def test_later_credential_failure_cannot_be_hidden_by_early_match(registry,value):
    payload,path,tokens,write=registry
    from pathlib import Path
    later=Path(payload['identities'][1]['token_file'])
    if value=='missing':later.unlink()
    elif value=='invalid':later.write_text('white space'.ljust(48,'x'))
    else:later.write_text(tokens['alice'])
    rejected(tokens['alice'])


def test_registry_and_legacy_credential_collision_fails_closed(registry,monkeypatch):
    payload,path,tokens,write=registry
    monkeypatch.setenv('NSAI_API_TOKEN_FILE',payload['identities'][0]['token_file'])
    rejected(tokens['alice'])


def test_legacy_identity_remains_compatible_with_registry(registry,monkeypatch,tmp_path):
    payload,path,tokens,write=registry
    token='legacy-synthetic-credential-'.ljust(48,'x')
    secret=tmp_path/'legacy.txt';secret.write_text(token)
    monkeypatch.setenv('NSAI_API_TOKEN_FILE',str(secret))
    assert security.principal('Bearer '+token)==dict(actor='local-operator',role='operator',permissions=sorted(security.ROLES['operator']))
    assert security.principal('Bearer '+tokens['alice'])['identity_kind']=='local-user'


def test_hot_reload_removes_identity_and_invalid_registry_fails_closed(registry):
    payload,path,tokens,write=registry
    assert security.principal('Bearer '+tokens['alice'])['actor']=='local-user-alice'
    payload['identities']=payload['identities'][1:];write()
    rejected(tokens['alice'],401)
    assert security.principal('Bearer '+tokens['bob'])['actor']=='local-user-bob'
    path.write_text('{}');rejected(tokens['bob'])


def test_malformed_bearer_does_not_read_registry(registry,monkeypatch):
    monkeypatch.setattr(security,'_local_identities',lambda:pytest.fail('Malformed bearer read registry'))
    with pytest.raises(HTTPException) as error:security.principal('Bearer bad space')
    assert error.value.status_code==401


def test_unknown_registry_token_does_not_fall_back_to_a_role(registry):
    rejected('unknown-synthetic-credential'.ljust(48,'x'),401)
