import os
import json
from pathlib import Path
from nsai import api,store,security
from semantic_fixture_helpers import configure_authority

secret=Path('/tmp/owned-db-password');secret.write_text('x'*48)
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',NSAI_DB_PASSWORD_FILE=str(secret))
configure_authority();identity=security.resolve_principal('Bearer '+Path('/tmp/fixture-user-alice').read_text())
with store.identity_context(identity):
    try:api.ingest(api.DocumentInput(title='Quota boundary',version='1',text='Motor-X maximum operating temperature is 75 C.'),identity)
    except Exception as error:assert getattr(error,'status_code',None)==409 and 'capacity' in str(error.detail).lower()
    else:raise AssertionError('Private row filtering bypassed the global source limit')
print(json.dumps(dict(status='PASS_SCOPED',global_limit_enforced=True)))
