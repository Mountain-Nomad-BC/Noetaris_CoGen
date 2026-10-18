"""Real PostgreSQL reservations; no paid provider is contacted."""
import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',reason='explicit owned PostgreSQL qualification')


def reserve(database,key='a',amount=1000000,bucket='amd-credits',actor='local-user-alice'):
    database("UPDATE cost_accounts SET enabled=true,limit_units=10000000 WHERE name='amd-credits';")
    return database(f"SELECT nsai_reserve_cost(repeat('{key}',64),'{bucket}','provider-a',{amount},100,200);",app=True,actor=actor)


def test_cash_reservation_idempotency_and_no_cross_actor_replay(database):
    assert reserve(database)=='a'*64
    assert reserve(database)=='a'*64
    assert database("SELECT reserved_units FROM cost_accounts WHERE name='amd-credits';")=='1000000'
    database("SELECT nsai_reserve_cost(repeat('a',64),'amd-credits','provider-a',2,100,200);",app=True,actor='local-user-alice',ok=False)
    database("SELECT nsai_reserve_cost(repeat('a',64),'amd-credits','provider-a',1000000,100,200);",app=True,actor='local-user-bob',ok=False)
    for table in ['cost_accounts','cost_reservations','cost_events']:
        database('SELECT * FROM '+table,app=True,actor='local-user-alice',ok=False)


def test_cash_accounts_cannot_be_used_even_if_owner_reenables_them(database):
    database("UPDATE cost_accounts SET enabled=true WHERE name LIKE 'cash-%';")
    for bucket in ['cash-api','cash-cloud','cash-contingency','cash-total']:
        database(f"SELECT nsai_reserve_cost(repeat('e',64),'{bucket}','provider-a',0,0,0);",app=True,actor='local-user-alice',ok=False)
    assert database("SELECT reserved_units FROM cost_accounts WHERE name='cash-total';")=='0'
    assert database("SELECT reserved_units FROM cost_accounts WHERE name='evolus-credits';")=='0'


def test_settlement_is_exact_idempotent_and_overrun_remains_recorded(database):
    reserve(database,amount=1000000)
    query="SELECT nsai_settle_cost(repeat('a',64),1200000,110,220);"
    database(query,app=True,actor='local-user-alice')
    database(query,app=True,actor='local-user-alice')
    assert database("SELECT spent_units||':'||reserved_units||':'||enabled FROM cost_accounts WHERE name='amd-credits';")=='1200000:0:false'
    assert database("SELECT spent_units FROM cost_accounts WHERE name='cash-total';")=='0'
    database("SELECT nsai_settle_cost(repeat('a',64),0,0,0);",app=True,actor='local-user-alice',ok=False)
    assert database("SELECT count(*) FROM cost_events WHERE kind='settled';")=='1'


def test_rollback_and_unknown_outcomes_do_not_release_exposure(database):
    database("BEGIN; SELECT nsai_reserve_cost(repeat('a',64),'amd-credits','provider-a',1000000,0,0); SELECT 1/0; COMMIT;",app=True,actor='local-user-alice',ok=False)
    assert database('SELECT count(*) FROM cost_reservations;')=='0'
    reserve(database)
    # There is deliberately no automatic TTL refund for an uncertain request.
    database("UPDATE cost_reservations SET created_at=now()-interval '30 days';")
    assert database("SELECT reserved_units FROM cost_accounts WHERE name='amd-credits';")=='1000000'
    database("SELECT nsai_settle_cost(repeat('a',64),0,0,0);",app=True,actor='local-user-bob',ok=False)


def test_concurrent_workers_cannot_overspend_remaining_allocation(database):
    database("UPDATE cost_accounts SET enabled=true,limit_units=10000000 WHERE name='amd-credits';")
    from concurrent.futures import ThreadPoolExecutor
    def attempt(key):
        return database(f"SELECT nsai_reserve_cost(repeat('{key}',64),'amd-credits','provider-a',9000000,0,0);",app=True,actor='local-user-alice',ok=None).returncode
    with ThreadPoolExecutor(max_workers=2) as pool:outcomes=list(pool.map(attempt,['a','b']))
    assert sorted(outcomes)==[0,3]
    assert database("SELECT reserved_units FROM cost_accounts WHERE name='amd-credits';")=='9000000'


def test_zero_value_and_readonly_roles_do_not_bypass_shutdown(database):
    database("UPDATE cost_accounts SET enabled=false WHERE name='amd-credits';")
    database("SELECT nsai_reserve_cost(repeat('a',64),'amd-credits','provider-a',0,0,0);",app=True,actor='local-user-alice',ok=False)
    for role in ['viewer','reviewer','admin']:
        database("SELECT nsai_reserve_cost(repeat('a',64),'amd-credits','provider-a',1,0,0);",app=True,actor='local-user-alice',role=role,ok=False)
    database('SELECT last_value FROM cost_events_id_seq;',app=True,actor='local-user-alice',ok=False)


def test_cost_status_is_admin_only_and_alerts_include_reserved_exposure(database):
    import json
    reserve(database,amount=9000000)
    database('SELECT nsai_cost_status();',app=True,actor='local-user-alice',ok=False)
    result=json.loads(database('SELECT nsai_cost_status();',app=True,actor='local-user-admin',role='admin'))
    accounts={row['name']:row for row in result['accounts']}
    assert accounts['amd-credits']['alert']=='90-percent'
    assert accounts['amd-credits']['spent']==0 and accounts['amd-credits']['reserved']==9000000
    assert accounts['cash-api']['enabled'] is False
    assert result['provider_billing_cap_guaranteed'] is False
