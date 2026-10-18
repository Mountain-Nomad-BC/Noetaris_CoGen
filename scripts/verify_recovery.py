"""Restore a real backup into a networkless disposable DB; never restore over the live volume."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import subprocess
import time
import tempfile
import re
import sys
import secrets
from uuid import uuid4
from migrate import stream_backup
from recovery_sequences import sequence_state

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from nsai.schema_contract import ACCESS_DEFINITIONS_SQL
DB_IMAGE='sha256:e8d60b4d26e679424148c662d01229c05d0d661745d846e7911af78b88bd9f6d'

def command(args,**kwargs):
    result=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=120,**kwargs)
    if result.returncode:raise RuntimeError('Recovery command failed: '+args[0]+' '+args[1]+' (credential/error contents withheld)')
    return result.stdout

def fingerprint(prefix, *, max_bytes=256*1024*1024):
    if type(max_bytes) is not int or not 1<=max_bytes<=256*1024*1024:
        raise ValueError('Invalid fingerprint byte budget')
    # Hash every complete row, retaining the existing COPY representation.
    values={}
    names=command(prefix+['psql','-X','-At','-v','ON_ERROR_STOP=1','-U','nsai','-d','nsai','-c',
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"]).decode().splitlines()
    for table in names:
        if re.fullmatch('[a-z_][a-z0-9_]*',table) is None:raise ValueError('Unexpected table identifier')
        sql=f"SET statement_timeout='120s'; SET temp_file_limit='256MB'; COPY (SELECT row_to_json(t)::text FROM {table} t ORDER BY row_to_json(t)::text) TO STDOUT"
        digest=hashlib.sha256(); rows=0
        # Enforce the disk bound while bytes arrive, before publication. The
        # shared bounded stream also kills/reaps a failed producer and removes
        # its partial capture. Scratch files are private to this table check.
        with tempfile.TemporaryDirectory(prefix='nsai-recovery-fingerprint-') as temporary:
            target=Path(temporary)/'rows.copy'
            stream_backup(prefix+['psql','-X','-U','nsai','-d','nsai','-q','-v','ON_ERROR_STOP=1','-c',sql],
                target,max_bytes=max_bytes,timeout=125)
            with target.open('rb') as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):
                    digest.update(block);rows+=block.count(b'\n')
        values[table]=dict(rows=rows,sha256=digest.hexdigest())
    return values


def access_and_sequences(prefix):
    def query(sql):return command(prefix+['psql','-X','-At','-v','ON_ERROR_STOP=1','-U','nsai','-d','nsai','-c',sql]).decode().strip()
    return dict(access=json.loads(query(ACCESS_DEFINITIONS_SQL)),
        sequences=sequence_state(query))


def cleanup_owned(name,owner):
    found=subprocess.run(['docker','inspect',name],capture_output=True,timeout=30)
    if found.returncode:
        remaining=subprocess.run(['docker','ps','-a','--filter','name=^/'+re.escape(name)+'$','--format','{{.Names}}'],capture_output=True,timeout=30)
        return remaining.returncode==0 and not remaining.stdout.strip()
    metadata=json.loads(found.stdout)[0]
    if metadata['Config'].get('Labels',{}).get('nsai.owner')!=owner:return False
    return subprocess.run(['docker','rm','--force',name],capture_output=True,timeout=30).returncode==0


def main():
    run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:8]
    name='nsai-recovery-'+run.lower()
    evidence=ROOT/'evidence/recovery'/run;evidence.mkdir(parents=True,exist_ok=False)
    backup_root=ROOT/'state/backups';backup_root.mkdir(parents=True,exist_ok=True)
    backup_file=backup_root/(run+'.dump')
    
    live=['docker','compose','exec','-T','db']
    before=fingerprint(live)
    access_before=access_and_sequences(live)
    stream_backup(live+['pg_dump','-U','nsai','-d','nsai','--format=custom'],backup_file)
    after_backup=fingerprint(live)
    if before!=after_backup or access_before!=access_and_sequences(live):raise SystemExit('Concurrent DB changes observed; snapshot comparison not stable. Backup retained; retry in a quiet window.')
    report=dict(run_id=run,status='PENDING',database_image=DB_IMAGE,backup_file=str(backup_file.relative_to(ROOT)),backup_sha256=json.loads(backup_file.with_suffix('.dump.manifest.json').read_text())['sha256'],
        live_database_overwritten=False,target_network='none',target_storage='ephemeral tmpfs',fingerprints=before)
    try:
        command(['docker','run','--detach','--name',name,'--label','nsai.owner='+run,
            '--network','none','--memory','1g','--cpus','1','--pids-limit','128','--security-opt','no-new-privileges:true',
            '--cap-drop','ALL','--read-only','--user','70:70',
            '--tmpfs','/var/lib/postgresql/data:rw,nosuid,nodev,size=512m,mode=1777','--tmpfs','/var/run/postgresql:rw,nosuid,nodev,size=8m,mode=1777',
            '--env','POSTGRES_USER=nsai','--env','POSTGRES_DB=nsai','--env','POSTGRES_PASSWORD='+secrets.token_hex(32),
            '--env','PGDATA=/var/lib/postgresql/data/pgdata',DB_IMAGE])
        for _ in range(30):
            probe=subprocess.run(['docker','exec',name,'pg_isready','-h','127.0.0.1','-U','nsai','-d','nsai'],capture_output=True,timeout=30)
            if probe.returncode==0:break
            time.sleep(1)
        else:raise RuntimeError('Isolated recovery DB did not become ready')
        # Cluster roles are absent from a database-only dump. This diagnostic
        # role resolves restored policy/ACL references; it is intentionally not
        # an application login or application-recovery acceptance.
        command(['docker','exec',name,'psql','-X','-v','ON_ERROR_STOP=1','-U','nsai','-d','nsai','-c',
            'CREATE ROLE nsai_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;'])
        manifest=json.loads(backup_file.with_suffix('.dump.manifest.json').read_bytes())
        if (backup_file.is_symlink() or type(manifest.get('size_bytes')) is not int
            or not 0<backup_file.stat().st_size<=64*1024*1024 or backup_file.stat().st_size!=manifest['size_bytes']
            or hashlib.sha256(backup_file.read_bytes()).hexdigest()!=manifest['sha256']):
            raise ValueError('Backup custody admission failed')
        with backup_file.open('rb') as stream:
            command(['docker','exec','-i',name,'pg_restore','-U','nsai','-d','nsai','--exit-on-error','--no-owner'],stdin=stream)
        restored=fingerprint(['docker','exec',name])
        if restored!=before:raise ValueError('Restored row fingerprints differ')
        access_restored=access_and_sequences(['docker','exec',name])
        if access_restored!=access_before:raise ValueError('Restored access definitions, ACLs or sequences differ')
        report.update(status='PASS_SCOPED',restored_fingerprints=restored,all_public_tables_match=True,
            access_definitions_acls_and_sequences_match=True,application_recovery_qualified=False,
            scope='Quiescent database rows, access definitions and sequences only; no application login/restart, role-state, crash or concurrent-write recovery acceptance')
    except Exception as error:
        report.update(status='FAIL',error=str(error));raise
    finally:
        # Only this uniquely named, owned tmpfs test container is stopped; no user volumes are removed.
        report['disposable_container_removed']=cleanup_owned(name,run)
        if not report['disposable_container_removed']:report['status']='FAIL_CLEANUP'
        (evidence/'receipt.json').write_text(json.dumps(report,indent=2))
    if report['status']!='PASS_SCOPED':raise RuntimeError('Owned recovery cleanup incomplete')
    print('Scoped recovery check passed: all public tables, access definitions, ACLs and sequences match. Application recovery remains unqualified; live DB was not overwritten.')

if __name__ == "__main__":
    main()
