import asyncio
import os
import json
from pathlib import Path
from nsai import api,store,security,semantic_jobs as jobs
from semantic_fixture_helpers import configure_authority,synthetic_encode

secret=Path('/tmp/owned-db-password');secret.write_text('x'*48)
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',NSAI_DB_PASSWORD_FILE=str(secret))
configure_authority();identity=security.resolve_principal('Bearer '+Path('/tmp/fixture-user-alice').read_text())
text='Motor-X maximum operating temperature is 75 C.\n'+'\n'.join(
    f'Section {number}: '+('insulation durability temperature safety '*16) for number in range(12))
with store.identity_context(identity):
    source=api.ingest(api.DocumentInput(title='Semantic quota boundary',version='1',text=text),identity)
job=jobs.claim_next()
try:asyncio.run(jobs.process_job(job,encode=synthetic_encode))
except Exception as error:assert getattr(error,'sqlstate',None)=='54000',type(error).__name__
else:raise AssertionError('Private row filtering bypassed the global semantic payload limit')
jobs.fail_job(job,'capacity-exhausted')
with store.identity_context(identity):
    assert not jobs.source_status(source['document_id'])['ready']
print(json.dumps(dict(status='PASS_SCOPED',global_limit_enforced=True,no_partial_publication=True)))
