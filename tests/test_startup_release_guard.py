import importlib.util
from pathlib import Path
import sys
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('release_guard', ROOT / 'scripts/check_release_readiness.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

def fixture(tmp_path):
    destination = tmp_path / 'plans/implementation'
    destination.mkdir(parents=True)
    for name in ('backlog.json', 'execution-status.json'):
        shutil.copyfile(ROOT / 'plans/implementation' / name, destination / name)
    return destination

def test_absent_admission_denies_without_writes(tmp_path):
    fixture(tmp_path)
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    result = guard.validate(tmp_path)
    assert result['status'] == 'DENY' and result['mutations_performed'] is False
    assert 'Required admission artifact missing: evidence/implementation/release-admission.json' in result['errors']
    assert before == {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}

def test_manual_acceptance_strings_cannot_admit(tmp_path):
    directory = fixture(tmp_path)
    ledger = json.loads((directory / 'execution-status.json').read_text())
    for card in ledger['cards']:
        card['accepted'] = True
        card['unaccepted_dependencies'] = []
        for criterion in card['criteria']:
            criterion['status'] = 'CONFIRMED'
    (directory / 'execution-status.json').write_text(json.dumps(ledger))
    assert guard.validate(tmp_path)['status'] == 'DENY'

def test_backlog_tamper_denies(tmp_path):
    directory = fixture(tmp_path)
    with (directory / 'backlog.json').open('a') as stream:
        stream.write(' ')
    assert 'Admission evidence invalid: ValueError: Original backlog binding mismatch' in guard.validate(tmp_path)['errors'][-1]

def test_gate_precedes_every_mutating_startup_stage():
    text = (ROOT / 'scripts/start-cpu.ps1').read_text()
    gate = text.index('check_release_readiness.py')
    for stage in ('-m venv', '-m pip', 'bootstrap_secrets.py', 'protect-secrets.ps1', 'prepare_cpu_model.py', 'compose @compose build', 'scripts/migrate.py'):
        assert gate < text.index(stage)
    assert "if ($LASTEXITCODE -ne 0) { throw 'Full-feature startup denied" in text

def test_missing_or_changed_source_snapshot_denies(tmp_path):
    fixture(tmp_path)
    path = tmp_path / 'src/example.py'
    path.parent.mkdir()
    path.write_text('first')
    before = guard.source_snapshot(tmp_path)
    path.write_text('changed')
    assert before != guard.source_snapshot(tmp_path)
    assert guard.validate(tmp_path)['status'] == 'DENY'

def test_actual_database_migration_changes_binding(tmp_path):
    path = tmp_path / 'database/migrations/0005_governed_records.sql'
    path.parent.mkdir(parents=True)
    path.write_text('SELECT 1;')
    before = guard.source_snapshot(tmp_path)
    assert 'database/migrations/0005_governed_records.sql' in before
    path.write_text('SELECT 2;')
    assert before != guard.source_snapshot(tmp_path)

def test_source_directory_reparse_rejected_before_descent(tmp_path, monkeypatch):
    import stat
    path = tmp_path / 'database'
    path.mkdir()
    original = Path.lstat
    class Attributes:
        st_file_attributes = getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 1024)
    monkeypatch.setattr(Path, 'lstat', lambda self: Attributes() if self == path else original(self))
    import pytest
    with pytest.raises(ValueError, match='junction'):
        guard.source_snapshot(tmp_path)


def test_frontend_source_lock_and_docker_inputs_are_release_bound(tmp_path):
    directory = tmp_path / 'frontend/noetaris'
    for name in ('src/App.jsx', 'package-lock.json', 'Dockerfile', 'deploy/nginx.conf'):
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('original', encoding='utf-8')
    before = guard.source_snapshot(tmp_path)
    for name in ('src/App.jsx', 'package-lock.json', 'Dockerfile', 'deploy/nginx.conf'):
        path = directory / name
        assert path.relative_to(tmp_path).as_posix() in before
        path.write_text('changed', encoding='utf-8')
        assert guard.source_snapshot(tmp_path) != before
        path.write_text('original', encoding='utf-8')


def test_frontend_snapshot_excludes_secrets_and_generated_dependencies(tmp_path):
    directory = tmp_path / 'frontend/noetaris'
    for name in ('.env', '.env.local', 'node_modules/dependency.js', 'dist/assets/bundle.js', 'build.log', '.env.example'):
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('synthetic', encoding='utf-8')
    assert set(guard.source_snapshot(tmp_path)) == {'frontend/noetaris/.env.example'}
