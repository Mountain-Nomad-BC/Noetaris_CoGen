"""Freeze the isolated CPU encoder closure; never install into the host or API.

Versions come from the existing lock (or the initial semantic smoke environment),
with shared runtime and reviewed security pins preserved. Hashes/requirements come
from official exact-version PyPI metadata.
"""
import argparse
from datetime import datetime,timezone
from importlib import metadata
import json
from pathlib import Path
from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from lock_dev_tools import fetch_release,lock_entries

ROOT=Path(__file__).resolve().parents[1]
ROOTS={'numpy':'2.5.1','onnxruntime':'1.27.0','tokenizers':'0.22.2'}
SECURITY_PINS={'fsspec':'2026.6.0'}  # GHSA-27vj-qcqg-25rc fixed upstream release.


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--write',action='store_true');args=cli.parse_args()
    path=ROOT/'requirements-semantic.lock'
    evidence=ROOT/'evidence/implementation/semantic-lock-provenance.json'
    environment=default_environment()
    environment.update(python_version='3.12',python_full_version='3.12.15',sys_platform='linux',
        platform_system='Linux',os_name='posix',platform_machine='x86_64',
        implementation_name='cpython',implementation_version='3.12.15',platform_python_implementation='CPython',extra='')
    if args.write:
        common=lock_entries(ROOT/'requirements.lock');existing=lock_entries(path) if path.exists() else {}
        found={};pending=dict(ROOTS,**SECURITY_PINS)
        while pending:
            name,version=pending.popitem()
            name=canonicalize_name(name)
            if name in found:
                if found[name]['version']!=version:raise ValueError('Conflicting semantic dependency pin')
                continue
            release=fetch_release(name,version);found[name]=release
            for raw in release['requires_dist']:
                req=Requirement(raw)
                if req.marker is not None and not req.marker.evaluate(environment):continue
                if req.url or req.extras:raise ValueError('Explicit extra/URL dependency needs review')
                dependency=canonicalize_name(req.name)
                selected=common.get(dependency) or SECURITY_PINS.get(dependency) or existing.get(dependency) or metadata.version(dependency)
                if not req.specifier.contains(selected):raise ValueError('Installed/shared dependency pin is incompatible: '+dependency)
                pending[dependency]=selected
        lines=['# Isolated encoder closure; CPython 3.12 Linux x86_64 only.',
               '# Qualified roots plus explicit security pins; official unyanked PyPI artifact hashes.']
        for name,release in sorted(found.items()):
            hashes=sorted({artifact['sha256'] for artifact in release['artifacts']})
            lines.append(name+'=='+release['version']+' '+' '.join('--hash=sha256:'+sha for sha in hashes))
        path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
        evidence.write_text(json.dumps(dict(scope='Encoder dependency custody, not package/security acceptance',
            recorded_at=datetime.now(timezone.utc).isoformat(),environment=environment,roots=ROOTS,security_pins=SECURITY_PINS,
            releases=found),indent=2)+'\n',encoding='utf-8')
    record=json.loads(evidence.read_text(encoding='utf-8'));entries=lock_entries(path)
    expected=record['releases']
    if entries!={name:release['version'] for name,release in expected.items()}:
        raise ValueError('Semantic closure differs from recorded exact release pins')
    common=lock_entries(ROOT/'requirements.lock')
    if any(entries.get(name)!=version for name,version in SECURITY_PINS.items()):
        raise ValueError('Semantic security pin differs from reviewed minimum fixed release')
    for name,version in entries.items():
        if name in common and common[name]!=version:raise ValueError('API/encoder shared dependency conflict')
        for raw in expected[name]['requires_dist']:
            req=Requirement(raw)
            if req.marker is not None and not req.marker.evaluate(environment):continue
            dependency=canonicalize_name(req.name)
            if req.url or req.extras or dependency not in entries or not req.specifier.contains(entries[dependency]):
                raise ValueError('Incomplete or incompatible semantic closure')
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):continue
        parts=line.split();name=canonicalize_name(parts[0].split('==')[0])
        actual={part.removeprefix('--hash=sha256:') for part in parts[1:]}
        if actual!={artifact['sha256'] for artifact in expected[name]['artifacts']}:
            raise ValueError('Semantic artifact hash mismatch')
    print(json.dumps(dict(status='PASS_LOCK_CUSTODY_ONLY',packages=len(entries),roots=ROOTS)))


if __name__=='__main__':main()
