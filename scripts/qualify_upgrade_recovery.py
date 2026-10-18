"""Owned populated-schema upgrade/refusal/restore rehearsal; never selects live resources."""
from __future__ import annotations
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import tempfile
import time
import traceback
from uuid import uuid4

import migrate
from qualify_local_stack import Stack

ROOT=Path(__file__).resolve().parent.parent
DB_IMAGE='sha256:e8d60b4d26e679424148c662d01229c05d0d661745d846e7911af78b88bd9f6d'
API_IMAGE='sha256:2ffe38c418aa16260baeaa9b6f0469ce9e58e84fdff792f7784746bef824113d'
PROFILE=dict(database_cpu=.75,database_memory_mib=768,client_cpu=.25,client_memory_mib=256,
    aggregate_cpu_max=1,aggregate_memory_mib_max=1024,pg_tmpfs_mib=256,host_ports=False,
    internal_network=True,inference_calls=0,whole_job_seconds=600,backup_bytes_max=16*1024*1024)

def digest(data):return hashlib.sha256(data).hexdigest()

def write(path,data):
    """Publish a complete private snapshot; failed serialization keeps the previous one."""
    path=Path(path);partial=path.with_name(path.name+'.'+uuid4().hex+'.partial')
    try:
        with partial.open('x',encoding='utf-8')as stream:
            json.dump(data,stream,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        os.replace(partial,path)
    finally:
        if partial.exists():partial.unlink()

def source_hashes():
    paths=[ROOT/'deploy/init.sql',ROOT/'scripts/migrate.py',ROOT/'scripts/qualify_local_stack.py',Path(__file__)]
    paths+=sorted((ROOT/'database/migrations').glob('*.sql'))
    return {p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in paths}

def historical_root(source,target,through):
    """Copy original SQL bytes only into an owned temporary migration window."""
    target=Path(target);(target/'deploy').mkdir(parents=True);(target/'database/migrations').mkdir(parents=True)
    shutil.copyfile(Path(source)/'deploy/init.sql',target/'deploy/init.sql')
    for p in sorted((Path(source)/'database/migrations').glob('*.sql')):
        if p.name<=through:shutil.copyfile(p,target/'database/migrations'/p.name)
    return target

def retained_rows(before,after):
    """Compare original column values; additive columns have separate full hashes."""
    observed=after.get('historical_tables',after['tables'])
    return all(name=='nsai_schema_migrations' or observed.get(name)==value for name,value in before['tables'].items())

def journal_entries(root):
    root=Path(root);paths=[root/'deploy/init.sql']+sorted((root/'database/migrations').glob('*.sql'))
    return {p.relative_to(root).as_posix():digest(p.read_bytes()) for p in paths}

def admitted_backup(path):
    """Independent recovery admission requires an exact complete size/digest manifest."""
    path=Path(path);manifest=path.with_suffix(path.suffix+'.manifest.json')
    if path.is_symlink() or manifest.is_symlink():raise ValueError('Backup symlinks are not admitted')
    data=json.loads(manifest.read_text());size=path.stat().st_size
    if type(data.get('size_bytes'))is not int or not 0<size<=PROFILE['backup_bytes_max'] or size!=data['size_bytes']:
        raise ValueError('Backup size admission failed')
    hasher=hashlib.sha256()
    with path.open('rb')as stream:
        for block in iter(lambda:stream.read(65536),b''):hasher.update(block)
    if not re.fullmatch('[a-f0-9]{64}',data.get('sha256',''))or hasher.hexdigest()!=data['sha256']:
        raise ValueError('Backup digest admission failed')
    return data

class Rehearsal:
    def __init__(self,output,compatibility_image=API_IMAGE):
        if not isinstance(compatibility_image,str)or not re.fullmatch('sha256:[a-f0-9]{64}',compatibility_image):
            raise ValueError('An exact local compatibility image digest is required')
        self.tag='nsai-upgrade-'+uuid4().hex[:12];self.output=Path(output)/self.tag;self.output.mkdir(parents=True)
        self.network=self.tag+'-net';self.containers=[];self.serial=0;self.deadline=time.monotonic()+600
        self.owner_password=secrets.token_hex(32);self.app_password=secrets.token_hex(32)
        self.compatibility_image=compatibility_image;self.hold_tag='nsai-owned-upgrade-compat:'+self.tag
        self.hold_created=False
        self.receipt=dict(run_id=self.tag,status='RUNNING',profile=PROFILE,sources_before=source_hashes(),
            cases=[],commands=[],production_containers_db_keys_or_volumes_selected=False,old_actual_api_compatibility=False,
            compatibility_image=compatibility_image,compatibility_scope='actual previous privacy-only application package helpers, not full HTTP API')
        self.save()
    def save(self):write(self.output/'receipt.json',self.receipt)
    def command(self,label,args,*,input=None,expected=0,timeout=60):
        remaining=self.deadline-time.monotonic()
        if remaining<=0:raise TimeoutError('Whole rehearsal deadline')
        result=subprocess.run(args,input=input,capture_output=True,timeout=min(timeout,remaining))
        self.serial+=1;stem=f'{self.serial:03d}-{label}'
        # No argv/SQL/key material is persisted. Preserve bounded real output with fixture keys redacted.
        for suffix,data in [('stdout',result.stdout),('stderr',result.stderr)]:
            for secret in (self.owner_password,self.app_password):data=data.replace(secret.encode(),b'[OWNED-CREDENTIAL-REDACTED]')
            (self.output/(stem+'-'+suffix+'.txt')).write_bytes(data)
        self.receipt['commands'].append(dict(label=label,exit_code=result.returncode,expected_exit=expected,
            stdin_sha256=digest(input)if input is not None else None,stdout_sha256=digest(result.stdout),
            stderr_sha256=digest(result.stderr),redacted_fixture_credentials=True));self.save()
        if expected is not None and result.returncode!=expected:raise RuntimeError('Owned command unexpected exit: '+label)
        return result
    def sql(self,container,sql,label='sql',expected=0):
        return self.command(label,['docker','exec','-i',container,'psql','-X','-v','ON_ERROR_STOP=1','-At','-U','nsai','-d','nsai'],input=sql.encode(),expected=expected,timeout=120).stdout.decode()
    def case(self,name,condition,details=None):
        self.receipt['cases'].append(dict(name=name,pass_=bool(condition),details=details));self.save()
        if not condition:raise AssertionError(name)
    def db(self,suffix):
        name=self.tag+'-'+suffix;self.containers.append(name)
        self.command('start-'+suffix,['docker','run','-d','--name',name,'--label','nsai.owner='+self.tag,
            '--network',self.network,'--network-alias','db','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true',
            '--user','70:70','--pids-limit','64','--cpus','.75','--memory','768m',
            '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=16m,mode=1777',
            '--tmpfs','/var/lib/postgresql/data:rw,nosuid,nodev,noexec,size=256m,mode=1777',
            '--tmpfs','/var/run/postgresql:rw,nosuid,nodev,noexec,size=8m,mode=1777',
            '--env','POSTGRES_USER=nsai','--env','POSTGRES_DB=nsai','--env','POSTGRES_PASSWORD='+self.owner_password,
            '--env','PGDATA=/var/lib/postgresql/data/pgdata',DB_IMAGE])
        for _ in range(90):
            # The entrypoint's temporary initialization server is socket-only.
            # TCP readiness identifies the final server after initialization.
            result=subprocess.run(['docker','exec',name,'pg_isready','-h','127.0.0.1','-U','nsai','-d','nsai'],capture_output=True,timeout=10)
            if result.returncode==0:break
            time.sleep(.25)
        else:raise TimeoutError('Owned database readiness')
        info=json.loads(self.command('inspect-'+suffix,['docker','inspect',name]).stdout)[0]
        # inspect output contains a synthetic fixture key; command() redacts before retention.
        policy=info['HostConfig']
        self.case('Owned '+suffix+' exact image and isolation',info['Image']==DB_IMAGE and not policy['PortBindings']
            and policy['ReadonlyRootfs'] and policy['Memory']==768*1024*1024 and policy['NanoCpus']==750000000
            and policy['PidsLimit']==64 and policy['CapDrop']==['ALL'] and 'no-new-privileges:true'in policy['SecurityOpt']
            and info['Config']['User']=='70:70')
        version=self.sql(name,'SHOW server_version;','postgres-version').strip()
        self.case('Owned '+suffix+' PostgreSQL16.15',version.startswith('16.15'),version)
        return name
    def remove(self,name,cleanup=False):
        info=json.loads(subprocess.run(['docker','inspect',name],capture_output=True,check=True).stdout)[0]
        if info['Config'].get('Labels',{}).get('nsai.owner')!=self.tag:raise RuntimeError('Refused unowned cleanup')
        if cleanup:
            subprocess.run(['docker','rm','-f',name],capture_output=True,check=True,timeout=30)
        else:self.command('remove-owned',['docker','rm','-f',name])
        self.containers.remove(name)
    def fingerprint(self,db):
        result=Stack.fingerprint(self,db)
        first=not hasattr(self,'historical_columns')
        if first:
            raw=self.sql(db,"SELECT jsonb_object_agg(table_name,columns) FROM (SELECT table_name,jsonb_agg(column_name ORDER BY ordinal_position) AS columns FROM information_schema.columns WHERE table_schema='public' GROUP BY table_name) names;",'historical-columns')
            self.historical_columns=json.loads(raw)
            write(self.output/'historical-columns.json',self.historical_columns)
        projections=[]
        for table,columns in self.historical_columns.items():
            if any(not re.fullmatch('[a-z_][a-z0-9_]*',name) for name in [table,*columns]):
                raise ValueError('Unexpected historical column identifier')
            # Explicit projection fails if any original column/table disappeared.
            projections.append("SELECT '"+table+"' AS name,(SELECT jsonb_build_object('rows',count(*),'sha256',"
                "encode(sha256(convert_to(coalesce(string_agg(to_jsonb(t)::text,E'\\n' ORDER BY to_jsonb(t)::text),'')"
                "||CASE WHEN count(*)>0 THEN E'\\n' ELSE '' END,'UTF8')),'hex')) "
                'FROM (SELECT '+','.join(columns)+' FROM public.'+table+') t) AS stamp')
        result['historical_tables']=json.loads(self.sql(db,
            'SELECT jsonb_object_agg(name,stamp) FROM ('+' UNION ALL '.join(projections)+') projections;',
            'historical-values')) if projections else {}
        if first:
            self.case('Historical column projection independently matches full baseline values',
                      result['historical_tables']==result['tables'])
        sequences={}
        for name in self.sql(db,"SELECT sequencename FROM pg_sequences WHERE schemaname='public' ORDER BY sequencename;",'sequence-names').splitlines():
            if not re.fullmatch('[a-z_][a-z0-9_]*',name):raise ValueError('Unexpected sequence identifier')
            sequences[name]=self.sql(db,'SELECT last_value,is_called FROM public.'+name+';','sequence-state').strip()
        result['sequences']=sequences
        return result
    def journal(self,db):
        raw=self.sql(db,'SELECT name,sha256 FROM nsai_schema_migrations ORDER BY name;','journal')
        return dict(line.split('|',1)for line in raw.splitlines())
    def old_image_probe(self,db,token):
        name=self.tag+'-old-client';self.containers.append(name)
        program="""import json,hashlib
from nsai import store,workflow_store
before=store.all_documents(); claims=store.all_claims()
assert len(before)==20 and len(claims)==40
assert {c['value']for c in claims}=={'75C','5mm'}
created=store.store_document('Owned compatibility source','Pump-Y operating limit is 80 C.','compatibility-only')
assert created['created']
original,media=workflow_store.original_source(created['document_id'])
assert original==b'Pump-Y operating limit is 80 C.' and media=='text/plain'
assert len(store.all_documents())==21 and len(store.all_claims())==41
print(json.dumps({'status':'PASS_SCOPED','read_documents':20,'read_claims':40,'new_document_original_sha256':hashlib.sha256(original).hexdigest(),'new_document_count':21,'new_claim_count':41,'scope':'actual pinned previous application package read/ingest/original helper only; no HTTP/auth/UI/inference/complete API compatibility'}))
"""
        result=self.command('old-image-package-probe',['docker','run','--name',name,'--label','nsai.owner='+self.tag,
            '--network',self.network,'--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true',
            '--user','10001:10001','--pids-limit','32','--cpus','.25','--memory','256m',
            '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=16m,mode=1777',
            '--env','NSAI_DB_HOST=db','--env','NSAI_DB_USER=nsai_app','--env','NSAI_DB_PASSWORD_FILE=/run/token',
            '--mount',f'type=bind,source={token},target=/run/token,readonly','--entrypoint','python',self.compatibility_image,'-c',program],timeout=90)
        self.case('Pinned previous application actual package read/write/original-source compatibility probe',json.loads(result.stdout)['status']=='PASS_SCOPED',json.loads(result.stdout))
        self.remove(name)
    def execute(self):
        try:
            for image in [DB_IMAGE,self.compatibility_image]:
                actual=self.command('pinned-image-present',['docker','image','inspect',image,'--format','{{.Id}}']).stdout.decode().strip()
                if actual!=image:raise ValueError('Local image identity mismatch')
            self.command('preserve-owned-compatibility-image',['docker','image','tag',self.compatibility_image,self.hold_tag]);self.hold_created=True
            self.command('network',['docker','network','create','--internal','--label','nsai.owner='+self.tag,self.network])
            with tempfile.TemporaryDirectory(prefix='nsai-owned-upgrade-')as tmp:
                tmp=Path(tmp);historical=historical_root(ROOT,tmp/'historical','0003_workflows.sql')
                db=self.db('upgrade');self.sql(db,migrate.migration_sql(historical)+'COMMIT;','baseline-migration')
                seed=''
                for i in range(1,21):
                    text=f'Pump-X operating limit is 75 C. Gap is 5 mm. Fixture {i}.'
                    sha=digest(text.encode())
                    seed+=f"INSERT INTO documents(id,title,source_version,sha256,raw_text,source_bytes,original_sha256,media_type) VALUES(md5('owned-doc-{i}'),'Original synthetic {i}','1','{sha}','{text}',convert_to('{text}','UTF8'),'{sha}','text/plain');\n"
                seed+="""INSERT INTO claims(id,document_id,subject,predicate,value,locator) SELECT md5('owned-claim-'||i||'-'||k),md5('owned-doc-'||i),'pump-x',CASE WHEN k=1 THEN 'operating limit' ELSE 'gap' END,CASE WHEN k=1 THEN '75C' ELSE '5mm' END,'line:1' FROM generate_series(1,20)i CROSS JOIN generate_series(1,2)k;
INSERT INTO sessions(id,owner) SELECT md5('session-'||i),'local-operator' FROM generate_series(1,10)i;
INSERT INTO session_messages(session_id,role,text,receipt) SELECT md5('session-'||i),'user','Original synthetic question','{}'::jsonb FROM generate_series(1,10)i;
INSERT INTO inference_runs(id,actor,state,details) VALUES(md5('owned-inference'),'local-operator','failed','{"reason":"original synthetic fixture; no model called"}');
UPDATE local_policy SET inference_enabled=false;
"""
                self.sql(db,seed,'populate-baseline')
                before=self.fingerprint(db);before_journal=self.journal(db);write(self.output/'baseline-fingerprint.json',before)
                self.case('Baseline journal exact historical SQL bytes',before_journal==journal_entries(historical))
                backup=self.output/'before-upgrade.sql';migrate.stream_backup(['docker','exec',db,'pg_dump','-U','nsai','-d','nsai'],backup,max_bytes=PROFILE['backup_bytes_max'],timeout=90)
                self.case('Pre-upgrade exclusive bounded backup manifest admitted',bool(admitted_backup(backup)))
                self.sql(db,migrate.migration_sql(ROOT)+migrate.role_sql(self.app_password),'populated-upgrade')
                after=self.fingerprint(db);write(self.output/'upgraded-fingerprint.json',after)
                self.case('Populated upgrade retains every historical table byte',retained_rows(before,after))
                self.case('Upgraded journal exact current SQL bytes',self.journal(db)==journal_entries(ROOT))
                self.sql(db,migrate.migration_sql(ROOT)+migrate.role_sql(self.app_password),'idempotent-upgrade')
                self.case('Repeated current migration is exact no-op',self.fingerprint(db)==after)
                original_hash=journal_entries(ROOT)['deploy/init.sql']
                self.sql(db,"UPDATE nsai_schema_migrations SET sha256='"+'0'*64+"' WHERE name='deploy/init.sql';",'dirty-fixture')
                dirty=self.fingerprint(db);result=self.command('dirty-history-refusal',['docker','exec','-i',db,'psql','-X','-v','ON_ERROR_STOP=1','-At','-U','nsai','-d','nsai'],input=(migrate.migration_sql(ROOT)+migrate.role_sql(self.app_password)).encode(),expected=None)
                self.case('Dirty history refused without committed mutation',result.returncode!=0 and b'Applied migration hash mismatch'in result.stderr and self.fingerprint(db)==dirty)
                self.sql(db,"UPDATE nsai_schema_migrations SET sha256='"+original_hash+"' WHERE name='deploy/init.sql';",'restore-owned-journal-hash')
                self.sql(db,"INSERT INTO nsai_schema_migrations(name,sha256) VALUES('unknown_owned_fixture.sql','"+'1'*64+"');",'unknown-fixture')
                unknown=self.fingerprint(db);result=self.command('unknown-history-refusal',['docker','exec','-i',db,'psql','-X','-v','ON_ERROR_STOP=1','-At','-U','nsai','-d','nsai'],input=(migrate.migration_sql(ROOT)+migrate.role_sql(self.app_password)).encode(),expected=None)
                self.case('Unknown history refused without committed mutation',result.returncode!=0 and b'unknown entries'in result.stderr and self.fingerprint(db)==unknown)
                self.sql(db,"DELETE FROM nsai_schema_migrations WHERE name='unknown_owned_fixture.sql';",'remove-owned-test-row')
                failure=historical_root(ROOT,tmp/'failure','9999.sql');(failure/'database/migrations/9999_owned_failure.sql').write_text('CREATE TABLE owned_rollback_probe(id int); INSERT INTO owned_rollback_probe VALUES(1); SELECT 1/0;')
                before_failure=self.fingerprint(db);result=self.command('transactional-failure',['docker','exec','-i',db,'psql','-X','-v','ON_ERROR_STOP=1','-At','-U','nsai','-d','nsai'],input=(migrate.migration_sql(failure)+migrate.role_sql(self.app_password)).encode(),expected=None)
                self.case('Later migration failure atomically rolls back DDL data journal',result.returncode!=0 and b'division by zero'in result.stderr and self.fingerprint(db)==before_failure)
                token=tmp/'app-token';token.write_text(self.app_password)
                self.old_image_probe(db,token)
                final=self.fingerprint(db);write(self.output/'final-fingerprint.json',final)
                current_backup=self.output/'upgraded.sql';migrate.stream_backup(['docker','exec',db,'pg_dump','-U','nsai','-d','nsai'],current_backup,max_bytes=PROFILE['backup_bytes_max'],timeout=90)
                manifest=admitted_backup(current_backup);self.case('Upgraded backup manifest admitted',bool(manifest))
                peak=self.command('source-memory-peak',['docker','exec',db,'cat','/sys/fs/cgroup/memory.peak']).stdout.decode().strip();self.receipt['source_cgroup_memory_peak_bytes']=int(peak)
                self.remove(db) # One database at a time; restores never access the source container.
                restore=self.db('restore')
                self.sql(restore,"CREATE ROLE nsai_app LOGIN PASSWORD '"+self.app_password+"';",'restore-role-bootstrap')
                self.command('restore-actual-dump',['docker','exec','-i',restore,'psql','-X','-v','ON_ERROR_STOP=1','-U','nsai','-d','nsai'],input=current_backup.read_bytes(),timeout=120)
                self.sql(restore,'BEGIN;'+migrate.role_sql(self.app_password),'restore-privilege-contract')
                restored=self.fingerprint(restore);write(self.output/'restored-fingerprint.json',restored)
                self.case('Second fresh database restore exact rows indexes triggers ACL role policy',restored==final)
                self.sql(restore,migrate.migration_sql(ROOT)+migrate.role_sql(self.app_password),'restored-migration-noop')
                self.case('Restored database migration exact no-op',self.fingerprint(restore)==restored)
                self.remove(restore)
                rollback=self.db('pre-upgrade-rollback')
                admitted_backup(backup)
                self.command('restore-pre-upgrade-dump',['docker','exec','-i',rollback,'psql','-X','-v','ON_ERROR_STOP=1','-U','nsai','-d','nsai'],input=backup.read_bytes(),timeout=120)
                rollback_state=self.fingerprint(rollback);write(self.output/'pre-upgrade-restored-fingerprint.json',rollback_state)
                self.case('Pre-upgrade backup actual rollback restores exact historical state',rollback_state==before)
                self.sql(rollback,migrate.migration_sql(historical)+'COMMIT;','rollback-historical-noop')
                self.case('Restored historical journal admitted by exact historical migrator',self.journal(rollback)==before_journal)
                self.receipt['sources_after']=source_hashes();self.case('Host migration/helper/runner sources unchanged',self.receipt['sources_before']==self.receipt['sources_after'])
                self.receipt.update(status='PASS_SCOPED',completed_at=datetime.now(timezone.utc).isoformat(),limitations=[
                    'Historical baseline is original current init+0002+0003 bytes, not an archived deployed schema artifact.',
                    'Actual pinned previous privacy-only application package read/ingest/original probe only; no complete old HTTP/auth/UI/inference compatibility claim.',
                    'No source backfill for arbitrary legacy null original bytes; no real user data, concurrent application snapshot, PITR, disk-full or maximum-capacity proof.',
                    'No destructive downgrade executed. Actual pre-upgrade rollback restores retained backup into a third sequential fresh database; no live rollback.',
                    'No live deployment, credential rotation, card acceptance or release certification.'])
        except Exception as error:
            detail=traceback.format_exc()
            for secret in (self.owner_password,self.app_password):detail=detail.replace(secret,'[OWNED-CREDENTIAL-REDACTED]')
            (self.output/'failure-traceback.txt').write_text(detail[-16000:],encoding='utf-8')
            self.receipt.update(status='FAIL',failure_type=type(error).__name__,failure_traceback='failure-traceback.txt')
        finally:
            self.cleanup()
            if not self.receipt['cleanup_complete']:self.receipt['status']='FAIL_CLEANUP'
            self.save()
            write(self.output/'artifact-manifest.json',{'files':{p.name:digest(p.read_bytes())for p in self.output.iterdir()if p.is_file()and p.name!='artifact-manifest.json'}})
        return self.receipt
    def cleanup(self):
        records=[]
        for name in list(reversed(self.containers)):
            try:self.remove(name,cleanup=True);records.append(dict(container=name,removed=True))
            except Exception as error:records.append(dict(container=name,removed=False,error_type=type(error).__name__))
        result=subprocess.run(['docker','network','inspect',self.network],capture_output=True)
        if result.returncode==0:
            info=json.loads(result.stdout)[0]
            if info.get('Labels',{}).get('nsai.owner')!=self.tag:raise RuntimeError('Unowned network cleanup refused')
            result=subprocess.run(['docker','network','rm',self.network],capture_output=True);records.append(dict(network=self.network,removed=result.returncode==0))
        remaining=subprocess.run(['docker','ps','-aq','--filter','label=nsai.owner='+self.tag],capture_output=True)
        nets=subprocess.run(['docker','network','ls','-q','--filter','label=nsai.owner='+self.tag],capture_output=True)
        hold_removed=True
        if self.hold_created:
            inspected=subprocess.run(['docker','image','inspect',self.hold_tag,'--format','{{.Id}}'],capture_output=True,timeout=30)
            if inspected.returncode==0 and inspected.stdout.decode().strip()==self.compatibility_image:
                untag=subprocess.run(['docker','image','rm',self.hold_tag],capture_output=True,timeout=30);hold_removed=untag.returncode==0
            else:hold_removed=False
            records.append(dict(owned_hold_tag=self.hold_tag,removed=hold_removed,original_image_not_removed=True))
        self.receipt.update(cleanup=records,cleanup_complete=hold_removed and remaining.returncode==0 and nets.returncode==0 and not remaining.stdout.strip()and not nets.stdout.strip())

def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--compatibility-image',default=API_IMAGE);args=parser.parse_args()
    root=ROOT/'evidence/implementation/upgrade-recovery';root.mkdir(parents=True,exist_ok=True)
    run=Rehearsal(root,args.compatibility_image);receipt=run.execute();write(root/'current.json',dict(run_id=run.tag,status=receipt['status'],receipt=(run.output/'receipt.json').relative_to(root).as_posix()))
    print(json.dumps(dict(run_id=run.tag,status=receipt['status'],cases=len(receipt['cases']),cleanup_complete=receipt['cleanup_complete'])))
    return 0 if receipt['status']=='PASS_SCOPED'and receipt['cleanup_complete']else 1

if __name__=='__main__':raise SystemExit(main())
