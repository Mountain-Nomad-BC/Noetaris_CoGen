import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',reason='explicit owned PostgreSQL qualification')


def begin(database,key,actor,kind='generation',users=5,personal=1,global_limit=1,queue=10):
    return database(f"SELECT nsai_operation_begin(repeat('{key}',32),'{kind}',{users},{personal},{global_limit},{queue});",app=True,actor=actor)


def test_queue_is_fifo_bounded_and_principal_scoped(database):
    assert begin(database,'a','local-user-alice')=='active'
    assert begin(database,'b','local-user-bob',queue=1)=='queued'
    assert begin(database,'c','local-user-charlie',queue=1)=='queue-limit'
    assert begin(database,'d','local-user-alice')=='personal-limit'
    assert database("SELECT nsai_operation_claim(repeat('b',32),1);",app=True,actor='local-user-bob')=='queued'
    database("SELECT nsai_operation_finish(repeat('a',32));",app=True,actor='local-user-alice')
    assert database("SELECT nsai_operation_claim(repeat('b',32),1);",app=True,actor='local-user-bob')=='active'
    database('SELECT * FROM operation_admissions;',app=True,actor='local-user-bob',ok=False)


def test_cross_account_cannot_claim_or_release_and_user_bound_is_shared(database):
    assert begin(database,'a','local-user-alice',users=1)=='active'
    assert begin(database,'b','local-user-bob',users=1)=='user-limit'
    database("SELECT nsai_operation_claim(repeat('a',32),1);",app=True,actor='local-user-bob',ok=False)
    assert database("SELECT nsai_operation_finish(repeat('a',32));",app=True,actor='local-user-bob')=='f'
    assert database("SELECT state FROM operation_admissions WHERE id=repeat('a',32);")=='active'


def test_ingestion_is_independently_limited_and_finished_slots_reusable(database):
    assert begin(database,'a','local-user-alice',kind='ingestion',queue=0)=='active'
    assert begin(database,'b','local-user-alice',kind='ingestion',queue=0)=='personal-limit'
    assert begin(database,'c','local-user-bob',kind='ingestion',global_limit=2,queue=0)=='active'
    database("SELECT nsai_operation_finish(repeat('a',32));",app=True,actor='local-user-alice')
    assert begin(database,'d','local-user-alice',kind='ingestion',global_limit=2,queue=0)=='active'


def test_expired_worker_releases_capacity_without_reusing_old_identity(database):
    assert begin(database,'a','local-user-alice')=='active'
    database("UPDATE operation_admissions SET expires_at=clock_timestamp()-interval '1 second';")
    assert begin(database,'b','local-user-bob')=='active'
    assert database("SELECT nsai_operation_claim(repeat('a',32),1);",app=True,actor='local-user-alice')=='expired'
    assert database("SELECT state FROM operation_admissions WHERE id=repeat('a',32);")=='expired'
