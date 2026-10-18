"""Focused operational regression checks; no Docker daemon or production state writes."""
import importlib.util
from pathlib import Path
import subprocess
import json
import sys
from unittest.mock import patch
import pytest
ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    module=importlib.util.module_from_spec(spec)
    # Match a direct script invocation without relying on another collected
    # test module to have added the scripts directory globally.
    with patch.object(sys,'path',[str(ROOT/'scripts'),*sys.path]):spec.loader.exec_module(module)
    return module

def test_imports_do_not_start_commands(monkeypatch):
    def forbidden(*args,**kwargs): raise AssertionError('Import started an operational command')
    monkeypatch.setattr(subprocess,'run',forbidden)
    monkeypatch.setattr(subprocess,'Popen',forbidden)
    for name in ('migrate','inspect_runtime','record_verification','check_compose',
                 'bootstrap_secrets','verify_persistence','check_secret_hygiene','demo_seed',
                 'lock_runtime','summarize_image_scans','task_cli','validate_compose_security',
                 'verify_kit_integrity','verify_local','verify_session_isolation','verify_browser',
                 'implementation_integration_harness','verify_recovery','qualification_shards','backfill_legacy_library'): load(name)


@pytest.mark.parametrize('state',['foreign-owner','daemon-unavailable','already-absent','owned'])
def test_recovery_cleanup_removes_only_proven_owned_container(monkeypatch,state):
    module=load('verify_recovery');calls=[]
    def run(args,**kwargs):
        calls.append(args)
        if args[1]=='inspect':
            if state in {'daemon-unavailable','already-absent'}:return subprocess.CompletedProcess(args,1,b'',b'')
            label='another-run' if state=='foreign-owner' else 'our-run'
            return subprocess.CompletedProcess(args,0,json.dumps([dict(Config=dict(Labels={'nsai.owner':label}))]).encode(),b'')
        if args[1]=='ps':return subprocess.CompletedProcess(args,1 if state=='daemon-unavailable' else 0,b'',b'')
        return subprocess.CompletedProcess(args,0,b'',b'')
    monkeypatch.setattr(module.subprocess,'run',run)
    assert module.cleanup_owned('nsai-recovery-our-run','our-run') is (state in {'already-absent','owned'})
    assert any(args[1]=='rm' for args in calls) is (state=='owned')

def test_direct_migration_denied_before_any_secret_backup_or_database_access(monkeypatch,tmp_path):
    module=load('migrate');module.ROOT=tmp_path
    calls=[]
    def deny(args,**kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args,1)
    monkeypatch.setattr(subprocess,'run',deny)
    monkeypatch.setattr(module,'stream_backup',lambda *a,**k:pytest.fail('Backup before admission'))
    with pytest.raises(SystemExit,match='Migration denied'):
        module.main()
    assert calls==[[sys.executable,str(tmp_path/'scripts/check_release_readiness.py')]]
    assert list(tmp_path.iterdir())==[]


def test_legacy_backfill_denied_before_any_container_or_data_access(monkeypatch,tmp_path):
    module=load('backfill_legacy_library');module.ROOT=tmp_path;calls=[]
    def deny(args,**kwargs):
        calls.append(args);return subprocess.CompletedProcess(args,1)
    monkeypatch.setattr(module.subprocess,'run',deny)
    with pytest.raises(SystemExit,match='Legacy preparation denied'):module.main([])
    assert calls==[[sys.executable,str(tmp_path/'scripts/check_release_readiness.py')]]

def test_command_recorder_never_replaces_reviewed_public_projection(monkeypatch,tmp_path):
    module=load('record_verification');module.ROOT=tmp_path
    (tmp_path/'assets').mkdir()
    reviewed=tmp_path/'assets/verification.json';reviewed.write_bytes(b'reviewed projection fixture')
    monkeypatch.setattr(subprocess,'run',lambda args,**kwargs:subprocess.CompletedProcess(args,0,'synthetic command output',''))
    assert module.main()==1  # Missing independent evidence never becomes PASS.
    assert reviewed.read_bytes()==b'reviewed projection fixture'
    private=json.loads((tmp_path/'evidence/raw/verification-receipts.json').read_text())
    assert private['overall_status']=='FAIL'
    assert private['certification'] is False and private['publication_reviewed'] is False

