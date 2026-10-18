"""Actual dump/restore into a fresh logical database in an owned PG container.

This is not host-disaster recovery, concurrent-backup or RTO/RPO acceptance.
"""
import json
import os
import pytest
from pathlib import Path
from uuid import uuid4
from test_private_access_database import database
from nsai.schema_contract import ACCESS_DEFINITIONS_SQL
from nsai.semantic_encoder import PINNED_MODEL_SHA256 as MODEL

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',
                             reason='explicit owned PostgreSQL qualification')


def test_restore_preserves_private_policy_native_index_and_pending_checkpoint(database):
    vector=[1.0]+[0.0]*383
    graph=json.dumps(dict(nodes=[dict(id='a'*64,kind='passage',locator='page:1',page=1,text='Recovery source')]))
    payload=json.dumps(dict(vectors={'a'*64:vector}))
    database("SET nsai.actor='local-user-alice'; SET nsai.role='operator'; "
        "INSERT INTO documents(id,title,source_version,sha256,original_sha256,raw_text,owner_scope,ingested_by) "
        "VALUES('recovery','Recovery','1',repeat('e',64),repeat('e',64),'Recovery source','local-user-alice','local-user-alice'); "
        f"INSERT INTO document_knowledge(document_id,source_sha256,revision,knowledge,formulas,artifact_sha256,source_ids,provenance_complete) VALUES('recovery',repeat('e',64),'1','{graph}','{{}}',repeat('b',64),ARRAY['recovery'],true); "
        f"INSERT INTO knowledge_embeddings(document_id,model_sha256,artifact_sha256,payload,source_ids,provenance_complete) VALUES('recovery','{MODEL}',repeat('c',64),'{payload}',ARRAY['recovery'],true); "
        f"INSERT INTO semantic_jobs(id,document_id,requested_actor,source_revision,source_sha256,knowledge_sha256,model_sha256,state) VALUES(repeat('d',64),'recovery','local-user-alice','1',repeat('e',64),repeat('b',64),'{MODEL}','queued'); "
        f"INSERT INTO semantic_job_vectors(job_id,node_id,vector,coverage,artifact_sha256) VALUES(repeat('d',64),repeat('a',64),'{json.dumps(vector)}','{{}}',repeat('f',64));")
    database("SELECT nsai_private_share('recovery','local-user-alice',1,'user','local-user-bob',NULL,false);",app=True)
    database("SELECT nsai_private_share('recovery','local-user-alice',2,'user','local-user-carol',NULL,false);",app=True)
    database("SELECT nsai_private_share('recovery','local-user-alice',3,'user','local-user-carol',NULL,true);",app=True)
    tables=['document_owners','document_policy_versions','document_read_grants','private_access_events',
            'semantic_jobs','semantic_job_vectors','source_index_state','knowledge_embeddings',
            'native_semantic_passages','semantic_storage_usage','nsai_schema_migrations']
    def fingerprint(sql):
        return {table:sql(f"SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text),'[]') FROM {table} t;") for table in tables}
    before=fingerprint(database)
    definitions_before=json.loads(database(ACCESS_DEFINITIONS_SQL,app=True))
    restored=database.restore_into_fresh_database()
    assert fingerprint(restored)==before
    definitions_after=json.loads(restored(ACCESS_DEFINITIONS_SQL,app=True))
    diagnostics=Path(__file__).resolve().parents[1]/'evidence/restore-definition-diagnostics'/uuid4().hex
    diagnostics.mkdir(parents=True)
    for name,value in [('before',definitions_before),('after',definitions_after)]:
        (diagnostics/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    assert definitions_before==definitions_after,{key for key in definitions_before if definitions_before[key]!=definitions_after[key]}
    for actor,expected in [('local-user-alice','t'),('local-user-bob','t'),('local-user-carol','f')]:
        assert restored(f"SELECT nsai_private_can_read('recovery','{actor}');",app=True)==expected
    assert restored("SELECT count(*) FROM documents WHERE id='recovery';",app=True,actor='local-user-carol')=='0'
    assert restored("SELECT count(*) FROM documents WHERE id='recovery';",app=True,actor='local-user-bob')=='1'
    restored('SELECT * FROM native_semantic_passages;',app=True,actor='local-user-bob',ok=False)
    restored('SELECT * FROM semantic_job_vectors;',app=True,actor='local-user-alice',ok=False)
    assert restored('SELECT canonical_bytes=(SELECT sum(octet_length(payload::text)) FROM knowledge_embeddings) FROM semantic_storage_usage;')=='t'
    assert restored("SELECT state FROM semantic_jobs WHERE id=repeat('d',64);")=='queued'
