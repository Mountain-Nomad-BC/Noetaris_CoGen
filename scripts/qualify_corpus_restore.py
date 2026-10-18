"""Quiescent owned-corpus recovery; never accepts live resource names."""
import hashlib
import json
from pathlib import Path
import re
import secrets
import subprocess
import time
import migrate
import sys
from recovery_sequences import sequence_state

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from nsai.schema_contract import ACCESS_DEFINITIONS_SQL


def fingerprint(stack,container):
    if container not in stack.containers:raise ValueError('Unowned fingerprint target')
    tables={}
    for name in stack.sql(container,"SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;").splitlines():
        if re.fullmatch('[a-z_][a-z0-9_]*',name) is None:raise ValueError('Unexpected table identifier')
        query="SELECT count(*)::text||'|'||encode(sha256(convert_to(coalesce(string_agg(h,'' ORDER BY h),''),'UTF8')),'hex') FROM (SELECT encode(sha256(convert_to(to_jsonb(t)::text,'UTF8')),'hex') h FROM public."+name+' t) row_digests;'
        count,digest=stack.sql(container,query).strip().split('|')
        tables[name]=dict(rows=int(count),multiset_sha256=digest)
    sequences=sequence_state(lambda sql:stack.sql(container,sql))
    return dict(tables=tables,sequences=sequences)


