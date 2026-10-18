"""Historical audit authorization; legacy metadata fixtures, not source-quality evidence."""
import json,os
import pytest
from nsai.contracts.evidence import canonical_hash
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',reason='explicit owned PostgreSQL qualification')

def historical(database,*,case='valid',event='governed.reviewed'):
 owner='local-user-alice';admin='local-user-admin';record='e'*64
 database("INSERT INTO documents(id,title,source_version,sha256,raw_text,owner_scope,ingested_by) VALUES('audit-alternate','Legacy alternate','1','ddd','Private alternate context','local-user-alice','local-user-alice');",app=True,actor=owner)
 for source in ['private','audit-alternate']:
  database("SELECT nsai_current_source_share('"+source+"',1,'user','local-user-admin',NULL,false);",app=True,actor=owner)
 # A quarantined legacy row is seeded once by the owned restore role; no
 # immutable row or trigger is modified to construct this negative fixture.
 complete='false' if case=='incomplete-parent' else 'true'
 database("INSERT INTO governed_records(id,kind,author,document_id,source_sha256,payload,source_ids,provenance_complete) VALUES(repeat('e',64),'proposal','local-user-alice','private',repeat('d',64),'{\"note\":\"Retained two-source candidate\"}',ARRAY['private','audit-alternate'],"+complete+");",app=case!='incomplete-parent',actor=owner)
 if case=='unknown-kind':event='governed.unknown-operation'
 details=dict(record_id='f'*64 if case=='missing-record' else record,document_id='wrong-origin' if case=='wrong-origin' else 'private',decision='reviewed',rationale='Retained historical private rationale.')
 previous=database('SELECT nsai_audit_head();') or None
 sha=canonical_hash(dict(actor=admin,event_type=event,details=details,previous_sha256=previous))
 def literal(value):return 'NULL' if value is None else "'"+value.replace("'","''")+"'"
 # Deliberately reproduce the old writer: only the origin is declared, while
 # the exact retained referent has complete two-source dependencies.
 database('INSERT INTO audit_events(actor,event_type,details,previous_sha256,sha256,source_ids,provenance_complete) VALUES('+','.join([literal(admin),literal(event),literal(json.dumps(details))+'::jsonb',literal(previous),literal(sha),"ARRAY['private']",'true'])+');',app=True,actor=admin,role='admin')
 row=database("SELECT row_to_json(a)::text FROM audit_events a WHERE sha256='"+sha+"';")
 return sha,row

def visible(database,sha):
 return database("SELECT count(*) FROM audit_events WHERE sha256='"+sha+"';",app=True,actor='local-user-admin',role='admin')

def test_historical_audit_follows_exact_parent_revocation_without_rewriting(database):
 sha,row=historical(database)
 assert visible(database,sha)=='1'
 database("SELECT nsai_current_source_share('audit-alternate',2,'user','local-user-admin',NULL,true);",app=True,actor='local-user-alice')
 assert database("SELECT count(*) FROM documents WHERE id='private';",app=True,actor='local-user-admin',role='admin')=='1'
 assert database("SELECT count(*) FROM governed_records WHERE id=repeat('e',64);",app=True,actor='local-user-admin',role='admin')=='0'
 assert visible(database,sha)=='0','Historical rationale remains visible after alternate-source revocation'
 database("SELECT nsai_current_source_share('audit-alternate',3,'user','local-user-admin',NULL,false);",app=True,actor='local-user-alice')
 assert visible(database,sha)=='1'
 assert database("SELECT row_to_json(a)::text FROM audit_events a WHERE sha256='"+sha+"';")==row

@pytest.mark.parametrize('case',['missing-record','wrong-origin','incomplete-parent','unknown-kind'])
def test_unclassifiable_governed_audit_is_retained_but_withheld(database,case):
 sha,row=historical(database,case=case)
 assert visible(database,sha)=='0'
 assert database("SELECT row_to_json(a)::text FROM audit_events a WHERE sha256='"+sha+"';")==row

def test_unrelated_origin_bound_audit_keeps_existing_visibility(database):
 sha,_=historical(database,event='source.inspected')
 database("SELECT nsai_current_source_share('audit-alternate',2,'user','local-user-admin',NULL,true);",app=True,actor='local-user-alice')
 assert visible(database,sha)=='1'
