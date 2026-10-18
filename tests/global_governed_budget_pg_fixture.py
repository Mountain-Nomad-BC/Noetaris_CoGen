"""A private owner's governed capacity cannot ignore another owner's records."""
import json
import os
from pathlib import Path
from nsai import api,store,security,governed_store
from semantic_fixture_helpers import configure_authority,publish_pending

password=Path('/tmp/owned-db-password');password.write_text('x'*48)
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',NSAI_DB_PASSWORD_FILE=str(password))
configure_authority()
alice=security.resolve_principal('Bearer '+Path('/tmp/fixture-user-alice').read_text())
with store.identity_context(alice):
    source=api.ingest(api.DocumentInput(title='Alice quota fixture',version='1',text='Motor-A maximum operating temperature is 75 C.'),alice)['document_id']
publish_pending()
with store.identity_context(alice):
    with store.connect() as conn:
        assert conn.execute('SELECT count(*) FROM governed_records').fetchone()[0]==0
    blocked=False
    try:
        governed_store.persist('assembly',alice['actor'],source,dict(note='x'*32768,source_ids=[source]))
    except Exception as error:
        if getattr(error,'sqlstate',None)!='54000':raise
        blocked=True
    assert blocked,'Hidden other-owner governed records bypassed the global capacity'
print(json.dumps(dict(status='PASS_SCOPED',other_owner_capacity_enforced=True)))