def test_missing_runtime_services_fail_closed(monkeypatch,tmp_path):
    module=load('inspect_runtime')
    expected={name:{'networks':{'fixture-net':True}} for name in module.CPU}
    monkeypatch.setattr(module,'expected_policy',lambda *args:expected)
    def docker(arguments):
        if arguments[0]=='compose':return json.dumps({'name':'fixture'})
        if arguments[0]=='ps':return ''
        if arguments[0]=='network':return json.dumps([{'Name':'fixture-net','Internal':True}])
        raise AssertionError('No container inspect is admitted when required services are absent')
    monkeypatch.setattr(module,'docker',docker)
    target=tmp_path/'runtime.json'
    assert module.main(['--output',str(target)])==1
    report=json.loads(target.read_text())
    assert report['status']=='FAIL' and report['services']==[]
    assert all(name+': required container missing' in report['errors'] for name in module.CPU)
    assert report['secret_contents_included'] is False

def test_empty_effective_compose_rejected():
    assert 'unexpected or missing active services' in load('check_compose').validate({})


@pytest.mark.parametrize('probe',[
    ['CMD','pg_isready','-h','127.0.0.1','-U','nsai','-d','nsai'],
    ['CMD-SHELL','pg_isready -U nsai -d nsai'], None,
])
def test_compose_requires_final_tcp_database_readiness(probe):
    module=load('check_compose')
    errors=module.validate(dict(services=dict(db=dict(healthcheck=dict(test=probe)))))
    assert ('db: final TCP readiness probe required' in errors)==(probe!=module.DB_READY)


def test_owned_database_waits_for_final_tcp_listener(monkeypatch):
    module=load('qualify_local_stack');stack=module.Stack.__new__(module.Stack)
    stack.db_image='owned-test-image';stack.run=lambda *args,**kwargs:'owned-test-db'
    probes=[]
    def run(args,**kwargs):
        probes.append(args)
        # The temporary initializer already accepts sockets; the final TCP
        # listener becomes available on the second bounded polling attempt.
        code=1 if '-h' in args and len(probes)==1 else 0
        return subprocess.CompletedProcess(args,code)
    monkeypatch.setattr(module.subprocess,'run',run)
    monkeypatch.setattr(module.time,'sleep',lambda seconds:None)
    assert stack.db('test','owned-network','fixture-password')=='owned-test-db'
    assert len(probes)==2 and all(args[args.index('-h')+1]=='127.0.0.1' for args in probes)

def test_backup_exclusive_stream_hash_and_manifest(tmp_path):
    module=load('migrate');target=tmp_path/'snapshot.sql'
    module.stream_backup([sys.executable,'-c',"import sys;sys.stdout.buffer.write(b'original backup')"],target)
    assert target.read_bytes()==b'original backup'
    assert target.with_suffix('.sql.manifest.json').exists()
    with pytest.raises(FileExistsError): module.stream_backup([sys.executable,'-c',"print('replacement')"],target)
    assert target.read_bytes()==b'original backup'

def test_backup_limit_rejects_and_cleans_partial(tmp_path):
    target=tmp_path/'oversized.sql'
    with pytest.raises(RuntimeError): load('migrate').stream_backup([sys.executable,'-c',"import sys;sys.stdout.buffer.write(b'x'*10000)"],target,max_bytes=100)
    assert not target.exists() and not target.with_suffix('.sql.partial').exists()

def test_backup_timeout_cancels(tmp_path):
    target=tmp_path/'slow.sql'
    with pytest.raises(RuntimeError,match='budget'): load('migrate').stream_backup([sys.executable,'-c','import time;time.sleep(5)'],target,timeout=.1)
    assert not target.exists()

def test_startup_observational_and_tests_before_migration():
    source=(ROOT/'scripts/start-cpu.ps1').read_text()
    assert source.index('-m pytest')<source.index('scripts/migrate.py')
    assert '--readiness-only' in source and 'verify_system.py --model' not in source
    assert 'protect-secrets.ps1' in source

def test_legacy_launchers_do_not_pull_or_skip_parser():
    for name in ('start.ps1','local-ai-start.ps1'):
        assert 'start-cpu.ps1' in (ROOT/'scripts'/name).read_text()
    for name in ('first-run.sh','local-ai-start.sh'):
        text=(ROOT/'scripts'/name).read_text()
        assert 'exit 2' in text and 'docker compose up' not in text

def test_migration_revokes_previous_authority():
    source=(ROOT/'scripts/migrate.py').read_text()
    for contract in ('NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS','pg_auth_members','REVOKE ALL ON ALL TABLES','REVOKE ALL ON ALL SEQUENCES'):
        assert contract in source

