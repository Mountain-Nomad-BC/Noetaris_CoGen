"""An unsafe role/schema must fail before the application receives a connection."""
import json
import os
from pathlib import Path
from nsai import store

password=Path('/tmp/owned-db-password');password.write_text('x'*48)
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',
                  NSAI_DB_PASSWORD_FILE=str(password))
entered=False
identity=dict(actor='local-user-bob',role='operator',identity_kind='local-user',permissions=['read'])
with store.identity_context(identity):
    try:
        with store.connect() as conn:
            entered=True
            conn.execute('SELECT raw_text FROM documents')
    except RuntimeError as error:
        assert not entered
        rejection_reason=str(error)
    else:raise AssertionError('Unsafe database contract reached content access')
print(json.dumps(dict(status='PASS',content_connection_yielded=entered,rejection_reason=rejection_reason)))
