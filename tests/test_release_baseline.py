"""Original negative fixtures for release evidence custody; no live resources."""
import hashlib
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/release_baseline.py'
spec = importlib.util.spec_from_file_location('release_baseline', SCRIPT)
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)


def test_receipt_bytes_are_verified_but_not_accepted(tmp_path):
    (tmp_path / 'evidence').mkdir()
    raw = b'{"status":"PASS"}'
    (tmp_path / 'evidence/result.json').write_bytes(raw)
    row = baseline.bind_evidence(tmp_path, {'path':'evidence/result.json', 'sha256':hashlib.sha256(raw).hexdigest()})
    assert row['byte_identity_verified'] is True
    assert row['requirement_accepted'] is False


def test_changed_evidence_is_not_admitted(tmp_path):
    (tmp_path / 'evidence').mkdir()
    (tmp_path / 'evidence/result.json').write_bytes(b'changed')
    with pytest.raises(ValueError):
        baseline.bind_evidence(tmp_path, {'path':'evidence/result.json', 'sha256':'a'*64})


@pytest.mark.parametrize('path', ['../outside.json', 'secrets/key.json', '/absolute.json'])
def test_evidence_cannot_escape_allowlisted_root(tmp_path, path):
    with pytest.raises(ValueError):
        baseline.bind_evidence(tmp_path, {'path':path, 'sha256':'a'*64})


def test_junction_or_symlink_is_not_followed(tmp_path):
    (tmp_path / 'evidence').mkdir()
    target = tmp_path / 'outside.json'
    target.write_bytes(b'private')
    link = tmp_path / 'evidence/result.json'
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip('Host lacks symlink privilege; link checks also run in container validation')
    with pytest.raises(ValueError):
        baseline.bind_evidence(tmp_path, {'path':'evidence/result.json', 'sha256':hashlib.sha256(b'private').hexdigest()})


def test_inventory_includes_tests_but_excludes_secrets_and_raw_evidence(tmp_path):
    for name in ('requirements.lock', 'requirements-build.lock', 'Dockerfile', '.dockerignore'):
        (tmp_path / name).write_text('fixture', encoding='utf-8')
    for directory in ('tests', 'secrets', 'evidence'):
        (tmp_path / directory).mkdir()
        (tmp_path / directory / 'entry.txt').write_text('fixture', encoding='utf-8')
    (tmp_path / '.env').write_text('fixture', encoding='utf-8')
    result = baseline.source_inventory(tmp_path)
    assert 'tests/entry.txt' in result
    assert '.env' not in result
    assert not any(p.startswith(('secrets/', 'evidence/')) for p in result)