def verify_restore(stack,root,db,network,db_secret,expected,folder):
    if db not in stack.containers or network not in stack.networks:raise ValueError('Unowned recovery source')
    before=fingerprint(stack,db)
    definitions_before=json.loads(stack.sql(db,ACCESS_DEFINITIONS_SQL))
    (folder/'access-before-restore.json').write_text(json.dumps(definitions_before,indent=2)+'\n',encoding='utf-8')
    backup_folder=root/'state/arxiv-corpus'/folder.name;backup_folder.mkdir(parents=True,exist_ok=False)
    backup=backup_folder/'postgres.dump'
    migrate.stream_backup(['docker','exec',db,'pg_dump','--format=custom','--compress=6','--no-owner','-U','nsai','-d','nsai'],backup,max_bytes=128*1024*1024,timeout=120)
    capture=json.loads(backup.with_suffix('.dump.manifest.json').read_bytes())
    if backup.stat().st_size!=capture['size_bytes'] or hashlib.sha256(backup.read_bytes()).hexdigest()!=capture['sha256']:
        raise ValueError('Backup custody mismatch')
    restored=stack.run('restore',stack.db_image,['--tmpfs','/var/lib/postgresql/data:rw,nosuid,nodev,size=1024m,mode=1777',
        '--tmpfs','/var/run/postgresql:rw,nosuid,nodev,size=8m,mode=1777','-e','POSTGRES_USER=nsai','-e','POSTGRES_DB=nsai',
        '-e','POSTGRES_PASSWORD='+secrets.token_hex(32),'-e','PGDATA=/var/lib/postgresql/data/pgdata'],
        network=network,alias='restored-db',user='70:70',memory='1536m',pids='128')
    for _ in range(120):
        probe=subprocess.run(['docker','exec',restored,'pg_isready','-h','127.0.0.1','-U','nsai'],capture_output=True,timeout=5)
        if probe.returncode==0:break
        time.sleep(.1)
    else:raise RuntimeError('Owned restored database readiness deadline')
    # Policy definitions refer to this cluster role even when pg_restore omits
    # ACLs and ownership. A fresh PostgreSQL cluster does not contain it.
    application_password=db_secret.read_text(encoding='utf-8')
    if re.fullmatch('[a-f0-9]{64}',application_password) is None:raise ValueError('Unexpected owned database credential syntax')
    stack.sql(restored,"CREATE ROLE nsai_app LOGIN PASSWORD '"+application_password+
        "' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;")
    with backup.open('rb') as source:
        loaded=subprocess.run(['docker','exec','-i',restored,'pg_restore','--exit-on-error','--no-owner','-U','nsai','-d','nsai'],stdin=source,capture_output=True,timeout=180)
    (folder/'restore-stderr.txt').write_bytes(loaded.stderr)
    if loaded.returncode:raise RuntimeError('Owned corpus restore failed')
    stack.sql(restored,migrate.role_sql(application_password))
    after=fingerprint(stack,restored)
    definitions_after=json.loads(stack.sql(restored,ACCESS_DEFINITIONS_SQL))
    (folder/'access-after-restore.json').write_text(json.dumps(definitions_after,indent=2)+'\n',encoding='utf-8')
    (folder/'logical-before-restore.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
    (folder/'logical-after-restore.json').write_text(json.dumps(after,indent=2)+'\n',encoding='utf-8')
    if before!=after:raise ValueError('Restored table bytes, rows or sequence state differ')
    if definitions_before!=definitions_after:raise ValueError('Restored authorization definitions or ACLs differ')
    program="""import hashlib,json,os,sys
sys.path.insert(0,'/')
from pathlib import Path
from nsai import store,security,workflow_store,semantic_jobs,research_store,api
from semantic_fixture_helpers import configure_authority
configure_authority()
alice=security.resolve_principal('Bearer '+Path('/tmp/fixture-user-alice').read_text())
expected=json.loads(os.environ['NSAI_EXPECTED_ORIGINALS'])
with store.identity_context(alice):
 for row in expected:
  data,media=workflow_store.original_source(row['document_id'])
  assert media=='application/pdf' and hashlib.sha256(data).hexdigest()==row['original_sha256']
  assert semantic_jobs.source_status(row['document_id'])['ready']
  artifact=research_store.get(row['document_id'])
  assert artifact['source_sha256']==row['original_sha256']
 assert api.documents(limit=25,cursor=None,q=None,identity=alice)['total']==len(expected)
bob=security.resolve_principal('Bearer '+Path('/tmp/fixture-user-bob').read_text())
with store.identity_context(bob):assert api.documents(limit=25,cursor=None,q=None,identity=bob)['total']==0
print(json.dumps(dict(status='PASS_SCOPED',originals_rehashed=len(expected),all_publications_ready=True,private_isolation_retained=True)))
"""
    client=stack.run('restore-client',stack.api_image,['--mount','type=bind,source='+str(db_secret)+',target=/run/secrets/db,readonly',
        '--mount','type=bind,source='+str(root/'tests/semantic_fixture_helpers.py')+',target=/semantic_fixture_helpers.py,readonly',
        '-e','NSAI_DB_HOST=restored-db','-e','NSAI_DB_USER=nsai_app','-e','NSAI_DB_NAME=nsai','-e','NSAI_DB_PASSWORD_FILE=/run/secrets/db',
        '-e','NSAI_EXPECTED_ORIGINALS='+json.dumps(expected,separators=(',',':')),'--entrypoint','python'],
        ['-c',program],network=network,memory='512m',pids='64')
    waited=subprocess.run(['docker','wait',client],capture_output=True,timeout=120)
    output=subprocess.run(['docker','logs',client],capture_output=True,timeout=30)
    (folder/'restore-client-output.json').write_bytes(output.stdout);(folder/'restore-client-stderr.txt').write_bytes(output.stderr)
    if waited.returncode or waited.stdout.strip()!=b'0':raise RuntimeError('Restored corpus application check failed')
    result=json.loads(output.stdout.strip().splitlines()[-1])
    return dict(status='PASS_SCOPED',fresh_container=True,logical_tables_and_sequences_equal=True,
        authorization_definitions_and_acls_equal=True,
        application=result,backup=dict(path=backup.relative_to(root).as_posix(),**capture),
        scope='Quiescent owned development corpus; no concurrent-write backup, PITR, RTO/RPO or disaster-recovery acceptance')
