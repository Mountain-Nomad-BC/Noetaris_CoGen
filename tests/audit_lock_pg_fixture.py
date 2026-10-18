"""Coordinate actual audit/share transactions; no fabricated authorization result."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
from threading import Event
from nsai import store,workflow_store as workflow

secret=Path('/tmp/owned-db-password');secret.write_text('x'*48)
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',NSAI_DB_PASSWORD_FILE=str(secret))
identity=dict(actor='local-user-alice',role='operator',identity_kind='local-user',permissions=['read'])
head=Event();policy=Event();ready=Event()


def append_audit():
    with store.identity_context(identity),store.connect() as conn:
        conn.execute("SET LOCAL statement_timeout='6s'")
        assert ready.wait(4)
        class Coordinated:
            def execute(self,query,*args):
                result=conn.execute(query,*args)
                if query=='SELECT pg_advisory_xact_lock(878701)':
                    head.set()
                    # Correct lock order keeps the competing writer blocked on
                    # source policy. It need not acquire that lock before commit.
                    policy.wait(.75)
                return result
        workflow.audit(Coordinated(),identity['actor'],'fixture.audit',dict(source_ids=['private']))


def change_sharing():
    with store.identity_context(identity),store.connect() as conn:
        conn.execute("SET LOCAL statement_timeout='6s'")
        ready.set()
        assert head.wait(4)
        conn.execute("SELECT nsai_current_source_share('private',1,'user','local-user-bob',NULL,false)")
        policy.set()
        workflow.audit(conn,identity['actor'],'fixture.share',dict(source_ids=['private']))


with ThreadPoolExecutor(max_workers=2) as pool:
    futures=[pool.submit(append_audit),pool.submit(change_sharing)]
    errors=[]
    for future in futures:
        try:future.result(timeout=10)
        except Exception as error:errors.append(type(error).__name__)
assert not errors,errors
assert policy.is_set()
print(json.dumps(dict(status='PASS_SCOPED',both_transactions_committed=True)))
