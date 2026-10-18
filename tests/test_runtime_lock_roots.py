import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('runtime_lock_under_test', ROOT/'scripts/lock_runtime.py')
lock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lock)


def project(tmp_path, requirements):
    (tmp_path/'pyproject.toml').write_text('[project]\ndependencies = '+json.dumps(requirements)+'\n')
    return tmp_path


def test_project_roots_preserve_fonttools_redis_oauth_and_psycopg_binary():
    import tomllib
    from packaging.requirements import Requirement
    declared = [Requirement(item) for item in tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['dependencies']]
    versions = {req.name.lower(): next(iter(req.specifier)).version for req in declared}
    versions['psycopg-binary'] = versions['psycopg']
    def distribution(name):
        return SimpleNamespace(version=versions[name], requires=["psycopg-binary==3.2.12; extra == 'binary'"] if name=='psycopg' else [])
    result = lock.resolved_runtime(ROOT, distribution=distribution)
    assert {'fonttools','redis','authlib','psycopg','psycopg-binary'} <= result.keys()
    assert result['psycopg-binary']=='3.2.12'


def test_extras_discovered_late_expand_dependencies_without_test_tools(tmp_path):
    root = project(tmp_path, ['parent==1','codec==1'])
    distributions = {
        'parent': SimpleNamespace(version='1', requires=['codec[audio]==1']),
        'codec': SimpleNamespace(version='1', requires=["audio-runtime==2; extra == 'audio'", "pytest==9; extra == 'test'"]),
        'audio-runtime': SimpleNamespace(version='2', requires=[]),
    }
    assert lock.resolved_runtime(root, distribution=distributions.__getitem__) == {
        'parent':'1','codec':'1','audio-runtime':'2'}


def test_installed_version_conflicts_are_rejected_before_rewriting_lock(tmp_path):
    root = project(tmp_path, ['parent==1'])
    target = root/'requirements.lock'
    target.write_text('retained prior lock\n')
    distributions = {
        'parent': SimpleNamespace(version='1', requires=['dependency>=2']),
        'dependency': SimpleNamespace(version='1', requires=[]),
    }
    with pytest.raises(ValueError, match='Installed version'):
        lock.resolved_runtime(root, distribution=distributions.__getitem__)
    assert target.read_text()=='retained prior lock\n'
