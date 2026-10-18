"""Independent negative custody and retained-data expectations for the owned rehearsal."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import pytest

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
spec=importlib.util.spec_from_file_location('upgrade_rehearsal',SCRIPTS/'qualify_upgrade_recovery.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def test_import_is_observational(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('Import tried to select external resources')
    monkeypatch.setattr(module.subprocess,'run',forbidden)
    again=importlib.util.module_from_spec(spec);spec.loader.exec_module(again)

def test_additive_tables_do_not_mask_old_data_change():
    before={'tables':{'documents':{'rows':20,'sha256':'original'},'nsai_schema_migrations':{'rows':3,'sha256':'old'}}}
    after={'tables':{'documents':{'rows':20,'sha256':'mutated'},'nsai_schema_migrations':{'rows':5,'sha256':'new'},'new':{'rows':0}}}
    assert not module.retained_rows(before,after)
    after['tables']['documents']=before['tables']['documents']
    assert module.retained_rows(before,after)


def test_additive_columns_use_original_projection_without_masking_mutation():
    original=dict(rows=2,sha256='original values')
    before=dict(tables={'documents':original})
    after=dict(tables={'documents':dict(rows=2,sha256='includes new default columns')},historical_tables={'documents':original})
    assert module.retained_rows(before,after)
    after['historical_tables']['documents']=dict(rows=2,sha256='changed original value')
    assert not module.retained_rows(before,after)
    after['historical_tables'].clear()
    assert not module.retained_rows(before,after)

def test_historical_sql_copies_exact_bytes_and_excludes_later_migrations(tmp_path):
    source=tmp_path/'source';(source/'deploy').mkdir(parents=True);(source/'database/migrations').mkdir(parents=True)
    (source/'deploy/init.sql').write_bytes(b'SELECT 1;\r\n')
    (source/'database/migrations/0003_before.sql').write_bytes(b'SELECT 3;\r\n')
    (source/'database/migrations/0004_after.sql').write_bytes(b'SELECT 4;\n')
    result=module.historical_root(source,tmp_path/'owned-copy','0003_before.sql')
    assert (result/'deploy/init.sql').read_bytes()==b'SELECT 1;\r\n'
    assert not (result/'database/migrations/0004_after.sql').exists()
    assert module.journal_entries(result)=={'deploy/init.sql':hashlib.sha256(b'SELECT 1;\r\n').hexdigest(),'database/migrations/0003_before.sql':hashlib.sha256(b'SELECT 3;\r\n').hexdigest()}

def backup(tmp_path):
    path=tmp_path/'owned.sql';data=b'BEGIN; SELECT 75; COMMIT;\n';path.write_bytes(data)
    manifest=path.with_suffix('.sql.manifest.json');manifest.write_text(json.dumps({'sha256':hashlib.sha256(data).hexdigest(),'size_bytes':len(data),'restore_verified':False}))
    return path,manifest

def test_successful_capture_is_not_claimed_restore_verified(tmp_path):
    path,_=backup(tmp_path)
    assert module.admitted_backup(path)['restore_verified']is False

@pytest.mark.parametrize('mutation',['missing-manifest','changed-byte','truncated','wrong-digest','bool-size'])
def test_backup_consumer_refuses_incomplete_or_tampered_capture(tmp_path,mutation):
    path,manifest=backup(tmp_path)
    if mutation=='missing-manifest':manifest.unlink()
    elif mutation=='changed-byte':path.write_bytes(path.read_bytes().replace(b'75',b'76'))
    elif mutation=='truncated':path.write_bytes(b'BEGIN;')
    else:
        data=json.loads(manifest.read_text());data['sha256'if mutation=='wrong-digest'else'size_bytes']='0'*64 if mutation=='wrong-digest'else True;manifest.write_text(json.dumps(data))
    with pytest.raises((ValueError,FileNotFoundError)):module.admitted_backup(path)

def test_deadline_expiry_still_removes_owned_resources(tmp_path,monkeypatch):
    run=module.Rehearsal(tmp_path);run.deadline=0
    name=run.tag+'-fixture';run.containers=[name];commands=[]
    def fake(args,**kwargs):
        commands.append(args)
        if args[1]=='inspect':return module.subprocess.CompletedProcess(args,0,json.dumps([{'Config':{'Labels':{'nsai.owner':run.tag}}}]).encode(),b'')
        if args[1:3]==['network','inspect']:return module.subprocess.CompletedProcess(args,1,b'',b'')
        return module.subprocess.CompletedProcess(args,0,b'',b'')
    monkeypatch.setattr(module.subprocess,'run',fake)
    run.cleanup()
    assert ['docker','rm','-f',name]in commands
    assert run.receipt['cleanup_complete']is True

def test_cleanup_refuses_a_mismatched_ownership_label(tmp_path,monkeypatch):
    run=module.Rehearsal(tmp_path);name=run.tag+'-fixture';commands=[]
    def fake(args,**kwargs):
        commands.append(args)
        return module.subprocess.CompletedProcess(args,0,json.dumps([{'Config':{'Labels':{'nsai.owner':'another-owned-run'}}}]).encode(),b'')
    monkeypatch.setattr(module.subprocess,'run',fake)
    with pytest.raises(RuntimeError,match='unowned'):run.remove(name,cleanup=True)
    assert not any(args[1]=='rm'for args in commands)

def test_failed_receipt_serialization_preserves_previous_complete_snapshot(tmp_path,monkeypatch):
    path=tmp_path/'private-receipt.json';path.write_text('{"previous":"complete"}')
    def fail_after_partial(data,stream,**kwargs):
        stream.write('{"incomplete":');raise OSError('original synthetic disk failure')
    monkeypatch.setattr(module.json,'dump',fail_after_partial)
    with pytest.raises(OSError):module.write(path,{'new':'receipt'})
    assert path.read_text()=='{"previous":"complete"}'
    assert list(tmp_path.glob('*.partial'))==[]

@pytest.mark.parametrize('image',['latest','nsai-implementation-candidate:local','sha256:bad',None])
def test_compatibility_probe_refuses_mutable_or_invalid_image_identity(tmp_path,image):
    with pytest.raises(ValueError,match='exact local'):module.Rehearsal(tmp_path,image)

@pytest.mark.parametrize('same_image',[True,False])
def test_hold_cleanup_only_untags_owned_matching_reference(tmp_path,monkeypatch,same_image):
    run=module.Rehearsal(tmp_path);run.hold_created=True;commands=[]
    def fake(args,**kwargs):
        commands.append(args)
        if args[1:3]==['network','inspect']:return module.subprocess.CompletedProcess(args,1,b'',b'')
        if args[1:3]==['image','inspect']:
            value=run.compatibility_image if same_image else 'sha256:'+'a'*64
            return module.subprocess.CompletedProcess(args,0,value.encode(),b'')
        return module.subprocess.CompletedProcess(args,0,b'',b'')
    monkeypatch.setattr(module.subprocess,'run',fake);run.cleanup()
    removals=[args for args in commands if args[1:3]==['image','rm']]
    assert removals==([['docker','image','rm',run.hold_tag]]if same_image else [])
    assert run.receipt['cleanup_complete']is same_image
