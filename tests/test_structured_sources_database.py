"""Packaged database custody for the new table evidence adapter."""
import json
import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',reason='explicit owned database qualification')


def test_structured_originals_manifest_and_private_publication(database):
    result=database.run_source_fixture('structured_sources_pg_fixture.py')
    assert result.returncode==0,result.stderr[-2500:]
    report=json.loads(result.stdout.strip().splitlines()[-1])
    assert report['status']=='PASS_SCOPED' and report['structured_manifest_preserved']
