import hashlib
import pytest
from fastapi import HTTPException
from nsai import oauth_accounts as accounts,security,store
from test_local_identity_registry import registry


def test_registry_link_uses_current_roles_and_rejects_rotated_credentials(registry,monkeypatch):
    payload,path,tokens,write=registry
    identity=security.resolve_principal('Bearer '+tokens['alice'])
    proof=accounts.link_proof(identity)
    assert accounts.verify_link(proof)==('link-registry','local-user-alice')
    monkeypatch.setattr(accounts,'_lookup_hash',lambda _:dict(actor='local-user-alice',authority='registry'))
    credential=accounts.SessionCredential('s'*43)
    assert security.resolve_principal(credential)==identity
    payload['identities'][0]['role']='viewer';write()
    assert security.resolve_principal(credential)['permissions']==['read']
    from pathlib import Path
    Path(payload['identities'][0]['token_file']).write_text('replacement-credential-'.ljust(48,'x'))
    with pytest.raises(PermissionError):accounts.verify_link(proof)


def test_removed_registry_account_invalidates_linked_oauth_session(registry,monkeypatch):
    payload,path,tokens,write=registry
    monkeypatch.setattr(accounts,'_lookup_hash',lambda _:dict(actor='local-user-alice',authority='registry'))
    payload['identities']=payload['identities'][1:];write()
    with pytest.raises(HTTPException) as error:accounts.resolve(accounts.SessionCredential('s'*43))
    assert error.value.status_code==401


def test_new_provider_identity_has_only_operator_permissions(monkeypatch):
    for setting in [*security.FILES.values(),'NSAI_LOCAL_IDENTITIES_FILE']:monkeypatch.delenv(setting,raising=False)
    monkeypatch.setattr(accounts,'_lookup_hash',lambda _:dict(actor='local-user-oauth-'+'a'*32,authority='provider'))
    identity=accounts.resolve(accounts.SessionCredential('s'*43))
    assert identity['role']=='operator' and 'admin' not in identity['permissions']
    assert identity['identity_kind']=='local-user'


@pytest.mark.parametrize('value',[None,'','a'*42,'a'*44,'x'*42+'!',123])
def test_bad_opaque_credentials_never_reach_database(value,monkeypatch):
    monkeypatch.setattr(store,'connect',lambda:pytest.fail('Invalid credential reached database'))
    with pytest.raises(HTTPException) as error:accounts.resolve(accounts.SessionCredential(value))
    assert error.value.status_code==401


def test_session_credential_never_reveals_secret_in_repr():
    credential=accounts.SessionCredential('s'*43)
    assert credential.token not in repr(credential)


def test_linking_mutations_cannot_upgrade_bound_request_context(monkeypatch):
    monkeypatch.setattr(store,'connect',lambda:pytest.fail('Request escalated to auth service'))
    with store.identity_context(dict(actor='local-user-alice',role='operator')):
        with pytest.raises(PermissionError):accounts.finish_login('google','subject','signup')
