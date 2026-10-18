import json
import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',
                             reason='explicit owned PostgreSQL qualification')


def test_audit_and_owner_sharing_use_compatible_lock_order(database):
    result=database.run_source_fixture('audit_lock_pg_fixture.py')
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout.strip().splitlines()[-1])['both_transactions_committed'] is True
