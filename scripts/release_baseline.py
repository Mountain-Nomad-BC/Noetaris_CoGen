"""Read-only release inventory. Evidence identity never grants release acceptance."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import re
import stat
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_candidate import snapshot


def safe_file(root, relative, *, prefix='evidence'):
    if not isinstance(relative, str) or '\\' in relative or ':' in relative:
        raise ValueError('Invalid artifact path')
    parts = PurePosixPath(relative)
    if parts.is_absolute() or '..' in parts.parts or not parts.parts or parts.parts[0] != prefix:
        raise ValueError('Artifact path outside admitted root')
    path = root
    for part in parts.parts:
        path = path / part
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
            raise ValueError('Artifact links or reparse points refused')
    if not path.is_file() or path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError('Artifact missing or exceeds bound')
    return path


def bind_evidence(root, entry):
    path = safe_file(root, entry['path'])
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if not re.fullmatch('[a-f0-9]{64}', entry.get('sha256', '')) or digest != entry['sha256']:
        raise ValueError('Evidence byte identity mismatch')
    return dict(path=entry['path'], sha256=digest, bytes=len(raw),
                byte_identity_verified=True, requirement_accepted=False,
                review='NOT_INDEPENDENTLY_REVIEWED')


def source_inventory(root):
    result = snapshot(root)
    def walk(directory):
        for path in directory.iterdir():
            if path.name in ('__pycache__', '.pytest_cache') or path.suffix == '.pyc':
                continue
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
                raise ValueError('Source links or reparse points refused')
            if path.is_dir():
                walk(path)
            elif path.is_file():
                result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ('tests', 'plans', 'docs', '.github'):
        directory = root / name
        if directory.exists():
            info = directory.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
                raise ValueError('Source directory reparse point refused')
            walk(directory)
    for name in ('README.md', 'NOTICE', 'LICENSE', '.gitignore', '.env.example'):
        path = root / name
        if path.exists():
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
                raise ValueError('Source file reparse point refused')
            result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def command(arguments):
    result = subprocess.run(arguments, capture_output=True, timeout=30, cwd=ROOT)
    if result.returncode:
        raise RuntimeError('Inventory command failed; raw output withheld')
    if len(result.stdout) > 2 * 1024 * 1024:
        raise RuntimeError('Inventory output exceeds bound')
    return result.stdout.decode('utf-8').strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog',default='evidence/release-validation/current.json')
    args = parser.parse_args()
    before = source_inventory(ROOT)
    run_id = uuid4().hex
    catalog_path = safe_file(ROOT, args.catalog)
    catalog_raw = catalog_path.read_bytes()
    catalog = json.loads(catalog_raw)
    evidence = [bind_evidence(ROOT, entry) for entry in catalog['evidence']]
    image = command(['docker', 'image', 'inspect', '--format', '{{.Id}}', 'nsai-implementation-candidate:local'])
    if not re.fullmatch('sha256:[a-f0-9]{64}', image):
        raise ValueError('Invalid candidate image identity')
    if image != catalog['api_candidate']:
        raise ValueError('Candidate changed; prior evidence needs explicit reassessment')
    # Select metadata fields at the Docker boundary; never capture Config.Env or inspect secrets.
    template = '{{json .Name}}|{{json .Image}}|{{json .State.Status}}|{{if .State.Health}}{{json .State.Health.Status}}{{else}}null{{end}}'
    containers = []
    for name in ('api', 'parser', 'db', 'llama-cpp'):
        value = command(['docker', 'container', 'inspect', '--format', template, 'amd-hackathon-nsai-' + name + '-1'])
        fields = [json.loads(v) for v in value.split('|')]
        containers.append(dict(service=name, name=fields[0], image=fields[1], status=fields[2], health=fields[3]))
    binding_entry = catalog['image_binding']
    bind_evidence(ROOT,binding_entry)
    image_binding = json.loads(safe_file(ROOT,binding_entry['path']).read_bytes())
    mismatches = [name for name, digest in image_binding['host_source_hashes'].items() if before.get(name) != digest]
    if image_binding['image'] != image or mismatches:
        raise ValueError('Candidate runtime source no longer matches image evidence')
    after = source_inventory(ROOT)
    if before != after:
        raise ValueError('Source changed during inventory')
    git_present = any((parent / '.git').exists() for parent in (ROOT, *ROOT.parents))
    report = dict(
        run_id=run_id, captured_at=datetime.now(timezone.utc).isoformat(),
        status='PASS_INVENTORY_ONLY', release_approved=False, independent_review='UNASSIGNED',
        source_manifest=before, source_manifest_sha256=hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
        manifest_scope='Build inputs plus tests, plans, docs, CI, notices and example configuration. Excludes private state, secrets, real .env, corpora, generated evidence and bytecode.',
        runtime_source_binding=dict(image=image, matched_files=len(image_binding['host_source_hashes'])),
        git=dict(metadata_present=git_present, commit=None, branch=None, tag=None, dirty_state='UNAVAILABLE_NOT_ASSERTED'),
        environment=dict(os=platform.system(), release=platform.release(), machine=platform.machine(),
                         python=platform.python_version(), docker=json.loads(command(['docker', 'version', '--format', '{{json .}}']))['Server']['Version'],
                         compose=command(['docker', 'compose', 'version', '--short'])),
        candidate_image=image, live_containers=containers,
        prior_evidence_catalog=dict(path=args.catalog, sha256=hashlib.sha256(catalog_raw).hexdigest()),
        evidence=evidence, disabled=['central-security', 'generated-execution', 'AMD', 'Evolus', 'voice'],
        unresolved=['No Git revision identity', 'Independent reviewer unassigned',
                    'Dedicated security scan prerequisite unresolved', 'OCR/formula quality remains partial',
                    'Cross-user/source isolation not commissioned', 'Untouched release holdouts not yet qualified'],
        limitations=['Existing evidence hashes checked; no test suite rerun by inventory.',
                     'Runtime source binding excludes changed host scripts and tests; full source manifest records those separately.',
                     'Hardware inventory, logs, schema snapshot and claim-by-claim evidence admission remain separate tasks.'],
    )
    destination = ROOT / 'evidence/release-validation/REL-C00' / run_id
    destination.mkdir(parents=True, exist_ok=False)
    # Retain exact catalog bytes: the navigation pointer may legitimately advance later.
    with (destination / 'catalog.json').open('xb') as stream:
        stream.write(catalog_raw)
    report['prior_evidence_catalog']['immutable_snapshot']='catalog.json'
    (destination / 'baseline.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], run_id=run_id, matched_runtime_files=report['runtime_source_binding']['matched_files'], evidence_files=len(evidence), release_approved=False)))


if __name__ == '__main__':
    main()
