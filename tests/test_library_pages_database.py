import hashlib
import json
import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',
                             reason='explicit owned PostgreSQL qualification')


def test_real_library_paging_past_one_hundred_uses_current_authority(database):
    statements=[]
    for number in range(123):
        actor='local-user-alice' if number<120 else 'local-user-bob'
        digest=hashlib.sha256(str(number).encode()).hexdigest()
        statements.append(f"SET nsai.actor='{actor}'; SET nsai.role='operator'; "
            'INSERT INTO documents(id,title,source_version,sha256,raw_text,owner_scope,ingested_by,created_at) '
            f"VALUES('{number:032x}','Owned source {number:03d}','1','{digest}','fixture','{actor}','{actor}','2020-01-01T00:00:00Z');")
    database('\n'.join(statements))
    result=database.run_source_fixture('library_pages_pg_fixture.py')
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout.strip().splitlines()[-1])['authorized_sources']==120
