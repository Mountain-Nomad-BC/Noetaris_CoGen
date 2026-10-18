"""Offline closure, artifact identity and build/install boundary checks."""
import importlib.util
import json
from pathlib import Path
import re
import tomllib
from urllib.parse import urlsplit
import pytest

ROOT=Path(__file__).resolve().parents[1]


def tool():
    spec=importlib.util.spec_from_file_location('toolchain_lock',ROOT/'scripts/lock_dev_tools.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def test_recorded_official_complete_build_and_dev_closure():
    module=tool(); groups=module.check(ROOT)
    assert set(groups['build'])=={'pip','setuptools','wheel','packaging'}
    assert set(groups['dev'])=={'pytest','pyyaml','packaging','pluggy','iniconfig','pygments','colorama'}
    provenance=json.loads((ROOT/'evidence/implementation/toolchain-lock-provenance.json').read_text())
    assert provenance['runtime_lock_modified'] is False
    for name,release in provenance['releases'].items():
        assert release['metadata_url']==f'https://pypi.org/pypi/{name}/{module.PINS[name]}/json'
        assert re.fullmatch('[a-f0-9]{64}',release['metadata_sha256'])
        assert release['artifacts']
        assert all(urlsplit(row['url']).hostname=='files.pythonhosted.org' for row in release['artifacts'])


def test_cross_platform_marker_union_includes_windows_dependency_without_dev_extras():
    metadata={'pytest':{'requires_dist':['colorama>=0.4; sys_platform == "win32"','hypothesis; extra == "dev"']},
              'colorama':{'requires_dist':[]}}
    assert tool().closure(['pytest'],metadata)==['colorama','pytest']


def test_new_or_incompatible_dependency_requires_review():
    with pytest.raises(ValueError,match='missing/incompatible'):
        tool().closure(['pytest'],{'pytest':{'requires_dist':['unreviewed_dependency>=1']}})
    with pytest.raises(ValueError,match='missing/incompatible'):
        tool().closure(['pytest'],{'pytest':{'requires_dist':['pluggy<1']}})


@pytest.mark.parametrize('line',['pytest>=9 --hash=sha256:'+'a'*64,'pytest==9.1.1','pytest==9.1.1 --hash=md5:'+'a'*32])
def test_unlocked_or_non_sha256_entries_rejected(tmp_path,line):
    path=tmp_path/'bad.lock';path.write_text(line)
    with pytest.raises(ValueError):tool().lock_entries(path)


def test_exact_backend_requirements_match_recorded_build_closure():
    project=tomllib.loads((ROOT/'pyproject.toml').read_text())
    assert project['build-system']['requires']==['setuptools==84.0.0','wheel==0.48.0']
    assert project['build-system']['build-backend']=='setuptools.build_meta'


def test_installers_use_locked_tools_and_no_isolated_unlocked_build():
    source=(ROOT/'scripts/start-cpu.ps1').read_text()
    assert source.index('requirements-build.lock')<source.index('--no-build-isolation --no-deps -e .')
    assert 'requirements-dev.lock' in source and "install 'pytest==" not in source
    assert source.count('--require-hashes --only-binary=:all:')>=3
    workflow=(ROOT/'.github/workflows/ci.yaml').read_text()
    refs=re.findall(r'uses:\s+([\w/-]+)@([^\s]+)',workflow)
    assert len(refs)==2 and all(re.fullmatch('[a-f0-9]{40}',sha) for _,sha in refs)
    assert 'persist-credentials: false' in workflow
    assert '--no-build-isolation --no-deps -e .' in workflow
    assert 'requirements-dev.lock' in workflow and 'requirements-build.lock' in workflow
    assert 'contents: read' in workflow and 'deploy/amd' not in workflow
