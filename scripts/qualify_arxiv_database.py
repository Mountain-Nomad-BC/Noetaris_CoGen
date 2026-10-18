"""Ingest and restore a prepared corpus in owned PostgreSQL; never the live database."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import secrets
import subprocess
import time
from uuid import uuid4
import migrate
from check_release_readiness import source_snapshot

ROOT=Path(__file__).resolve().parents[1]
DB_IMAGE='sha256:e8d60b4d26e679424148c662d01229c05d0d661745d846e7911af78b88bd9f6d'


def run(manifest,image,enrichment_manifest=None):
    if not re.fullmatch('sha256:[a-f0-9]{64}',image):raise ValueError('Exact candidate image required')
    folder=manifest.parent.resolve()
    if folder.parent!=ROOT/'data/arxiv-corpus' or manifest.name!='manifest.json':raise ValueError('Expected a prepared private corpus directory')
    if enrichment_manifest and not enrichment_manifest.resolve().is_relative_to(folder):raise ValueError('Supplement manifest outside prepared corpus')
    run_id='nsai-arxiv-db-'+uuid4().hex[:12];network=run_id+'-net';db=run_id+'-db';worker=run_id+'-worker';owner=uuid4().hex
    password=secrets.token_hex(32);app_password=secrets.token_hex(32)
    evidence=ROOT/'evidence/arxiv-ingestion'/run_id;evidence.mkdir(parents=True)
    backup_folder=ROOT/'state/arxiv-corpus'/run_id;backup_folder.mkdir(parents=True)
    report=dict(run_id=run_id,status='FAIL',candidate_image=image,database_image=DB_IMAGE,user_volumes_accessed=False,
                host_ports=False,owned_resources_only=True,sources_before=source_snapshot(ROOT),cleanup=[],restored=False)
    if enrichment_manifest:report['enrichment_manifest_sha256']=hashlib.sha256(enrichment_manifest.read_bytes()).hexdigest()
    def command(args,*,data=None,timeout=120):
        result=subprocess.run(args,cwd=ROOT,input=data,capture_output=True,timeout=timeout)
        if result.returncode:
            diagnostics=(result.stdout+result.stderr).decode(errors='replace')[-5000:]
            report['private_failure_diagnostics']=diagnostics.replace(password,'[owned credential]').replace(app_password,'[owned credential]')
            raise RuntimeError('Owned corpus command failed; inspect private receipt')
        return result.stdout
    def sql(statement,database='nsai'):
        return command(['docker','exec','-i',db,'psql','-v','ON_ERROR_STOP=1','-U','nsai','-d',database],data=statement.encode())
    def client(program,database='nsai'):
        prefix="import os\nfrom pathlib import Path\nPath('/tmp/db-password').write_text("+repr(app_password)+")\n"
        for role in ['operator','viewer']:
            prefix+="Path('/tmp/"+role+"').write_text("+repr(secrets.token_hex(32))+')\n'
        return command(['docker','run','--rm','--name',worker,'--label','nsai.owner='+owner,'--network',network,'--read-only',
             '--cap-drop','ALL','--security-opt','no-new-privileges:true','--user','10001:10001','--cpus','1','--memory','768m','--pids-limit','64',
             '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=32m,mode=1777','--mount','type=bind,source='+str(folder)+',target=/corpus,readonly',
             '-e','NSAI_DB_HOST='+db,'-e','NSAI_DB_NAME='+database,'-e','NSAI_DB_USER=nsai_app','-e','NSAI_DB_PASSWORD_FILE=/tmp/db-password',
             '-e','NSAI_API_TOKEN_FILE=/tmp/operator','-e','NSAI_VIEWER_TOKEN_FILE=/tmp/viewer',
             '-e','NSAI_CORPUS_ENRICHMENT='+('/corpus/'+enrichment_manifest.relative_to(folder).as_posix() if enrichment_manifest else ''),
             '-i',image,'python','-'],data=(prefix+program).encode(),timeout=600)
    try:
        command(['docker','network','create','--internal','--label','nsai.owner='+owner,network])
        command(['docker','run','-d','--name',db,'--label','nsai.owner='+owner,'--network',network,'--memory','768m','--cpus','.5',
            '--pids-limit','128','--security-opt','no-new-privileges:true','--tmpfs','/var/lib/postgresql/data:rw,nosuid,nodev,size=512m',
            '--tmpfs','/var/run/postgresql:rw,nosuid,nodev,size=8m','-e','POSTGRES_USER=nsai','-e','POSTGRES_DB=nsai',
            '-e','POSTGRES_PASSWORD='+password,DB_IMAGE])
        for _ in range(30):
            # initdb's temporary socket-only server must not satisfy runtime readiness.
            if subprocess.run(['docker','exec',db,'pg_isready','-h','127.0.0.1','-U','nsai','-d','nsai'],capture_output=True,timeout=5).returncode==0:break
            time.sleep(1)
        else:raise RuntimeError('Owned corpus database readiness failed')
        sql(migrate.migration_sql(ROOT)+migrate.role_sql(app_password))
        harness=(ROOT/'scripts/arxiv_database_harness.py').read_text()
        report['harness_sha256']=hashlib.sha256(harness.encode()).hexdigest()
        raw=client(harness);report['ingestion']=json.loads(raw)
        if report['ingestion']['status']!='PASS_SCOPED':raise RuntimeError('Owned corpus ingestion did not qualify')
        backup=backup_folder/'postgres.dump'
        migrate.stream_backup(['docker','exec',db,'pg_dump','--format=custom','--compress=6','--no-owner','--no-privileges','-U','nsai','-d','nsai'],backup,max_bytes=128*1024*1024,timeout=120)
        capture=json.loads(backup.with_suffix('.dump.manifest.json').read_text())
        if backup.stat().st_size!=capture['size_bytes'] or hashlib.sha256(backup.read_bytes()).hexdigest()!=capture['sha256']:
            raise RuntimeError('Backup byte admission failed')
        sql('CREATE DATABASE nsai_restore;')
        command(['docker','exec','-i',db,'pg_restore','--exit-on-error','--no-owner','--no-privileges','-U','nsai','-d','nsai_restore'],data=backup.read_bytes(),timeout=180)
        sql('BEGIN;GRANT CONNECT ON DATABASE nsai_restore TO nsai_app;'+migrate.role_sql(app_password),'nsai_restore')
        restore_program='''
from nsai import store, research_store as r, workflow_store as w
import json,hashlib
from pathlib import Path
manifest=json.loads(Path('/corpus/manifest.json').read_text())
checks=[]
for row in manifest['papers']:
 original,media=w.original_source(row['document_id'])
 assert hashlib.sha256(original).hexdigest()==row['source_sha256']
 artifact=r.get(row['document_id']);assert artifact['artifact_sha256']==row['artifact_sha256']
 graph=r.embedded_graph(row['document_id'],manifest['semantic_model']['sha256'])
 assert len(graph['embeddings']['records'])==row['semantic_passages']
 checks.append(row['document_id'])
assert w.audit_report()['valid']
with store.connect() as conn:
 counts={name:conn.execute('SELECT count(*) FROM '+name).fetchone()[0] for name in ['documents','document_knowledge','knowledge_embeddings','research_supplements','governed_records','claims','audit_events','sessions']}
for row in manifest['papers']:
 for supplement in r.supplements(row['document_id']):
  assert r.artifact_hash(supplement['payload'])==supplement['id'] and supplement['review_state']=='candidate'
print(json.dumps(dict(status='PASS_SCOPED',documents_restored=checks,counts=counts)))
'''
        report['restore']=json.loads(client(restore_program,'nsai_restore'))
        if report['restore']['counts']!=report['ingestion']['counts']:raise RuntimeError('Restored counts differ')
        report.update(restored=True,backup=dict(path=backup.relative_to(ROOT).as_posix(),**capture),status='PASS_SCOPED')
    except Exception as error:
        report['error_type']=type(error).__name__;report['status']='FAIL'
    finally:
        for name,kind in [(worker,'container'),(db,'container'),(network,'network')]:
            args=['docker','network','inspect',name] if kind=='network' else ['docker','inspect',name]
            inspected=subprocess.run(args,capture_output=True,timeout=15)
            if inspected.returncode:
                report['cleanup'].append(dict(name=name,absent=True));continue
            info=json.loads(inspected.stdout)[0];labels=info.get('Labels',{}) if kind=='network' else info['Config'].get('Labels',{})
            if labels.get('nsai.owner')!=owner:
                report['cleanup'].append(dict(name=name,absent=False,unowned_cleanup_refused=True));continue
            result=subprocess.run(['docker','network','rm',name] if kind=='network' else ['docker','rm','-f',name],capture_output=True,timeout=30)
            inspected=subprocess.run(args,capture_output=True,timeout=15)
            report['cleanup'].append(dict(name=name,absent=inspected.returncode!=0,remove_exit=result.returncode))
        report['cleanup_complete']=all(item['absent'] for item in report['cleanup'])
        report['sources_after']=source_snapshot(ROOT)
        if not report['cleanup_complete'] or report['sources_before']!=report['sources_after']:report['status']='FAIL'
        report['captured_at']=datetime.now(timezone.utc).isoformat()
        (evidence/'receipt.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        print(json.dumps(report,indent=2,allow_nan=False))
    return 0 if report['status']=='PASS_SCOPED' else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--image',required=True);p.add_argument('--enrichment-manifest',type=Path);a=p.parse_args()
    raise SystemExit(run(a.manifest.resolve(),a.image,a.enrichment_manifest.resolve() if a.enrichment_manifest else None))