def test_acl_replaces_existing_grants_including_children():
    source=(ROOT/'scripts/protect-secrets.ps1').read_text()
    assert 'DirectorySecurity' in source and 'FileSecurity' in source
    assert 'Get-ChildItem' in source and 'state/backups' in source
    assert 'SetAccessRuleProtection($true, $false)' in source
    assert 'Set-Acl -LiteralPath $item.FullName' in source
    assert 'Get-Acl -LiteralPath $item.FullName' in source
    assert 'Private ACL principal or permission verification failed.' in source


def test_ordered_migrations_and_dirty_hash_admission(tmp_path):
    (tmp_path/'deploy').mkdir(); (tmp_path/'database/migrations').mkdir(parents=True)
    (tmp_path/'deploy/init.sql').write_text('CREATE TABLE sample(id int);')
    (tmp_path/'database/migrations/0004.sql').write_text('ALTER TABLE sample ADD COLUMN extra int;')
    (tmp_path/'database/migrations/0002.sql').write_text('ALTER TABLE sample ADD COLUMN old int;')
    sql=load('migrate').migration_sql(tmp_path)
    assert sql.index('0002.sql')<sql.index('0004.sql')
    assert 'pg_advisory_xact_lock' in sql and 'Applied migration hash mismatch' in sql
    assert 'Migration history contains unknown entries' in sql
    assert sql.startswith('BEGIN;') and 'COMMIT;' not in sql
    assert '\\gset' in sql and '\\if :migration_needed' in sql
    assert sql.count('INSERT INTO nsai_schema_migrations')==3

def test_backup_limit_never_writes_over_budget(tmp_path,monkeypatch):
    # A fast writer must not race ahead of a polling filesystem-size check.
    target=tmp_path/'fast.sql'
    with pytest.raises(RuntimeError,match='size budget'):
        load('migrate').stream_backup([sys.executable,'-c',"import sys;sys.stdout.buffer.write(b'x'*10000000)"],target,max_bytes=65536)
    assert not target.exists() and not target.with_suffix('.sql.partial').exists()

def test_backup_preserves_existing_manifest_without_starting_capture(tmp_path,monkeypatch):
    module=load('migrate');target=tmp_path/'snapshot.sql'
    manifest=target.with_suffix('.sql.manifest.json');manifest.write_bytes(b'previous manifest')
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**k:pytest.fail('Capture started despite existing manifest'))
    with pytest.raises(FileExistsError):module.stream_backup(['unused'],target)
    assert manifest.read_bytes()==b'previous manifest' and not target.exists()
    assert not target.with_suffix('.sql.partial').exists()

def test_backup_disk_failure_does_not_publish_partial_capture(tmp_path,monkeypatch):
    module=load('migrate');target=tmp_path/'snapshot.sql'
    def fail_fsync(fd):raise OSError('Synthetic full disk')
    monkeypatch.setattr(module.os,'fsync',fail_fsync)
    with pytest.raises(OSError,match='Synthetic full disk'):
        module.stream_backup([sys.executable,'-c',"print('synthetic backup')"],target)
    assert not target.exists() and not target.with_suffix('.sql.partial').exists()
    assert not target.with_suffix('.sql.manifest.json').exists()

def test_manifest_finalization_failure_keeps_sql_without_success_manifest(tmp_path,monkeypatch):
    module=load('migrate');target=tmp_path/'snapshot.sql'
    original=module.os.fsync;calls=[]
    def fail_manifest(fd):
        calls.append(fd)
        if len(calls)==2:raise OSError('Synthetic manifest disk failure')
        original(fd)
    monkeypatch.setattr(module.os,'fsync',fail_manifest)
    with pytest.raises(OSError,match='manifest disk failure'):
        module.stream_backup([sys.executable,'-c',"print('synthetic backup')"],target)
    assert target.read_bytes().strip()==b'synthetic backup'
    assert not target.with_suffix('.sql.manifest.json').exists()
    assert not list(tmp_path.glob('*.partial'))

def test_concurrent_backups_have_independent_exact_content_and_manifests(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import hashlib
    module=load('migrate')
    def capture(number):
        target=tmp_path/f'snapshot-{number}.sql';content=f'synthetic-{number}'
        module.stream_backup([sys.executable,'-c',f'print({content!r})'],target)
        manifest=json.loads(target.with_suffix('.sql.manifest.json').read_text())
        assert target.read_bytes().strip()==content.encode()
        assert manifest['sha256']==hashlib.sha256(target.read_bytes()).hexdigest()
        assert manifest['restore_verified'] is False
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(capture,range(4)))
    assert not list(tmp_path.glob('*.partial'))
