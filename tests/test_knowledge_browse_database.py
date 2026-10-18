import json
import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',
                             reason='explicit owned PostgreSQL qualification')


def test_private_knowledge_navigation_and_formula_lineage_reauthorize_each_read(database):
    result=database.run_source_fixture('knowledge_browse_pg_fixture.py')
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout.strip().splitlines()[-1])['owner_shared_reader_revocation'] is True
