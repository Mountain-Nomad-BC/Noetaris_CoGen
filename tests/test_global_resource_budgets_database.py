import json
import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',
                             reason='explicit owned PostgreSQL qualification')


def test_private_owner_cannot_bypass_global_document_capacity(database):
    database("INSERT INTO documents(id,title,source_version,sha256,raw_text,owner_scope,ingested_by) "
             "SELECT 'hidden-'||n,'Hidden','1',md5(n::text),'fixture','local-user-bob','local-user-bob' FROM generate_series(1,98) n;",actor='local-user-bob')
    result=database.run_source_fixture('global_source_budget_pg_fixture.py')
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout.strip().splitlines()[-1])['global_limit_enforced']
    assert database('SELECT count(*) FROM documents;')=='100'


def test_job_scope_cannot_hide_other_owners_semantic_payload_usage(database):
    # Compressible synthetic payloads leave less than 16 KiB in the existing
    # 128 MiB canonical JSON budget. No private text crosses into Alice's client.
    database("INSERT INTO documents(id,title,source_version,sha256,raw_text,owner_scope,ingested_by) "
             "SELECT 'hidden-storage-'||n,'Hidden','1',md5(n::text),'fixture','local-user-bob','local-user-bob' FROM generate_series(1,8) n; "
             "INSERT INTO document_knowledge(document_id,source_sha256,revision,knowledge,formulas,artifact_sha256,source_ids,provenance_complete) "
             "SELECT 'hidden-storage-'||n,repeat('a',64),'1','{}','{}',repeat('d',64),ARRAY['hidden-storage-'||n],true FROM generate_series(1,8) n; "
             "INSERT INTO knowledge_embeddings(document_id,model_sha256,artifact_sha256,payload,source_ids,provenance_complete) "
             "SELECT 'hidden-storage-'||n,repeat('b',64),repeat('c',64),jsonb_build_object('padding',repeat('x',16775168)),ARRAY['hidden-storage-'||n],true FROM generate_series(1,8) n;",actor='local-user-bob')
    result=database.run_source_fixture('global_embedding_budget_pg_fixture.py')
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout.strip().splitlines()[-1])['no_partial_publication']
    assert database('SELECT canonical_bytes=(SELECT sum(octet_length(payload::text)) FROM knowledge_embeddings) FROM semantic_storage_usage;')=='t'
    database('SELECT * FROM semantic_storage_usage;',app=True,actor='local-user-alice',ok=False)


def test_semantic_storage_accounting_tracks_rollback_and_rejected_mutations(database):
    database("INSERT INTO document_knowledge(document_id,source_sha256,revision,knowledge,formulas,artifact_sha256) VALUES('legacy',repeat('a',64),'1','{}','{}',repeat('b',64));")
    insert="INSERT INTO knowledge_embeddings(document_id,model_sha256,artifact_sha256,payload) VALUES('legacy',repeat('a',64),repeat('b',64),'{\"x\":1}');"
    database('BEGIN; '+insert+' ROLLBACK;')
    assert database('SELECT canonical_bytes FROM semantic_storage_usage;')=='0'
    database(insert)
    database("UPDATE knowledge_embeddings SET payload='{\"x\":12345}';",ok=False)
    assert database('SELECT canonical_bytes=(SELECT sum(octet_length(payload::text)) FROM knowledge_embeddings) FROM semantic_storage_usage;')=='t'
    database('DELETE FROM knowledge_embeddings;',ok=False)
    assert database('SELECT canonical_bytes=(SELECT sum(octet_length(payload::text)) FROM knowledge_embeddings) FROM semantic_storage_usage;')=='t'
