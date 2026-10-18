"""Owned SQL-seeded query-plan diagnostic, not ingestion/capacity acceptance."""
import hashlib
import argparse
import json
import secrets
import subprocess
import time
from uuid import uuid4
import migrate
from qualify_local_stack import Stack,ROOT
from check_release_readiness import source_snapshot


def main(mode='lexical',plan_cache='auto',repeated_session=False):
    folder=ROOT/'evidence/lexical-query-diagnostics'/uuid4().hex
    stack=Stack(folder,'nsai-db-package-qualified:local','nsai-ocr-hardened-candidate:local')
    before=source_snapshot(ROOT);report=dict(status='FAIL',scope=__doc__,source_before=before,
        production_limits_changed=False,sql_seed_only=True,documents=1000,chunks=50000,mode=mode,
        vector_scope='Synthetic normalized dense vectors; not model output' if mode=='semantic' else None,
        plan_cache_mode=plan_cache,repeated_session=repeated_session)
    try:
        network=stack.network('data')
        db=stack.run('db',stack.db_image,['--tmpfs','/var/lib/postgresql/data:rw,nosuid,size=2048m,mode=1777',
            '--tmpfs','/var/run/postgresql:rw,nosuid,size=8m,mode=1777','-e','POSTGRES_USER=nsai','-e','POSTGRES_DB=nsai',
            '-e','POSTGRES_PASSWORD='+secrets.token_hex(32),'-e','PGDATA=/var/lib/postgresql/data/pgdata'],
            network=network,alias='db',user='70:70',memory='3072m',pids='128')
        for _ in range(100):
            ready=subprocess.run(['docker','exec',db,'pg_isready','-h','127.0.0.1','-U','nsai'],capture_output=True)
            if ready.returncode==0:break
            time.sleep(.1)
        stack.sql(db,migrate.migration_sql(ROOT)+migrate.role_sql(secrets.token_hex(32)))
        seed="""SET nsai.actor='local-user-alice'; SET nsai.role='operator';
        INSERT INTO documents(id,title,source_version,sha256,original_sha256,raw_text,owner_scope,ingested_by,manifest)
        SELECT 'probe-'||n,'Synthetic plan fixture','1',md5(n::text)||md5(n::text),md5(n::text)||md5(n::text),'Synthetic source',
          'local-user-alice','local-user-alice',jsonb_build_object('documents',jsonb_build_array(jsonb_build_object('metadata',
            jsonb_build_object('complete',true,'pages',(SELECT jsonb_agg(jsonb_build_object('page',p,'status','native','complete',true)) FROM generate_series(1,50) p),
                              'diagnostic_padding',repeat('synthetic source metadata ',1000)))))
        FROM generate_series(1,1000) n;
        INSERT INTO source_spans(document_id,locator,text)
        SELECT 'probe-'||n,'page:'||p||':line:1','Motor-'||n||' synthetic inspection bulletin: record coating wear and inspect insulation.'
        FROM generate_series(1,1000) n CROSS JOIN generate_series(1,50) p;
        INSERT INTO chunks(id,document_id,locator,text,sha256)
        SELECT md5(document_id||locator),document_id,locator,text,md5(text)||md5(text) FROM source_spans;
        INSERT INTO document_knowledge(document_id,source_sha256,revision,knowledge,formulas,artifact_sha256,source_ids,provenance_complete)
        SELECT id,original_sha256,'1','{}','{}',repeat('b',64),ARRAY[id],true FROM documents;
        INSERT INTO knowledge_embeddings(document_id,model_sha256,artifact_sha256,payload,source_ids,provenance_complete)
        SELECT id,repeat('a',64),repeat('c',64),'{}',ARRAY[id],true FROM documents;
        INSERT INTO semantic_jobs(id,document_id,requested_actor,source_revision,source_sha256,knowledge_sha256,model_sha256,state)
        SELECT md5(id)||md5(id),id,'local-user-alice','1',original_sha256,repeat('b',64),repeat('a',64),'succeeded' FROM documents;
        INSERT INTO semantic_publications(id,document_id,model_sha256,knowledge_sha256,embedding_sha256,source_ids)
        SELECT md5(id)||md5(id),id,repeat('a',64),repeat('b',64),repeat('c',64),ARRAY[id] FROM documents;
        UPDATE source_index_state SET state='ready',current_publication_id=md5(document_id)||md5(document_id);
        ANALYZE;
        """
        if mode=='semantic':
            node_id="md5(id||p::text)||md5(id||p::text)"
            knowledge="jsonb_build_object('nodes',(SELECT jsonb_agg(jsonb_build_object('id',"+node_id+",'kind','passage','locator','page:'||p||':line:1','page',p,'text','Synthetic insulation inspection passage')) FROM generate_series(1,50) p))"
            payload="jsonb_build_object('vectors',(SELECT jsonb_object_agg("+node_id+",to_jsonb(array_fill(1/sqrt(384::double precision),ARRAY[384]))) FROM generate_series(1,50) p))"
            seed=seed.replace("'1','{}','{}',repeat('b',64)","'1',"+knowledge+",'{}',repeat('b',64)",1)
            seed=seed.replace("repeat('c',64),'{}',ARRAY[id]","repeat('c',64),"+payload+",ARRAY[id]",1)
            seed=seed.replace("repeat('a',64)","'6fd5d72fe4589f189f8ebc006442dbb529bb7ce38f8082112682524616046452'")
            seed="SET nsai.capacity_profile='reference-1000'; "+seed
        stack.sql(db,seed);report['seed_sha256']=hashlib.sha256(seed.encode()).hexdigest()
        query="""LOAD 'auto_explain'; SET auto_explain.log_nested_statements=on;
        SET auto_explain.log_analyze=on; SET auto_explain.log_buffers=on;
        SET auto_explain.log_timing=on; SET auto_explain.log_verbose=on;
        SET auto_explain.log_min_duration='50ms'; SET auto_explain.log_format=json;
        SET statement_timeout='60s'; SET ROLE nsai_app;
        SET nsai.actor='local-user-alice'; SET nsai.role='operator';
        SELECT count(*) FROM nsai_library_lexical_search('Which documents discuss coating wear and insulation inspection?',
          '"documents" OR "discuss" OR "coating" OR "wear" OR "insulation" OR "inspection"',NULL,NULL,NULL,NULL,13);
        """
        if mode=='semantic':
            query=query[:query.index('        SELECT count(*) FROM nsai_library_lexical_search')]+"SELECT count(*) FROM nsai_library_semantic_search(array_fill(1/sqrt(384::double precision),ARRAY[384]),NULL,NULL,NULL,NULL,13);"
        query="SET plan_cache_mode='"+plan_cache+"'; "+query
        if repeated_session:
            boundary=query.index('SELECT count(*) FROM nsai_library_')
            program=query[:boundary]+"\n\\timing on\n"+(query[boundary:]+"\n")*8
            result=subprocess.run(['docker','exec','-i',db,'psql','-v','ON_ERROR_STOP=1','-At','-U','nsai','-d','nsai'],
                input=program.encode('utf-8'),capture_output=True,timeout=540)
            (folder/'repeated-session-output.txt').write_bytes(result.stdout)
            (folder/'repeated-session-errors.txt').write_bytes(result.stderr)
            report['repeated_session_returncode']=result.returncode
            assert result.returncode==0,'Repeated same-session query failed; retained output'
        start=time.perf_counter();output=stack.sql(db,query);report['elapsed_seconds']=time.perf_counter()-start
        report['query_sha256']=hashlib.sha256(query.encode()).hexdigest()
        assert output.strip().splitlines()[-1]=='13'
        plain=query.replace("SET auto_explain.log_min_duration='50ms'","SET auto_explain.log_min_duration=-1")
        report['uninstrumented_seconds']=[]
        for _ in range(3):
            start=time.perf_counter();output=stack.sql(db,plain)
            report['uninstrumented_seconds'].append(time.perf_counter()-start)
            assert output.strip().splitlines()[-1]=='13'
        report['rank_component_seconds']={}
        for name,expression in ([] if mode=='semantic' else [
            ('exact',"ts_rank_cd(search,plainto_tsquery('english','Which documents discuss coating wear and insulation inspection?'))"),
            ('alternate',"ts_rank_cd(search,websearch_to_tsquery('english','\"documents\" OR \"discuss\" OR \"coating\" OR \"wear\" OR \"insulation\" OR \"inspection\"'))")]):
            start=time.perf_counter();stack.sql(db,'SELECT sum('+expression+') FROM chunks;')
            report['rank_component_seconds'][name]=time.perf_counter()-start
        logs=subprocess.run(['docker','logs',db],capture_output=True,timeout=30,check=True)
        (folder/'nested-plans.txt').write_bytes(logs.stderr)
        report['plans_sha256']=hashlib.sha256(logs.stderr).hexdigest()
        report['source_after']=source_snapshot(ROOT)
        assert report['source_before']==report['source_after']
        report['status']='PASS_DIAGNOSTIC'
    except Exception as error:report['failure_type']=type(error).__name__;report['failure']=str(error)[:500]
    finally:
        if 'db' in locals():
            logs=subprocess.run(['docker','logs',db],capture_output=True,timeout=30)
            (folder/'nested-plans.txt').write_bytes(logs.stderr)
            report['plans_sha256']=hashlib.sha256(logs.stderr).hexdigest()
        stack.cleanup();report['cleanup_complete']=stack.receipt['cleanup_complete']
        (folder/'diagnostic-receipt.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(status=report['status'],folder=folder.as_posix(),seconds=report.get('elapsed_seconds'))))
    return 0 if report['status']=='PASS_DIAGNOSTIC' else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mode',choices=['lexical','semantic'],default='lexical')
    parser.add_argument('--plan-cache',choices=['auto','force_custom_plan','force_generic_plan'],default='auto')
    parser.add_argument('--repeated-session',action='store_true')
    args=parser.parse_args()
    raise SystemExit(main(args.mode,args.plan_cache,args.repeated_session))
