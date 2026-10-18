import json
import os
import pytest
from test_private_access_database import database
from nsai.semantic_encoder import PINNED_MODEL_SHA256 as MODEL

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',
                             reason='explicit owned PostgreSQL qualification')


def test_native_vector_shape_finiteness_norm_and_index_rollback(database):
    unit='ARRAY[1.0::double precision]||array_fill(0::double precision,ARRAY[383])'
    assert database(f'SELECT nsai_native_vector_valid({unit});')=='t'
    for vector in ['NULL','ARRAY[1.0::double precision]',"ARRAY['NaN'::double precision]||array_fill(0::double precision,ARRAY[383])",'array_fill(0::double precision,ARRAY[384])']:
        assert database(f'SELECT nsai_native_vector_valid({vector});')=='f'
    graph=json.dumps(dict(nodes=[dict(id=key*64,kind='passage',locator='page:1',page=1,text='Candidate source passage') for key in ['a','b']]))
    payload=json.dumps(dict(vectors={'a'*64:[1.0]+[0.0]*383,'b'*64:[1.0,0.0]}))
    database("INSERT INTO documents(id,title,source_version,sha256,raw_text,owner_scope,ingested_by) "
        "VALUES('bad-native','Fixture','1',repeat('d',64),'Fixture','local-user-alice','local-user-alice'); "
        f"INSERT INTO document_knowledge(document_id,source_sha256,revision,knowledge,formulas,artifact_sha256,source_ids,provenance_complete) VALUES('bad-native',repeat('d',64),'1','{graph}','{{}}',repeat('b',64),ARRAY['bad-native'],true);",actor='local-user-alice')
    before=database('SELECT canonical_bytes FROM semantic_storage_usage;')
    database(f"INSERT INTO knowledge_embeddings(document_id,model_sha256,artifact_sha256,payload,source_ids,provenance_complete) VALUES('bad-native','{MODEL}',repeat('c',64),'{payload}',ARRAY['bad-native'],true);",ok=False)
    assert database("SELECT count(*) FROM knowledge_embeddings WHERE document_id='bad-native';")=='0'
    assert database("SELECT count(*) FROM native_semantic_passages WHERE document_id='bad-native';")=='0'
    assert database('SELECT canonical_bytes FROM semantic_storage_usage;')==before


def test_ignored_duplicate_embedding_does_not_charge_storage_twice(database):
    graph=json.dumps(dict(nodes=[dict(id='a'*64,kind='passage',locator='page:1',page=1,text='Idempotent source')]))
    payload=json.dumps(dict(vectors={'a'*64:[1.0]+[0.0]*383}))
    database("INSERT INTO documents(id,title,source_version,sha256,raw_text,owner_scope,ingested_by) "
        "VALUES('idempotent-native','Fixture','1',repeat('e',64),'Fixture','local-user-alice','local-user-alice'); "
        f"INSERT INTO document_knowledge(document_id,source_sha256,revision,knowledge,formulas,artifact_sha256,source_ids,provenance_complete) VALUES('idempotent-native',repeat('e',64),'1','{graph}','{{}}',repeat('b',64),ARRAY['idempotent-native'],true);",actor='local-user-alice')
    insert=f"INSERT INTO knowledge_embeddings(document_id,model_sha256,artifact_sha256,payload,source_ids,provenance_complete) VALUES('idempotent-native','{MODEL}',repeat('c',64),'{payload}',ARRAY['idempotent-native'],true) ON CONFLICT(document_id,model_sha256) DO NOTHING;"
    database(insert);before=database('SELECT canonical_bytes FROM semantic_storage_usage;')
    database(insert)
    assert database('SELECT count(*) FROM knowledge_embeddings;')=='1'
    assert database('SELECT canonical_bytes FROM semantic_storage_usage;')==before
