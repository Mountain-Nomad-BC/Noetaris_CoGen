"""Ledger appends must serialize against the global, not RLS-visible, head."""
import hashlib
import json
import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',
                             reason='explicit owned PostgreSQL qualification')


def test_legacy_writer_cannot_append_after_an_invisible_private_head(database):
    def append(actor, previous, *, private=False, ok=True):
        body=dict(actor=actor,event_type='fixture',details={},previous_sha256=previous)
        digest=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        return database("INSERT INTO audit_events(actor,event_type,details,previous_sha256,sha256,source_ids,provenance_complete) "
            f"VALUES('{actor}','fixture','{{}}','{previous}','{digest}',ARRAY[]::text[],true);",
            app=True,actor=actor if private else None,ok=ok)
    append('local-operator','0'*64)
    legacy_head=database('SELECT sha256 FROM audit_events ORDER BY id DESC LIMIT 1;',app=True)
    append('local-user-alice',legacy_head,private=True)
    global_head=database('SELECT nsai_audit_head();',app=True)
    assert global_head!=legacy_head
    assert database('SELECT sha256 FROM audit_events ORDER BY id DESC LIMIT 1;',app=True)==legacy_head
    # This is the old writer's RLS-visible head; accepting it forks the chain.
    append('local-reviewer',legacy_head,ok=False)
    assert database('SELECT count(*) FROM audit_events;')=='2'
    append('local-reviewer',global_head)
    assert database('SELECT count(*) FROM audit_events;')=='3'


def test_preallocated_out_of_order_identity_cannot_reorder_ledger(database):
    reserved=database("SELECT nextval(pg_get_serial_sequence('audit_events','id'));")
    database("INSERT INTO audit_events(actor,event_type,details,previous_sha256,sha256) "
             "VALUES('local-operator','fixture','{}',repeat('0',64),repeat('a',64));",app=True)
    rejected=database("INSERT INTO audit_events(id,actor,event_type,details,previous_sha256,sha256) "
        f"OVERRIDING SYSTEM VALUE VALUES({reserved},'local-operator','fixture','{{}}',repeat('a',64),repeat('b',64));",app=True,ok=None)
    assert rejected.returncode!=0 and 'Stale audit head' in rejected.stderr
    assert database('SELECT count(*) FROM audit_events;')=='1'
