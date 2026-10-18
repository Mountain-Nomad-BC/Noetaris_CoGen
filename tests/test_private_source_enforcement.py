"""Real PostgreSQL source-policy enforcement, beyond pure policy decisions."""
import os
import json
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',
                             reason='explicit owned PostgreSQL qualification')


def test_every_source_table_filters_before_projection(database):
    for document in ['private','legacy']:
        database(f"INSERT INTO source_spans VALUES('{document}','page:1','Private canary'); "
                 f"INSERT INTO chunks(id,document_id,locator,text,sha256) VALUES('{document}','{document}','page:1','Private canary',repeat('a',64)); "
                 f"INSERT INTO claims(id,document_id,subject,predicate,value,locator) VALUES('{document}','{document}','Motor','limit','85 C','page:1'); "
                 f"INSERT INTO claim_events(claim_id,event_type,actor) VALUES('{document}','test','test'); "
                 f"INSERT INTO document_knowledge(document_id,source_sha256,revision,knowledge,formulas,artifact_sha256,source_ids,provenance_complete) VALUES('{document}',repeat('a',64),'1','{{}}','{{}}',repeat('a',64),ARRAY['{document}'],true); "
                 f"INSERT INTO knowledge_embeddings(document_id,model_sha256,artifact_sha256,payload,source_ids,provenance_complete) VALUES('{document}',repeat('b',64),repeat('c',64),'{{}}',ARRAY['{document}'],true);")
    for table in ['documents','source_spans','chunks','claims','claim_events',
                  'document_knowledge','knowledge_embeddings']:
        assert database(f'SELECT count(*) FROM {table};',app=True)=='1'
        assert database(f'SELECT count(*) FROM {table};',app=True,actor='local-user-alice')=='1'
        assert database(f'SELECT count(*) FROM {table};',app=True,actor='local-user-bob')=='0'


def test_same_bytes_are_separate_private_logical_sources(database):
    database("INSERT INTO documents(id,title,source_version,sha256,raw_text,owner_scope,ingested_by) "
             "VALUES('bob-copy','Copy','1','aaa','secret','local-user-bob','local-user-bob');",
             app=True,actor='local-user-bob')
    assert database("SELECT id FROM documents;",app=True,actor='local-user-bob')=='bob-copy'
    assert database("SELECT id FROM documents;",app=True,actor='local-user-alice')=='private'
    assert database("SELECT count(*) FROM document_owners;")=='2'
    database("INSERT INTO documents(id,title,source_version,sha256,raw_text,owner_scope,ingested_by) "
             "VALUES('alice-duplicate','Duplicate','1','aaa','secret','local-user-alice','local-user-alice');",
             app=True,actor='local-user-alice',ok=False)
    assert database("SELECT count(*) FROM document_owners;")=='2'


def test_prior_application_conflict_target_survives_private_copies(database):
    # The old writer uses the physical hash and the original global target.
    database("INSERT INTO documents(id,title,source_version,sha256,raw_text) "
             "VALUES('legacy-copy','Copy','1','aaa','legacy') "
             "ON CONFLICT(sha256,source_version) DO NOTHING;",app=True)
    database("INSERT INTO documents(id,title,source_version,sha256,raw_text) "
             "VALUES('legacy-duplicate','Copy','1','aaa','legacy') "
             "ON CONFLICT(sha256,source_version) DO NOTHING;",app=True)
    assert database("SELECT id FROM documents WHERE sha256='aaa';",app=True)=='legacy-copy'
    assert database("SELECT original_sha256 FROM documents WHERE id='private';",
                    app=True,actor='local-user-alice')=='aaa'
    database("INSERT INTO documents(id,title,source_version,sha256,raw_text) "
             "VALUES('collision','Copy','1','private/1/local-user-alice/aaa','legacy');",
             app=True,ok=False)


def test_private_actor_cannot_create_shared_or_another_users_source(database):
    for scope, submitter in [('legacy-shared','local-user-alice'),
                             ('local-user-bob','local-user-alice'),
                             ('local-user-alice','local-user-bob')]:
        database("INSERT INTO documents(id,title,source_version,sha256,raw_text,owner_scope,ingested_by) "
                 f"VALUES('bad','Bad','1','bad','x','{scope}','{submitter}');",
                 app=True,actor='local-user-alice',ok=False)
    assert database("SELECT count(*) FROM documents WHERE id='bad';")=='0'
    assert database("SELECT count(*) FROM private_access_events WHERE document_id='bad';")=='0'


def test_row_filter_requires_admin_grant_and_audits_once_per_transaction(database):
    assert database('SELECT count(*) FROM documents;',app=True,actor='local-user-admin',role='admin')=='0'
    database("SELECT nsai_private_share('private','local-user-alice',1,'user','local-user-admin',NULL,false);",app=True)
    assert database("BEGIN; SELECT id FROM documents; SELECT raw_text FROM documents; COMMIT;",
                    app=True,actor='local-user-admin',role='admin').splitlines()==['private','secret']
    assert database("SELECT count(*) FROM private_access_events WHERE event_type='privileged-read';")=='1'
    database("CREATE FUNCTION fail_row_audit() RETURNS trigger LANGUAGE plpgsql AS $$ "
             "BEGIN RAISE EXCEPTION 'Owned audit outage'; END $$; "
             "CREATE TRIGGER fail_row_audit BEFORE INSERT ON private_access_events FOR EACH ROW EXECUTE FUNCTION fail_row_audit();")
    database('SELECT raw_text FROM documents;',app=True,actor='local-user-admin',role='admin',ok=False)
    assert database("SELECT count(*) FROM private_access_events WHERE event_type='privileged-read';")=='1'


def test_connection_local_context_does_not_survive_commit_or_rollback(database):
    assert database("BEGIN; SET LOCAL nsai.actor='local-user-alice'; SET LOCAL nsai.role='operator'; "
                    "SELECT id FROM documents; COMMIT; SELECT id FROM documents; "
                    "BEGIN; SET LOCAL nsai.actor='local-user-bob'; SET LOCAL nsai.role='operator'; "
                    "SELECT count(*) FROM documents; ROLLBACK; SELECT id FROM documents;",
                    app=True).splitlines()==['private','legacy','0','legacy']


def test_real_application_ingestion_and_pool_identity_isolation(database):
    result=database.run_source_fixture()
    assert result.returncode==0, result.stderr
    report=json.loads(result.stdout.strip().splitlines()[-1])
    assert report['status']=='PASS' and len(report['checks'])>=15
    assert len(set(report['documents']))==2
    assert database("SELECT count(*) FROM private_access_events WHERE event_type='privileged-read';")=='1'
