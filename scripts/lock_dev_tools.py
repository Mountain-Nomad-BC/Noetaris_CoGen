"""Reviewable, exact build/test dependency closure from official PyPI release metadata.

--write fetches immutable-version metadata; the default checks existing lock shape offline.
It never installs tools, changes the runtime lock, starts Docker or accesses credentials.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import urllib.request
from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.specifiers import SpecifierSet

ROOT = Path(__file__).resolve().parents[1]
# Installed development versions retained; absent build tools explicitly selected
# from their official PyPI releases on 2026-10-14. No floating version resolution.
PINS = {'pytest':'9.1.1', 'pyyaml':'6.0.3', 'packaging':'26.3', 'pluggy':'1.6.0',
        'iniconfig':'2.3.1', 'pygments':'2.21.0', 'colorama':'0.4.6',
        'setuptools':'84.0.0', 'wheel':'0.48.0', 'pip':'26.2.1'}
GROUPS = {'build':('pip','setuptools','wheel'), 'dev':('pytest','pyyaml')}
ENVIRONMENTS = []
for version in ('3.12.15','3.13.0','3.14.5'):
    for platform, system, os_name, machine in [('win32','Windows','nt','AMD64'),('linux','Linux','posix','x86_64'),('darwin','Darwin','posix','arm64')]:
        env = default_environment()
        env.update(python_version='.'.join(version.split('.')[:2]), python_full_version=version,
                   sys_platform=platform, platform_system=system, os_name=os_name,
                   platform_machine=machine, implementation_name='cpython',
                   implementation_version=version, platform_python_implementation='CPython', extra='')
        ENVIRONMENTS.append(env)


def active(requirement: Requirement) -> bool:
    return requirement.marker is None or any(requirement.marker.evaluate(env) for env in ENVIRONMENTS)


def fetch_release(name: str, version: str) -> dict:
    url = f'https://pypi.org/pypi/{name}/{version}/json'
    request = urllib.request.Request(url, headers={'User-Agent':'NSAI-reviewed-toolchain-lock/1'})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read(4*1024*1024+1)
    if len(raw) > 4*1024*1024:
        raise ValueError('PyPI metadata budget exceeded')
    data = json.loads(raw)
    if str(data['info']['version']) != version:
        raise ValueError('PyPI release identity mismatch')
    artifacts = []
    for file in data['urls']:
        if file.get('yanked'):
            continue
        digest = file.get('digests', {}).get('sha256', '')
        if not re.fullmatch('[a-f0-9]{64}', digest):
            raise ValueError('Release artifact lacks SHA256')
        artifacts.append({'filename':file['filename'], 'sha256':digest, 'url':file['url'],
                          'packagetype':file['packagetype'], 'requires_python':file.get('requires_python')})
    if not artifacts:
        raise ValueError('No unyanked release artifacts')
    return {'package':name, 'version':version, 'metadata_url':url,
            'metadata_sha256':hashlib.sha256(raw).hexdigest(),
            'requires_python':data['info'].get('requires_python'),
            'requires_dist':data['info'].get('requires_dist') or [], 'artifacts':artifacts}


def closure(roots, metadata):
    found, pending = set(), list(roots)
    while pending:
        name = canonicalize_name(pending.pop())
        if name in found:
            continue
        if name not in PINS:
            raise ValueError('Dependency lacks a reviewed exact pin: '+name)
        release = metadata[name]
        if any(not SpecifierSet(release.get('requires_python') or '').contains(env['python_full_version']) for env in ENVIRONMENTS):
            raise ValueError('Tool release does not support the declared Python matrix: '+name)
        found.add(name)
        for raw in release.get('requires_dist', []):
            requirement = Requirement(raw)
            if not active(requirement):
                continue
            dependency = canonicalize_name(requirement.name)
            if requirement.url or requirement.extras:
                raise ValueError('URL/extra dependency requires explicit lock review')
            if dependency not in PINS or not requirement.specifier.contains(PINS[dependency]):
                raise ValueError('Dependency version missing/incompatible: '+dependency)
            pending.append(dependency)
    return sorted(found)


def lock_entries(path: Path) -> dict[str, str]:
    found = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        if not re.fullmatch(r'[A-Za-z0-9_-]+==[A-Za-z0-9_.]+', parts[0]) or len(parts)<2:
            raise ValueError('Lock requires exact version and hashes')
        name, version = parts[0].split('==')
        name = canonicalize_name(name)
        if name in found or any(not re.fullmatch(r'--hash=sha256:[a-f0-9]{64}', part) for part in parts[1:]):
            raise ValueError('Duplicate package or malformed artifact hash')
        found[name] = version
    return found


def check(root=ROOT):
    root = Path(root)
    provenance = json.loads((root/'evidence/implementation/toolchain-lock-provenance.json').read_text(encoding='utf-8'))
    found = {}
    for group in GROUPS:
        found[group] = lock_entries(root/f'requirements-{group}.lock')
        if not set(GROUPS[group]) <= set(found[group]) or any(PINS.get(name) != version for name, version in found[group].items()):
            raise ValueError('Lock differs from reviewed pins')
        expected = closure(GROUPS[group], provenance['releases'])
        if sorted(found[group]) != expected:
            raise ValueError('Lock is missing or adds a dependency from the recorded complete closure')
        for line in (root/f'requirements-{group}.lock').read_text(encoding='utf-8').splitlines():
            if not line or line.startswith('#'): continue
            parts = line.split()
            name = canonicalize_name(parts[0].split('==')[0])
            actual = {part.removeprefix('--hash=sha256:') for part in parts[1:]}
            expected_hashes = {file['sha256'] for file in provenance['releases'][name]['artifacts']}
            if actual != expected_hashes:
                raise ValueError('Lock artifact hashes differ from recorded official release metadata')
    for name in set(found['build']) & set(found['dev']):
        if found['build'][name] != found['dev'][name]:
            raise ValueError('Build/dev lock conflict')
    return found


def write(root=ROOT):
    root = Path(root)
    metadata = {name:fetch_release(name, version) for name, version in sorted(PINS.items())}
    groups = {}
    for group, roots in GROUPS.items():
        packages = closure(roots, metadata)
        groups[group] = packages
        lines = ['# Exact reviewed tool closure; CPython 3.12-3.14, Windows/Linux/macOS marker union.',
                 '# Official PyPI release SHA256 for all unyanked platform artifacts; install --only-binary=:all:.']
        for name in packages:
            hashes = sorted({file['sha256'] for file in metadata[name]['artifacts']})
            lines.append(name+'=='+PINS[name]+' '+ ' '.join('--hash=sha256:'+digest for digest in hashes))
        (root/f'requirements-{group}.lock').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    evidence = root/'evidence/implementation/toolchain-lock-provenance.json'
    evidence.parent.mkdir(parents=True,exist_ok=True)
    evidence.write_text(json.dumps({'captured_at':datetime.now(timezone.utc).isoformat(),
        'pins':PINS, 'roots':GROUPS, 'groups':groups, 'marker_environments':ENVIRONMENTS,
        'releases':metadata, 'runtime_lock_modified':False},indent=2),encoding='utf-8')
    return check(root)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
    result=write() if args.write else check()
    print(json.dumps({'status':'PASS','groups':result}))


if __name__=='__main__': main()
