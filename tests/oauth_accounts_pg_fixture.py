"""Real typed account/session operations, audit rollback and identity hot reload."""
import json
import os
from pathlib import Path
from fastapi import HTTPException
from nsai import oauth_accounts as accounts,security,store,workflow_store as workflows

secret=Path('/tmp/owned-db-password');secret.write_text('x'*48)
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',NSAI_DB_PASSWORD_FILE=str(secret))
for setting in [*security.FILES.values(),'NSAI_LOCAL_IDENTITIES_FILE']:os.environ.pop(setting,None)

first=accounts.finish_login('google','fixture-provider-alice','signup')
again=accounts.finish_login('google','fixture-provider-alice','login')
assert first['identity']==again['identity'] and first['token']!=again['token']
credential=accounts.SessionCredential(again['token'])
assert accounts.csrf_matches(credential,again['csrf'])
assert not accounts.csrf_matches(credential,'w'*43)
with store.identity_context(again['identity']):
    assert accounts.resolve(credential)==again['identity']
with store.identity_context(dict(actor='local-user-bob',role='operator')):
    try:accounts.resolve(credential)
    except HTTPException as error:assert error.status_code==401
    else:raise AssertionError('Cross-account session lookup succeeded')
linked=accounts.finish_login('github','12345','link',proof=accounts.link_proof(again['identity'],credential=credential))
assert linked['identity']==again['identity']
assert accounts.revoke(accounts.SessionCredential(first['token']))
try:accounts.resolve(accounts.SessionCredential(first['token']))
except HTTPException as error:assert error.status_code==401
else:raise AssertionError('Revoked login survived')
assert accounts.resolve(credential)==again['identity']

# Preserve the exact existing individual actor and its externally managed roles.
local_token=Path('/tmp/oauth-local-token');local_token.write_text('r'*48)
registry=Path('/tmp/oauth-local-identities.json')
payload=dict(schema_version='nsai.local-identities/1',identities=[
    dict(actor='local-user-alice',role='viewer',token_file=str(local_token))])
registry.write_text(json.dumps(payload));os.environ['NSAI_LOCAL_IDENTITIES_FILE']=str(registry)
local=security.resolve_principal('Bearer '+'r'*48)
linked_local=accounts.finish_login('google','fixture-local-alice','link',proof=accounts.link_proof(local))
assert linked_local['identity']['actor']=='local-user-alice'
assert linked_local['identity']['permissions']==['read']
local_credential=accounts.SessionCredential(linked_local['token'])
payload['identities'][0]['role']='operator';registry.write_text(json.dumps(payload))
assert accounts.resolve(local_credential)['role']=='operator'
with store.identity_context(accounts.resolve(local_credential)):
    with store.connect() as conn:
        assert conn.execute("SELECT owner_scope FROM documents WHERE id='private'").fetchone()[0]=='local-user-alice'

# A canonical audit failure must roll back binding and login together.
original_audit=workflows.audit;original_token=accounts.secrets.token_urlsafe
def failed_audit(*args,**kwargs):raise RuntimeError('Owned audit outage')
workflows.audit=failed_audit;accounts.secrets.token_urlsafe=lambda _: 'f'*43
try:
    try:accounts.finish_login('google','fixture-rollback','signup')
    except RuntimeError:pass
    else:raise AssertionError('Audit failure was ignored')
finally:
    workflows.audit=original_audit;accounts.secrets.token_urlsafe=original_token
assert accounts._lookup_hash(accounts.token_hash('f'*43)) is None
try:accounts.finish_login('google','fixture-rollback','login')
except Exception as error:assert getattr(error,'sqlstate',None)=='28000'
else:raise AssertionError('Failed signup left a bound account')
audit=workflows.audit_report()
assert audit['valid'] is True and audit['count']>=5
print(json.dumps(dict(status='PASS_SCOPED',new_accounts_are_ordinary=True,
    local_actor_and_owner_preserved=True,registry_roles_refreshed=True,
    explicit_linking=True,cross_account_denied=True,revocation=True,
    csrf_hash_verified=True,audit_chain_valid=True,audit_failure_rolls_back=True)))
