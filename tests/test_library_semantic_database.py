"""Synthetic vectors qualify authorization/ranking mechanics, not model quality."""
import hashlib
import json
import os
import pytest
from test_private_access_database import database
from nsai.semantic_encoder import PINNED_MODEL_SHA256 as MODEL

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',
                             reason='explicit owned PostgreSQL qualification')


def test_library_search_filters_before_ranking_without_document_shortlist(database):
    statements=[]
    for number in range(27):
        doc=f'library-{number:02d}';owner='local-user-alice' if number<26 else 'local-user-bob'
        digest=hashlib.sha256(doc.encode()).hexdigest();node=hashlib.sha256((doc+'node').encode()).hexdigest()
        # Bob has the highest similarity and must not displace Alice's top hit.
        vector=[1.0]+[0.0]*383 if number==26 else [.8,.6]+[0.0]*382
        knowledge=json.dumps(dict(nodes=[dict(id=node,kind='passage',locator='page:1',page=1,text='Insulation coating degradation',
            source_segments=[dict(locator='page:1',char_start=0,char_end=10,text='Insulation'),
                             dict(locator='page:1:line:2',char_start=0,char_end=19,text='coating degradation')])]))
        payload=json.dumps(dict(vectors={node:vector}))
        text='insulation coating degradation '*(100 if number==26 else 1)
        statements.append(f"SET nsai.actor='{owner}'; SET nsai.role='operator'; "
            f"INSERT INTO documents(id,title,source_version,sha256,original_sha256,raw_text,owner_scope,ingested_by) VALUES('{doc}','Owned','1','{digest}','{digest}','source','{owner}','{owner}'); "
            f"INSERT INTO source_spans(document_id,locator,text) VALUES('{doc}','page:1','{text}'); "
            f"INSERT INTO chunks(id,document_id,locator,text,sha256) VALUES('{digest[:32]}','{doc}','page:1','{text}','{digest}'); "
            f"INSERT INTO document_knowledge(document_id,source_sha256,revision,knowledge,formulas,artifact_sha256,source_ids,provenance_complete) VALUES('{doc}','{digest}','1','{knowledge}','{{}}',repeat('b',64),ARRAY['{doc}'],true); "
            f"INSERT INTO knowledge_embeddings(document_id,model_sha256,artifact_sha256,payload,source_ids,provenance_complete) VALUES('{doc}','{MODEL}',repeat('c',64),'{payload}',ARRAY['{doc}'],true); "
            f"INSERT INTO semantic_jobs(id,document_id,requested_actor,source_revision,source_sha256,knowledge_sha256,model_sha256,state) VALUES('{digest}','{doc}','{owner}','1','{digest}',repeat('b',64),'{MODEL}','succeeded'); "
            f"INSERT INTO semantic_publications(id,document_id,model_sha256,knowledge_sha256,embedding_sha256,source_ids) VALUES('{digest}','{doc}','{MODEL}',repeat('b',64),repeat('c',64),ARRAY['{doc}']); "
            f"UPDATE source_index_state SET current_publication_id='{digest}',state='ready' WHERE document_id='{doc}';")
    database('\n'.join(statements))
    assert database('SELECT count(*) FROM native_semantic_passages;')=='27'
    database('SELECT * FROM native_semantic_passages;',app=True,actor='local-user-alice',ok=False)
    database("UPDATE native_semantic_passages SET locator='changed';",ok=False)
    database("SELECT nsai_build_native_passages('library-00','"+MODEL+"');",app=True,actor='local-user-alice',ok=False)
    query="ARRAY[1.0"+",0.0"*383+"]::double precision[]"
    call=f"nsai_library_semantic_search({query},NULL,NULL,NULL,NULL,51)"
    assert database(f'SELECT count(*) FROM {call};',app=True,actor='local-user-alice')=='26'
    result=json.loads(database(f'SELECT * FROM nsai_library_semantic_search({query},NULL,NULL,NULL,NULL,1);',app=True,actor='local-user-alice'))
    assert result['document_id']!='library-26' and result['score']==pytest.approx(.8)
    assert [segment['locator'] for segment in result['source_segments']]==['page:1','page:1:line:2']
    # A non-axis query checks exact coordinate order and signed dot products;
    # the oracle is the original Python vector, not the derived SQL index.
    for coordinates,expected_score in [([.6,.8]+[0.0]*382,.96),
                                        ([-1.0]+[0.0]*383,None)]:
        query_sql='ARRAY['+','.join(str(value) for value in coordinates)+']::double precision[]'
        scored=json.loads(database(f"SELECT coalesce(jsonb_agg(hit),'[]') FROM nsai_library_semantic_search({query_sql},NULL,NULL,NULL,NULL,51) hit;",app=True,actor='local-user-alice'))
        if expected_score is None:
            assert scored==[]
        else:
            assert len(scored)==26
            for hit in scored:
                assert hit['score']==pytest.approx(sum(a*b for a,b in zip([.8,.6]+[0.0]*382,coordinates)),abs=1e-12)
    assert database(f"SELECT count(*) FROM nsai_library_semantic_search({query},NULL,NULL,NULL,'coating',51);",app=True,actor='local-user-alice')=='26'
    assert database(f"SELECT count(*) FROM nsai_library_semantic_search({query},NULL,NULL,NULL,'unrelated',51);",app=True,actor='local-user-alice')=='0'
    assert database(f'SELECT count(*) FROM {call};',app=True,actor='local-user-bob')=='1'
    assert database(f'SELECT count(*) FROM {call};',app=True)=='0'
    lexical="nsai_library_lexical_search('insulation coating degradation','insulation OR coating OR degradation',NULL,NULL,NULL,NULL,51)"
    assert database(f'SELECT count(*) FROM {lexical};',app=True,actor='local-user-alice')=='26'
    assert database(f'SELECT count(*) FROM {lexical};',app=True,actor='local-user-bob')=='1'
    assert database(f'SELECT count(*) FROM {lexical};',app=True)=='0'
    for exact,alternate in [('coating','coating'),('unknown insulation','insulation OR degradation'),
                            ('insulation coating','insulation OR coating'),('insulation','')]:
        observed=json.loads(database(f"SELECT jsonb_agg(hit ORDER BY (hit->>'score')::double precision DESC,hit->>'id') FROM nsai_library_lexical_search('{exact}','{alternate}',NULL,NULL,NULL,NULL,51) hit;",app=True,actor='local-user-alice'))
        expected=json.loads(database("SELECT jsonb_agg(jsonb_build_object('id',id,'score',score) ORDER BY score DESC,id) FROM ("
            f"SELECT c.id,ts_rank_cd(c.search,plainto_tsquery('english','{exact}'))+ts_rank_cd(c.search,websearch_to_tsquery('english','{alternate}'))*0.25 AS score "
            f"FROM chunks c WHERE (c.search @@ plainto_tsquery('english','{exact}') OR c.search @@ websearch_to_tsquery('english','{alternate}')) "
            "AND nsai_index_source_readable(c.document_id)) ranked;",app=True,actor='local-user-alice'))
        assert [dict(id=hit['id'],score=hit['score']) for hit in observed]==expected
    assert database("SELECT count(*) FROM nsai_library_lexical_search('insulation','insulation',NULL,ARRAY['library-26'],NULL,NULL,1);",app=True,actor='local-user-alice')=='0'
    assert database("SELECT count(*) FROM nsai_library_lexical_search('insulation','insulation',NULL,NULL,'wrong',NULL,1);",app=True,actor='local-user-alice')=='0'
    assert database("SELECT count(*) FROM nsai_library_lexical_search('insulation','insulation',NULL,NULL,NULL,ARRAY[2],1);",app=True,actor='local-user-alice')=='0'
    assert database(f"SELECT count(*) FROM nsai_library_semantic_search({query},ARRAY['library-26'],NULL,NULL,NULL,1);",app=True,actor='local-user-alice')=='0'
    assert database(f"SELECT count(*) FROM nsai_library_semantic_search({query},NULL,'wrong',NULL,NULL,1);",app=True,actor='local-user-alice')=='0'
    assert database(f"SELECT count(*) FROM nsai_library_semantic_search({query},NULL,NULL,ARRAY[2],NULL,1);",app=True,actor='local-user-alice')=='0'
    database("SELECT nsai_private_share('library-26','local-user-bob',1,'user','local-user-alice',NULL,false);",app=True)
    result=json.loads(database(f'SELECT * FROM nsai_library_semantic_search({query},NULL,NULL,NULL,NULL,1);',app=True,actor='local-user-alice'))
    assert result['document_id']=='library-26'
    lexical_result=json.loads(database("SELECT * FROM nsai_library_lexical_search('insulation coating degradation','insulation OR coating OR degradation',NULL,NULL,NULL,NULL,1);",app=True,actor='local-user-alice'))
    assert lexical_result['document_id']=='library-26'
    database("SELECT nsai_private_share('library-26','local-user-bob',2,'user','local-user-alice',NULL,true);",app=True)
    result=json.loads(database(f'SELECT * FROM nsai_library_semantic_search({query},NULL,NULL,NULL,NULL,1);',app=True,actor='local-user-alice'))
    assert result['document_id']!='library-26'
    lexical_result=json.loads(database("SELECT * FROM nsai_library_lexical_search('insulation coating degradation','insulation OR coating OR degradation',NULL,NULL,NULL,NULL,1);",app=True,actor='local-user-alice'))
    assert lexical_result['document_id']!='library-26'
