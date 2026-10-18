"""Complete contributing-source enforcement for stored outputs and caches."""
import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',
                             reason='explicit owned PostgreSQL qualification')


def test_all_dependencies_required_and_revoked_for_every_derived_record(database):
    database("INSERT INTO documents(id,title,source_version,sha256,raw_text,owner_scope,ingested_by) "
             "VALUES('bob-private','Bob','1','bbb-private','Bob private canary','local-user-bob','local-user-bob');",
             actor='local-user-bob')
    database("INSERT INTO sessions(id,owner) VALUES('session','local-user-alice'); "
             "INSERT INTO claims(id,document_id,subject,predicate,value,locator) VALUES('claim','private','Motor','limit','85 C','page:1'); "
             "INSERT INTO session_messages(session_id,role,text,receipt,source_ids,provenance_complete) "
             "VALUES('session','assistant','Bob private canary','{}',ARRAY['private','bob-private'],true); "
             "INSERT INTO invocation_receipts(actor,request_id,payload_sha256,state,response,source_ids,provenance_complete) "
             "VALUES('local-user-alice',repeat('a',32),repeat('b',64),'completed','{\"answer\":\"Bob private canary\"}',ARRAY['private','bob-private'],true); "
             "INSERT INTO governed_records(id,kind,author,document_id,source_sha256,payload,source_ids,provenance_complete) "
             "VALUES(repeat('c',64),'proposal','local-user-alice','private',repeat('d',64),'{\"bridge\":\"Bob private canary\"}',ARRAY['private','bob-private'],true); "
             "INSERT INTO learning_proposals(id,author,source_claim_id,reflection,source_ids,provenance_complete) "
             "VALUES('learning','local-user-alice','claim','Bob private canary',ARRAY['private','bob-private'],true); "
             "INSERT INTO inference_runs(id,actor,state,details,source_ids,provenance_complete) "
             "VALUES('run','local-user-alice','completed','{\"private\":\"Bob private canary\"}',ARRAY['private','bob-private'],true); "
             "UPDATE claims SET status='verified',reviewed_by='local-user-reviewer',source_ids=ARRAY['private','bob-private'],provenance_complete=true; "
             "INSERT INTO audit_events(actor,event_type,details,previous_sha256,sha256,source_ids,provenance_complete) "
             "VALUES('local-user-alice','test','{\"private\":\"Bob private canary\"}',repeat('0',64),repeat('e',64),ARRAY['private','bob-private'],true); "
             "INSERT INTO document_knowledge(document_id,source_sha256,revision,knowledge,formulas,artifact_sha256,source_ids,provenance_complete) "
             "VALUES('private',repeat('a',64),'1','{\"bridge\":\"Bob private canary\"}','{}',repeat('b',64),ARRAY['private','bob-private'],true); "
             "INSERT INTO knowledge_embeddings(document_id,model_sha256,artifact_sha256,payload,source_ids,provenance_complete) "
             "VALUES('private',repeat('a',64),repeat('b',64),'{\"nearest\":\"Bob private canary\"}',ARRAY['private','bob-private'],true); "
             "INSERT INTO research_supplements(id,document_id,kind,source_sha256,review_record_id,payload,author,source_ids,provenance_complete) "
             "VALUES(repeat('f',64),'private','ocr',repeat('d',64),repeat('c',64),'{\"private\":\"Bob private canary\"}','local-user-alice',ARRAY['private','bob-private'],true); "
             "INSERT INTO governed_reviews(record_id,actor,decision,rationale) "
             "VALUES(repeat('c',64),'local-user-reviewer','reviewed','Independent fixture review');")
    tables=['session_messages','invocation_receipts','governed_records','governed_reviews','learning_proposals',
            'inference_runs','claims','audit_events','document_knowledge','knowledge_embeddings','research_supplements']
    def counts(actor):
        return [database(f'SELECT count(*) FROM {table};',app=True,actor=actor) for table in tables]
    assert counts('local-user-alice')==['0']*len(tables)
    database("SELECT nsai_private_share('bob-private','local-user-bob',1,'user','local-user-alice',NULL,false);",app=True,actor='local-user-bob')
    assert counts('local-user-alice')==['1']*len(tables)
    assert counts('local-user-bob')==['0']*len(tables)
    database("SELECT nsai_private_share('bob-private','local-user-bob',2,'user','local-user-alice',NULL,true);",app=True,actor='local-user-bob')
    assert counts('local-user-alice')==['0']*len(tables)
    assert [database(f'SELECT count(*) FROM {table};',app=True) for table in tables]==['0']*len(tables)


def test_unknown_provenance_and_unknown_source_fail_closed(database):
    database("INSERT INTO sessions(id,owner) VALUES('session','local-user-alice'); "
             "INSERT INTO session_messages(session_id,role,text,receipt) VALUES('session','assistant','Unknown legacy answer','{}'); "
             "INSERT INTO session_messages(session_id,role,text,receipt,source_ids,provenance_complete) "
             "VALUES('session','assistant','Missing-source answer','{}',ARRAY['unknown-source'],true);")
    assert database('SELECT count(*) FROM session_messages;',app=True,actor='local-user-alice')=='0'
    database("INSERT INTO session_messages(session_id,role,text,receipt,source_ids,provenance_complete) "
             "VALUES('session','assistant','Source-independent refusal','{}',ARRAY[]::text[],true);")
    assert database('SELECT count(*) FROM session_messages;',app=True,actor='local-user-alice')=='1'


def test_real_application_revokes_messages_memory_and_invocation_cache(database):
    import json
    result=database.run_source_fixture('private_derived_pg_fixture.py')
    assert result.returncode==0,result.stderr
    report=json.loads(result.stdout.strip().splitlines()[-1])
    assert report['status']=='PASS' and len(report['checks'])>=12
