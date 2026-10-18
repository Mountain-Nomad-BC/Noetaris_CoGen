"""Real SQL queue/lease/publication contracts; fixture vectors are not model evaluation."""
import hashlib
import json
import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',
                             reason='explicit owned PostgreSQL qualification')
MODEL='a'*64
KNOWLEDGE='b'*64
EMBEDDING='c'*64


def prepare(database,name='job-source',actor='local-user-alice'):
    digest=hashlib.sha256(('Owned fixture source '+name).encode()).hexdigest()
    job_id=hashlib.sha256((name+MODEL).encode()).hexdigest()
    database("INSERT INTO documents(id,title,source_version,sha256,raw_text,original_sha256,owner_scope,ingested_by) "
             f"VALUES('{name}','Owned job','1','{digest}','Owned fixture source','{digest}','{actor}','{actor}'); "
             "INSERT INTO document_knowledge(document_id,source_sha256,revision,knowledge,formulas,artifact_sha256,source_ids,provenance_complete) "
             f"VALUES('{name}','{digest}','1','{{}}','{{}}','{KNOWLEDGE}',ARRAY['{name}'],true);",actor=actor)
    result=database(f"SELECT nsai_enqueue_semantic_job('{job_id}','{name}','{MODEL}','{KNOWLEDGE}');",app=True,actor=actor)
    assert result==job_id
    return job_id,digest


def claim(database,seconds=300):
    raw=database(f"SELECT nsai_claim_semantic_job('{MODEL}',ARRAY['local-user-alice','local-user-bob'],2,{seconds});",app=True)
    return json.loads(raw) if raw else None


def test_enqueue_idempotent_bounded_claims_and_actor_fairness(database):
    first,_=prepare(database,'alice-one')
    assert database(f"SELECT nsai_enqueue_semantic_job(repeat('f',64),'alice-one','{MODEL}','{KNOWLEDGE}');",app=True,actor='local-user-alice')==first
    prepare(database,'alice-two')
    prepare(database,'bob-one','local-user-bob')
    database(f"SELECT nsai_claim_semantic_job('{MODEL}',ARRAY['local-user-alice'],2,30);",app=True,actor='local-user-alice',ok=False)
    one,two=claim(database),claim(database)
    assert {one['actor'],two['actor']}=={'local-user-alice','local-user-bob'}
    assert one['id']!=two['id'] and claim(database) is None
    assert database('SELECT count(*) FROM semantic_jobs;')=='3'
    for table in ['semantic_jobs','source_index_state','semantic_publications','semantic_job_events']:
        database(f'SELECT * FROM {table};',app=True,ok=False)
    database('SELECT last_value FROM semantic_job_events_id_seq;',app=True,ok=False)


def test_expired_lease_takeover_blocks_old_worker_and_attempts_are_bounded(database):
    job_id,_=prepare(database)
    old=claim(database,30)
    database(f"UPDATE semantic_jobs SET lease_expires_at=clock_timestamp()-interval '1 second' WHERE id='{job_id}';")
    new=claim(database,30)
    assert new['lease_token']!=old['lease_token'] and new['attempt']==2
    assert database("SELECT count(*) FROM documents;",app=True,actor='local-user-alice',job=old)=='0'
    assert database("SELECT id FROM documents;",app=True,actor='local-user-alice',job=new)=='job-source'
    database(f"SELECT nsai_publish_semantic_job('{job_id}','{old['lease_token']}','{EMBEDDING}',ARRAY['local-user-alice']);",
             app=True,actor='local-user-alice',job=old,ok=False)
    database(f"UPDATE semantic_jobs SET lease_expires_at=clock_timestamp()-interval '1 second' WHERE id='{job_id}';")
    final=claim(database,30)
    assert final['attempt']==3
    database(f"UPDATE semantic_jobs SET lease_expires_at=clock_timestamp()-interval '1 second' WHERE id='{job_id}';")
    assert claim(database) is None
    assert database(f"SELECT state||':'||attempts FROM semantic_jobs WHERE id='{job_id}';")=='failed:3'


def test_embeddings_publication_and_job_success_commit_or_roll_back_together(database):
    job_id,digest=prepare(database)
    job=claim(database)
    payload=json.dumps(dict(source_sha256=digest,knowledge_sha256=KNOWLEDGE,model_identity=dict(sha256=MODEL)))
    publish=("INSERT INTO knowledge_embeddings(document_id,model_sha256,artifact_sha256,payload,source_ids,provenance_complete) "
             f"VALUES('job-source','{MODEL}','{EMBEDDING}','{payload}',ARRAY['job-source'],true); "
             f"SELECT nsai_publish_semantic_job('{job_id}','{job['lease_token']}','{EMBEDDING}',ARRAY['local-user-alice']);")
    database('BEGIN; '+publish+' SELECT 1/0; COMMIT;',app=True,actor='local-user-alice',job=job,ok=False)
    assert database('SELECT count(*) FROM knowledge_embeddings;')=='0'
    assert database('SELECT count(*) FROM semantic_publications;')=='0'
    assert database(f"SELECT state FROM semantic_jobs WHERE id='{job_id}';")=='running'
    database('BEGIN; '+publish+' COMMIT;',app=True,actor='local-user-alice',job=job)
    assert database('SELECT count(*) FROM knowledge_embeddings;')=='1'
    assert database('SELECT count(*) FROM semantic_publications;')=='1'
    assert database(f"SELECT state FROM semantic_jobs WHERE id='{job_id}';")=='succeeded'
    assert database("SELECT current_publication_id FROM source_index_state WHERE document_id='job-source';")==job_id
    database(f"SELECT nsai_publish_semantic_job('{job_id}','{job['lease_token']}','{EMBEDDING}',ARRAY['local-user-alice']);",
             app=True,actor='local-user-alice',job=job,ok=False)


def test_policy_change_or_inactive_identity_prevents_claim_and_publication(database):
    job_id,_=prepare(database)
    assert database(f"SELECT nsai_claim_semantic_job('{MODEL}',ARRAY[]::text[],2,30);",app=True)==''
    job=claim(database)
    database("SELECT nsai_current_source_share('job-source',1,'user','local-user-bob',NULL,false);",app=True,actor='local-user-alice')
    assert database('SELECT count(*) FROM document_knowledge;',app=True,actor='local-user-alice',job=job)=='0'
    database(f"SELECT nsai_publish_semantic_job('{job_id}','{job['lease_token']}','{EMBEDDING}',ARRAY['local-user-alice']);",
             app=True,actor='local-user-alice',job=job,ok=False)
    assert database('SELECT count(*) FROM semantic_publications;')=='0'
