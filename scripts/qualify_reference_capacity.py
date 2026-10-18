"""Bounded owned capacity measurement; never changes admission or live limits."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
from uuid import uuid4
import migrate
from check_release_readiness import source_snapshot
from qualify_local_stack import Stack,ROOT


def main(profile):
    research=profile=='arxiv-development'
    corpus=ROOT/'data/arxiv-corpus/download-958f8bd56fe6'
    corpus_before={}
    if research:
        manifest=json.loads((corpus/'manifest.json').read_bytes())
        from ingest_arxiv_corpus import private_file
        for relative in ['manifest.json',*[row['pdf_relative_path'] for row in manifest['papers']]]:
            corpus_before[relative]=hashlib.sha256(private_file(corpus,relative).read_bytes()).hexdigest()
        assert len(manifest['papers'])==14 and all(corpus_before[row['pdf_relative_path']]==row['pdf_sha256'] for row in manifest['papers'])
    database_memory=3072 if profile=='P1' else 1536
    database_tmpfs=2048 if profile=='P1' else 1024
    deadline_seconds=1800 if profile=='P1' else 900
    resource_profile='reference-1000' if profile=='P1' else 'default'
    run=uuid4().hex;folder=ROOT/'evidence/reference-capacity'/run
    stack=Stack(folder,'nsai-db-package-qualified:local','nsai-ocr-hardened-candidate:local')
    before=source_snapshot(ROOT);fixtures=['library_corpus_runtime_fixture.py' if research else 'capacity_runtime_fixture.py','semantic_fixture_helpers.py']
    fixture_hashes={name:hashlib.sha256((ROOT/'tests'/name).read_bytes()).hexdigest() for name in fixtures}
    report=dict(status='FAIL',run_id=run,profile=profile,source_before=before,fixture_sha256=fixture_hashes,
        scope=__doc__,capacity_accepted=False,live_services_accessed=False,user_volumes_accessed=False,
        server_capacity_profile=resource_profile,
        workload='Private existing research PDFs; development retrieval measurement only' if research else 'Generated sparse native PDFs',
        corpus_input_sha256=corpus_before,retrieval_quality_accepted=False,
        profile_limits=dict(cpu_per_container=1,database_memory_mib=database_memory,parser_memory_mib=512,
                            encoder_memory_mib=768,client_memory_mib=1024,database_tmpfs_mib=database_tmpfs,whole_job_seconds=deadline_seconds))
    def command(arguments,*,timeout=30,ok=True):
        result=subprocess.run(['docker',*arguments],capture_output=True,timeout=timeout)
        if ok and result.returncode:raise RuntimeError('Owned capacity command failed')
        return result
    try:
        encoder_image=command(['image','inspect','nsai-cpu-encoder:qualification','--format','{{.Id}}']).stdout.decode().strip()
        report['images']=dict(api=stack.api_image,db=stack.db_image,encoder=encoder_image)
        report['encoder_manifest_sha256']=hashlib.sha256((ROOT/'state/models/all-MiniLM-L6-v2/manifest.json').read_bytes()).hexdigest()
        data_net=stack.network('data');parser_net=stack.network('parser');encoder_net=stack.network('encoder')
        with tempfile.TemporaryDirectory(prefix='nsai-capacity-') as temporary:
            temporary=Path(temporary);password=secrets.token_hex(32);application_password=secrets.token_hex(32)
            for name,value in [('db',application_password),('parser',secrets.token_hex(32)),('encoder',secrets.token_hex(32))]:
                (temporary/name).write_text(value)
            def secret(name):return ['--mount','type=bind,source='+str(temporary/name)+',target=/run/secrets/'+name+',readonly']
            db=stack.run('db',stack.db_image,['--tmpfs',f'/var/lib/postgresql/data:rw,nosuid,size={database_tmpfs}m,mode=1777',
                '--tmpfs','/var/run/postgresql:rw,nosuid,size=8m,mode=1777','-e','POSTGRES_USER=nsai',
                '-e','POSTGRES_DB=nsai','-e','POSTGRES_PASSWORD='+password,'-e','PGDATA=/var/lib/postgresql/data/pgdata'],
                network=data_net,alias='db',user='70:70',memory=str(database_memory)+'m',pids='128')
            for _ in range(120):
                if command(['exec',db,'pg_isready','-h','127.0.0.1','-U','nsai'],ok=False).returncode==0:break
                time.sleep(.1)
            else:raise RuntimeError('Capacity database readiness exceeded')
            stack.sql(db,migrate.migration_sql(ROOT)+migrate.role_sql(application_password))
            parser=stack.run('parser',stack.api_image,[*secret('parser'),'-e','NSAI_PARSER_TOKEN_FILE=/run/secrets/parser','--entrypoint','uvicorn'],
                ['nsai.parser:app','--host','0.0.0.0','--port','8788','--no-access-log'],network=parser_net,alias='parser',memory='512m')
            encoder=stack.run('encoder',encoder_image,[*secret('encoder'),'-e','NSAI_ENCODER_TOKEN_FILE=/run/secrets/encoder',
                '-e','NSAI_ENCODER_MODEL_DIR=/models','--mount','type=bind,source='+str(ROOT/'state/models/all-MiniLM-L6-v2')+',target=/models,readonly',
                '--entrypoint','uvicorn'],['nsai.encoder_service:app','--host','0.0.0.0','--port','8092','--no-access-log'],
                network=encoder_net,alias='encoder',memory='768m')
            for name,port in [(parser,8788),(encoder,8092)]:
                for _ in range(120):
                    probe="import urllib.request;urllib.request.urlopen('http://127.0.0.1:"+str(port)+"/healthz',timeout=2)"
                    if command(['exec',name,'python','-c',probe],ok=False).returncode==0:break
                    time.sleep(.1)
                else:raise RuntimeError('Capacity service readiness exceeded')
            name=stack.prefix+'-client'
            client_container=name
            # Create first, connect all isolated service networks, then start.
            options=['create','--name',name,'--label','nsai.owner='+stack.tag,'--network',data_net,
                '--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--user','10001:10001',
                '--cpus','1','--memory','1024m','--pids-limit','128','--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777',
                *secret('db'),*secret('parser'),*secret('encoder'),
                '--mount','type=bind,source='+str(ROOT/'tests'/fixtures[0])+',target=/qualification.py,readonly',
                '--mount','type=bind,source='+str(ROOT/'tests/semantic_fixture_helpers.py')+',target=/semantic_fixture_helpers.py,readonly',
                '-e','NSAI_DB_HOST=db','-e','NSAI_DB_USER=nsai_app','-e','NSAI_DB_NAME=nsai','-e','NSAI_DB_PASSWORD_FILE=/run/secrets/db',
                '-e','NSAI_CAPACITY_PROFILE='+resource_profile,
                '-e','NSAI_PARSER_URL=http://parser:8788','-e','NSAI_PARSER_TOKEN_FILE=/run/secrets/parser',
                '-e','NSAI_ENCODER_URL=http://encoder:8092','-e','NSAI_ENCODER_TOKEN_FILE=/run/secrets/encoder',
                '--entrypoint','python',stack.api_image,'/qualification.py','--profile',profile]
            if research:
                options[options.index('--entrypoint'):options.index('--entrypoint')]=['--mount','type=bind,source='+str(corpus)+',target=/corpus,readonly']
            command(options);stack.containers.append(name)
            command(['network','connect',parser_net,name]);command(['network','connect',encoder_net,name]);command(['start',name])
            deadline=time.monotonic()+deadline_seconds;next_progress=time.monotonic()+15
            while command(['inspect',name,'--format','{{.State.Running}}']).stdout.strip()==b'true':
                if time.monotonic()>deadline:raise TimeoutError('Owned capacity deadline exceeded')
                if time.monotonic()>=next_progress:
                    progress=dict(documents=int(stack.sql(db,'SELECT count(*) FROM documents;').strip().splitlines()[-1]),
                                  publications=int(stack.sql(db,'SELECT count(*) FROM semantic_publications;').strip().splitlines()[-1]))
                    (folder/'progress.json').write_text(json.dumps(progress),encoding='utf-8')
                    print(json.dumps(dict(run_id=run,progress=progress)),flush=True);next_progress=time.monotonic()+15
                time.sleep(1)
            output=command(['logs',name]);(folder/'worker-output.json').write_bytes(output.stdout)
            (folder/'worker-stderr.txt').write_bytes(output.stderr)
            code=command(['inspect',name,'--format','{{.State.ExitCode}}']).stdout.strip()
            lines=[json.loads(line) for line in output.stdout.splitlines() if line.strip()]
            report['worker_progress']=[line['progress'] for line in lines if 'progress' in line]
            def sql(statement):return stack.sql(db,statement).strip().splitlines()[-1]
            report['database']=dict(documents=int(sql('SELECT count(*) FROM documents;')),
                pages=int(sql("SELECT coalesce(sum(jsonb_array_length(manifest#>'{documents,0,metadata,pages}')),0) FROM documents;")),
                publications=int(sql('SELECT count(*) FROM semantic_publications;')),
                vectors=int(sql("SELECT count(*) FROM knowledge_embeddings e CROSS JOIN LATERAL jsonb_object_keys(e.payload->'vectors');")),
                native_vectors=int(sql('SELECT count(*) FROM native_semantic_passages;')),
                native_relation_bytes=int(sql("SELECT pg_total_relation_size('native_semantic_passages');")),
                database_bytes=int(sql('SELECT pg_database_size(current_database());')),
                embedding_bytes=int(sql('SELECT coalesce(sum(pg_column_size(payload)),0) FROM knowledge_embeddings;')),
                relation_index_bytes=int(sql("SELECT coalesce(sum(pg_indexes_size(c.oid)),0) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r';")),
                pgdata_end_bytes=int(command(['exec',db,'du','-sk','/var/lib/postgresql/data/pgdata']).stdout.split()[0])*1024)
            report['resources']={}
            for component,container in [('db',db),('parser',parser),('encoder',encoder),('client',name)]:
                peak=command(['exec',container,'cat','/sys/fs/cgroup/memory.peak'],ok=False)
                cpu=command(['exec',container,'cat','/sys/fs/cgroup/cpu.stat'],ok=False)
                # The completed client is stopped: copy its resource metrics from
                # inspect when cgroup access is unavailable, without inventing a peak.
                report['resources'][component]=dict(memory_peak_bytes=int(peak.stdout) if peak.returncode==0 else None,
                    cpu_stat=cpu.stdout.decode() if cpu.returncode==0 else None)
            client_observations=[entry for entry in report['worker_progress'] if 'memory_peak_bytes' in entry]
            if client_observations:
                report['resources']['client']=dict(memory_peak_bytes=client_observations[-1]['memory_peak_bytes'],
                    phase='last observed progress; later peak unknown')
            if code!=b'0':raise RuntimeError('Capacity worker failed; retained private diagnostics')
            report['result']=[line['result'] for line in lines if 'result' in line][-1]
            assert report['result']['status']=='PASS_SCOPED'
            assert report['database']['documents']==report['result']['documents']
            assert report['database']['pages']==report['result']['pages']
            assert report['database']['publications']==report['result']['documents']
            assert report['database']['vectors']>0
            if not research:assert report['database']['vectors']>=report['result']['pages']
            assert report['database']['native_vectors']==report['database']['vectors']
            report['resources']['client']=dict(**report['result']['client_resources_before_exit'],phase='observed before process exit')
            if research or profile=='smoke':
                from qualify_corpus_restore import verify_restore
                originals=report['result']['originals'] if research else [
                    dict(document_id=row['document_id'],original_sha256=row['sha256']) for row in report['result']['generated_sources']]
                report['data_preservation']=verify_restore(stack,ROOT,db,data_net,temporary/'db',originals,folder)
            report['source_after']=source_snapshot(ROOT)
            report['fixture_after_sha256']={key:hashlib.sha256((ROOT/'tests'/key).read_bytes()).hexdigest() for key in fixtures}
            assert report['source_before']==report['source_after'] and fixture_hashes==report['fixture_after_sha256']
            report['status']='PASS_SCOPED'
    except Exception as error:report['failure_type']=type(error).__name__;report['failure']=str(error)[:500]
    finally:
        for component in ('parser','encoder'):
            container=locals().get(component)
            if container and container in stack.containers:
                logs=command(['logs',container],ok=False)
                (folder/(component+'-output.txt')).write_bytes(logs.stdout)
                (folder/(component+'-stderr.txt')).write_bytes(logs.stderr)
        if 'client_container' in locals() and client_container in stack.containers and not (folder/'worker-output.json').exists():
            output=command(['logs',client_container],ok=False)
            (folder/'worker-output.json').write_bytes(output.stdout)
            (folder/'worker-stderr.txt').write_bytes(output.stderr)
        report['source_after']=source_snapshot(ROOT)
        if research:
            report['corpus_after_sha256']={relative:hashlib.sha256(private_file(corpus,relative).read_bytes()).hexdigest() for relative in corpus_before}
            if report['corpus_after_sha256']!=corpus_before:report['status']='FAIL';report['input_drift']=True
        report['fixture_after_sha256']={key:hashlib.sha256((ROOT/'tests'/key).read_bytes()).hexdigest() for key in fixtures}
        report['artifact_sha256']={path.name:hashlib.sha256(path.read_bytes()).hexdigest()
            for path in folder.iterdir() if path.is_file() and path.name!='capacity-receipt.json'}
        if report['source_before']!=report['source_after'] or fixture_hashes!=report['fixture_after_sha256']:
            report['status']='FAIL';report['input_drift']=True
        stack.cleanup();report['cleanup_complete']=stack.receipt['cleanup_complete']
        if not report['cleanup_complete']:report['status']='FAIL'
        (folder/'capacity-receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],profile=profile,run_id=run,cleanup=report['cleanup_complete'])))
    return 0 if report['status']=='PASS_SCOPED' else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--profile',choices=['smoke','P0','P1','arxiv-development'],required=True)
    raise SystemExit(main(parser.parse_args().profile))
