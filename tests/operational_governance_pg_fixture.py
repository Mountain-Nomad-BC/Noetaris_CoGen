"""Real application accounting with separate principals; no model call or cash spend."""
import json
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from nsai import store,workflow_store as workflows
from nsai import operation_admission as operations

secret=Path('/tmp/owned-db-password');secret.write_text('x'*48)
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',NSAI_DB_PASSWORD_FILE=str(secret))
alice=dict(actor='local-user-alice',role='operator',identity_kind='local-user',permissions=['chat'])
bob=dict(actor='local-user-bob',role='operator',identity_kind='local-user',permissions=['chat'])
expiring=dict(actor='local-user-expiring',role='operator',identity_kind='local-user',permissions=['chat'])


def denied(actor,message):
    try:workflows.reserve_inference(actor)
    except ValueError as error:assert message in str(error)
    else:raise AssertionError('Generation limit was bypassed')


with store.identity_context(alice):
    with store.connect() as conn:
        assert conn.execute('SELECT nsai_active_inference_count()').fetchone()[0]==0
    first,_=workflows.reserve_inference(alice['actor'])
    denied(alice['actor'],'Personal generation concurrency')
with store.identity_context(bob):
    denied(bob['actor'],'Global inference concurrency')
    try:workflows.finish_inference(first,bob['actor'],dict(fixture=True))
    except LookupError:pass
    else:raise AssertionError('Foreign actor completed an inference reservation')
def complete_concurrently(worker):
    with store.identity_context(alice):
        return workflows.finish_inference(first,alice['actor'],dict(fixture=True,worker=worker))
with ThreadPoolExecutor(max_workers=2) as pool:
    receipts=list(pool.map(complete_concurrently,['one','two']))
assert receipts[0]==receipts[1]
with store.identity_context(alice),store.connect() as conn:
    assert conn.execute("SELECT count(*) FROM audit_events WHERE actor=%s AND event_type='inference.completed' AND details->>'run_id'=%s",
        (alice['actor'],first)).fetchone()[0]==1
with store.identity_context(bob):
    second,_=workflows.reserve_inference(bob['actor'])
    workflows.finish_inference(second,bob['actor'],dict(fixture=True))
with store.identity_context(alice):
    for attempt in range(19):
        run,_=workflows.reserve_inference(alice['actor'])
        if attempt==0:
            workflows.finish_inference(run,alice['actor'],dict(fixture=True))
        else:
            workflows.finish_inference(run,alice['actor'],dict(fixture=True),failed=attempt==1)
    denied(alice['actor'],'Personal daily generation')
    workflows.retrieve('unmatched evidence query')
    with store.connect() as conn:
        assert conn.execute('SELECT count(*) FROM inference_runs WHERE actor=%s',(alice['actor'],)).fetchone()[0]==20
        assert conn.execute("SELECT count(*) FROM inference_runs WHERE actor=%s AND state='failed'",(alice['actor'],)).fetchone()[0]==1
with store.identity_context(expiring):
    expired='f'*32
    assert workflows.reconcile_inference(expiring['actor'])['reconciled']==1
    assert workflows.reconcile_inference(expiring['actor'])['reconciled']==0
    with store.connect() as conn:
        state,details=conn.execute('SELECT state,details FROM inference_runs WHERE id=%s',(expired,)).fetchone()
        assert state=='failed' and details['reason']=='lease-expired'
        assert conn.execute("SELECT count(*) FROM inference_runs WHERE actor=%s AND state='failed'",(expiring['actor'],)).fetchone()[0]==1
        assert conn.execute("SELECT count(*) FROM audit_events WHERE actor=%s AND event_type='inference.abandoned' AND details->>'run_id'=%s",
            (expiring['actor'],expired)).fetchone()[0]==1
with store.identity_context(bob):
    assert workflows.reserve_inference(bob['actor'])[0]
with store.identity_context(alice):
    with operations.admitted_sync('ingestion'):
        try:
            with operations.admitted_sync('ingestion'):raise AssertionError('Duplicate ingestion admitted')
        except operations.Busy:pass
    with store.connect() as conn:
        assert conn.execute("SELECT nsai_operation_begin(%s,'ingestion',5,1,5,0)",('f'*32,)).fetchone()[0]=='active'
        assert conn.execute('SELECT nsai_operation_finish(%s)',('f'*32,)).fetchone()[0]
async def queue_scenario():
    acquired=asyncio.Event()
    async def bob_operation():
        with store.identity_context(bob):
            async with operations.admitted('generation'):acquired.set()
    with store.identity_context(alice):
        async with operations.admitted('generation'):
            queued=asyncio.create_task(bob_operation())
            await asyncio.sleep(.3)
            assert not acquired.is_set()
        await asyncio.wait_for(queued,5)
        assert acquired.is_set()
asyncio.run(queue_scenario())
print(json.dumps(dict(status='PASS_SCOPED',personal_daily=20,personal_active=1,global_active=1,
    principals_isolated=True,retrieval_not_charged=True,model_contacted=False,
    durable_queue_waits_for_slot=True,ingestion_exclusion=True,concurrent_finish_single_event=True,
    foreign_finish_denied=True,failed_and_abandoned_attempts_charged=True,abandoned_reservation_reconciled=True)))
