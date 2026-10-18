"""Owned PostgreSQL SIGKILL recovery; synthetic sources, never live resources."""
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import migrate
from check_release_readiness import source_snapshot
from qualify_local_stack import Stack
import qualify_local_stack as stack_module
from qualify_corpus_restore import fingerprint

HEADER="""import asyncio,hashlib,json,sys,time
sys.path.insert(0,'/')
from pathlib import Path
from unittest.mock import patch
from nsai import api,store,security,workflow_store as w,semantic_jobs as jobs,research_store
from semantic_fixture_helpers import configure_authority,synthetic_encode,mixed_extraction_fixture
configure_authority()
alice=security.resolve_principal('Bearer '+Path('/tmp/fixture-user-alice').read_text())
"""


def main():
    started=time.monotonic();deadline=started+600
    run=uuid4().hex;folder=ROOT/'evidence/process-crash-recovery'/run
    stack=Stack(folder,'nsai-db-package-qualified:local','nsai-ocr-hardened-candidate:local')
    volume=stack.prefix+'-pgdata';volume_created=False
    report=dict(status='FAIL',run_id=run,scope=__doc__,checks=[],source_before=source_snapshot(ROOT),
        fixture_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        helper_sha256=hashlib.sha256((ROOT/'tests/semantic_fixture_helpers.py').read_bytes()).hexdigest(),
        images=dict(api=stack.api_image,database=stack.db_image),live_resources_accessed=False,
        user_volumes_accessed=False,host_ports=False,release_approved=False,
        profile=dict(whole_job_seconds=600,cpu_per_container=1,database_memory_mib=768,client_memory_mib=512),
        encoder='Synthetic unit vectors; no semantic quality claim',host_power_loss_qualified=False)
    def command(args,*,timeout=60,ok=True,data=None):
        remaining=deadline-time.monotonic()
        if remaining<=0:raise TimeoutError('Owned crash-recovery deadline')
        result=subprocess.run(['docker',*args],input=data,capture_output=True,timeout=min(timeout,remaining))
        if ok and result.returncode:raise RuntimeError('Owned crash-recovery command failed')
        return result
    original_command=stack_module.command
    def bounded_stack_command(args,*,input=None,timeout=60):
        if not args or args[0]!='docker':raise ValueError('Unexpected owned stack command')
        return command(args[1:],timeout=timeout,data=input).stdout
    # Includes all per-table fingerprint SQL and Stack.run/network commands.
    # Cleanup deliberately remains available after the work deadline.
    stack_module.command=bounded_stack_command
    def check(label,value):
        report['checks'].append(dict(label=label,pass_=bool(value)))
        if not value:raise AssertionError(label)
    def owned(name):
        data=json.loads(command(['inspect',name]).stdout)[0]
        if name not in stack.containers or data['Config'].get('Labels',{}).get('nsai.owner')!=stack.tag:
            raise RuntimeError('Refused action on unowned container')
    def ready(db):
        for _ in range(120):
            if command(['exec',db,'pg_isready','-h','127.0.0.1','-U','nsai'],ok=False).returncode==0:return
            time.sleep(.1)
        raise RuntimeError('Owned crash database readiness')
    try:
        network=stack.network('data')
        command(['volume','create','--label','nsai.owner='+stack.tag,volume]);volume_created=True
        initializer=stack.prefix+'-volume-init';stack.containers.append(initializer)
        command(['run','--rm','--name',initializer,'--label','nsai.owner='+stack.tag,'--network','none',
            '--read-only','--cap-drop','ALL','--cap-add','CHOWN','--security-opt','no-new-privileges:true',
            '--user','0:0','--memory','64m','--cpus','.25','--pids-limit','32',
            '--mount','type=volume,source='+volume+',target=/owned','--entrypoint','chown',stack.db_image,'70:70','/owned'])
        with tempfile.TemporaryDirectory(prefix='nsai-crash-') as temporary:
            secret=Path(temporary)/'app-db';password=secrets.token_hex(32);secret.write_text(password,encoding='utf-8')
            db=stack.run('db',stack.db_image,['--mount','type=volume,source='+volume+',target=/var/lib/postgresql/data',
                '--tmpfs','/var/run/postgresql:rw,nosuid,nodev,size=8m,mode=1777',
                '-e','POSTGRES_USER=nsai','-e','POSTGRES_DB=nsai','-e','POSTGRES_PASSWORD='+secrets.token_hex(32),
                '-e','PGDATA=/var/lib/postgresql/data/pgdata'],network=network,alias='db',user='70:70',memory='768m',pids='128')
            ready(db);stack.sql(db,migrate.migration_sql(ROOT)+migrate.role_sql(password))
            settings=json.loads(stack.sql(db,"SELECT json_build_object('fsync',current_setting('fsync'),'synchronous_commit',current_setting('synchronous_commit'),'full_page_writes',current_setting('full_page_writes'));").strip())
            report['durability_settings']=settings
            check('PostgreSQL acknowledged-commit durability settings remain enabled',all(v=='on' for v in settings.values()))
            system_before=stack.sql(db,'SELECT system_identifier FROM pg_control_system();').strip()
            def client(suffix,program,wait=True):
                name=stack.run(suffix,stack.api_image,['--mount','type=bind,source='+str(secret)+',target=/run/db,readonly',
                    '--mount','type=bind,source='+str(ROOT/'tests/semantic_fixture_helpers.py')+',target=/semantic_fixture_helpers.py,readonly',
                    '-e','NSAI_DB_HOST=db','-e','NSAI_DB_NAME=nsai','-e','NSAI_DB_USER=nsai_app',
                    '-e','NSAI_DB_PASSWORD_FILE=/run/db','--entrypoint','python'],['-c',HEADER+program],
                    network=network,memory='512m',pids='64')
                if not wait:return name
                completed=command(['wait',name],timeout=120)
                output=command(['logs',name]);(folder/(suffix+'-stdout.json')).write_bytes(output.stdout)
                (folder/(suffix+'-stderr.txt')).write_bytes(output.stderr)
                if completed.stdout.strip()!=b'0':raise RuntimeError('Owned application crash fixture failed: '+suffix)
                return json.loads(output.stdout.strip().splitlines()[-1])
            state=client('committed',"""
data,native,parsed=mixed_extraction_fixture()
with store.identity_context(alice):mixed=w.persist_source('Crash preserved native and OCR','1',data,parsed,alice['actor'])['document_id']
job=jobs.claim_next();assert job['document_id']==mixed
assert asyncio.run(jobs.process_job(job,encode=synthetic_encode))['state']=='succeeded'
with store.identity_context(alice):pending=api.ingest(api.DocumentInput(title='Crash preserved checkpoint',version='1',text='Motor-K maximum operating temperature is 72 C.'),alice)['document_id']
job=jobs.claim_next();assert job['document_id']==pending
save=jobs._save_checkpoints
class CheckpointCrash(RuntimeError):pass
def checkpoint_then_fail(job,records):
 save(job,records);raise CheckpointCrash()
with patch('nsai.semantic_jobs._save_checkpoints',side_effect=checkpoint_then_fail):
 try:asyncio.run(jobs.process_job(job,encode=synthetic_encode))
 except CheckpointCrash:pass
 else:raise AssertionError('Expected checkpoint interruption')
assert jobs.fail_job(job,'processing-failed')
print(json.dumps(dict(mixed=mixed,pending=pending,original_sha256=hashlib.sha256(data).hexdigest(),native_snapshot=parsed['extraction_history'][0],checkpoint_job=job['id'])),flush=True)
""")
            report['committed_state']=state
            print(json.dumps(dict(progress='acknowledged sources and checkpoint committed',run_id=run)),flush=True)
            before=fingerprint(stack,db);(folder/'committed-tables-before.json').write_text(json.dumps(before,indent=2)+'\n')
            writer=client('uncommitted',"""
from nsai.ingestion import parse_source
persist=research_store.persist
def pause_after_research(*args,**kwargs):
 result=persist(*args,**kwargs)
 print(json.dumps(dict(phase='transaction-open',document_id=args[1])),flush=True)
 while True:time.sleep(1)
with store.identity_context(alice),patch('nsai.research_store.persist',side_effect=pause_after_research):
 w.persist_source('Unacknowledged crash upload','1',b'Uncommitted source must not survive.',parse_source(b'Uncommitted source must not survive.','pending.txt'),alice['actor'])
""",wait=False)
            for _ in range(60):
                output=command(['logs',writer])
                if output.stdout.strip():
                    pending_write=json.loads(output.stdout.strip().splitlines()[-1]);break
                time.sleep(.1)
            else:raise RuntimeError('Uncommitted application transaction not observed')
            check('Real source transaction has not committed before forced kill',pending_write['phase']=='transaction-open'
                and stack.sql(db,"SELECT count(*) FROM pg_stat_activity WHERE usename='nsai_app' AND state='idle in transaction';").strip()=='1')
            owned(db);command(['kill','--signal','KILL',db]);owned(writer);command(['kill','--signal','KILL',writer])
            print(json.dumps(dict(progress='owned database hard-killed',run_id=run)),flush=True)
            command(['start',db]);ready(db)
            check('Same owned persistent cluster restarts rather than being reinitialized',
                stack.sql(db,'SELECT system_identifier FROM pg_control_system();').strip()==system_before)
            after=fingerprint(stack,db);(folder/'committed-tables-after.json').write_text(json.dumps(after,indent=2)+'\n')
            check('Every committed public-table row survives database SIGKILL',before['tables']==after['tables'])
            # PostgreSQL sequences can advance for an aborted transaction; gaps
            # are valid and do not imply missing committed source records.
            report['sequence_state_before']=before['sequences'];report['sequence_state_after']=after['sequences']
            check('Unacknowledged source transaction is absent after WAL recovery',
                stack.sql(db,"SELECT count(*) FROM documents WHERE id='"+pending_write['document_id']+"';").strip()=='0')
            result=client('recovered','expected='+repr(state)+'\n'+"""
with store.identity_context(alice):
 original,media=w.original_source(expected['mixed'])
 assert media=='application/pdf' and hashlib.sha256(original).hexdigest()==expected['original_sha256']
 assert w.source(expected['mixed'])['manifest']['documents'][0]['metadata']['extraction_history'][0]==expected['native_snapshot']
 assert jobs.source_status(expected['mixed'])['ready']
job=jobs.claim_next();assert job['id']==expected['checkpoint_job']
calls=[]
async def encode(texts):calls.extend(texts);return await synthetic_encode(texts)
assert asyncio.run(jobs.process_job(job,encode=encode))['state']=='succeeded'
assert calls==['Index generation identity check']
with store.identity_context(alice):
 assert jobs.source_status(expected['pending'])['ready']
 assert w.original_source(expected['pending'])[0]==b'Motor-K maximum operating temperature is 72 C.'
bob=security.resolve_principal('Bearer '+Path('/tmp/fixture-user-bob').read_text())
with store.identity_context(bob):assert api.documents(limit=25,cursor=None,q=None,identity=bob)['total']==0
print(json.dumps(dict(originals_preserved=True,exact_native_snapshot_preserved=True,published_index_preserved=True,checkpoint_reused=True,private_isolation_preserved=True)))
""")
            report['application_recovery']=result
            check('Packaged application preserves originals snapshots indexes checkpoints and private isolation',all(result.values()))
            report['status']='PASS_SCOPED'
    except Exception as error:report.update(failure_type=type(error).__name__,failure=str(error)[:500])
    finally:
        stack_module.command=original_command
        report['work_elapsed_seconds']=time.monotonic()-started
        if report['work_elapsed_seconds']>600:report['status']='FAIL_TIMEOUT'
        if 'db' in locals():
            logs=subprocess.run(['docker','logs',db],capture_output=True,timeout=30)
            (folder/'database-log.txt').write_bytes(logs.stdout+logs.stderr)
        report['source_after']=source_snapshot(ROOT)
        report['helper_after_sha256']=hashlib.sha256((ROOT/'tests/semantic_fixture_helpers.py').read_bytes()).hexdigest()
        report['fixture_after_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        if report['source_before']!=report['source_after'] or report['helper_sha256']!=report['helper_after_sha256'] or report['fixture_sha256']!=report['fixture_after_sha256']:report['status']='FAIL'
        stack.cleanup();report['cleanup_complete']=stack.receipt['cleanup_complete']
        if volume_created:
            metadata=json.loads(subprocess.run(['docker','volume','inspect',volume],capture_output=True,check=True,timeout=30).stdout)[0]
            if metadata.get('Labels',{}).get('nsai.owner')!=stack.tag:raise RuntimeError('Refused unowned volume removal')
            removed=subprocess.run(['docker','volume','rm',volume],capture_output=True,timeout=30).returncode==0
            report['owned_volume_removed']=removed;report['cleanup_complete'] &= removed
        if not report['cleanup_complete']:report['status']='FAIL'
        report['artifacts']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file() and p.name!='receipt.json'}
        (folder/'receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],run_id=run,checks=len(report['checks']),cleanup=report['cleanup_complete'])))
    return 0 if report['status']=='PASS_SCOPED' else 1


if __name__=='__main__':raise SystemExit(main())
