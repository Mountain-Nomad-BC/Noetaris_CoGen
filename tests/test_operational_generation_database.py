import json
import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',reason='explicit owned PostgreSQL qualification')


def test_real_application_daily_and_cross_worker_global_admission(database):
    database("INSERT INTO inference_runs(id,actor,state,created_at) "
        "VALUES(repeat('f',32),'local-user-expiring','reserved',now()-interval '301 seconds');")
    result=database.run_source_fixture('operational_governance_pg_fixture.py')
    assert result.returncode==0,result.stderr
    receipt=json.loads(result.stdout.strip().splitlines()[-1])
    assert receipt['status']=='PASS_SCOPED'
    assert receipt['concurrent_finish_single_event']
    assert receipt['foreign_finish_denied']
    assert receipt['failed_and_abandoned_attempts_charged']
    assert receipt['abandoned_reservation_reconciled']
