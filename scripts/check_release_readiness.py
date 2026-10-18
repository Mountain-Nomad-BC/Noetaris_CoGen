"""Read-only foundation release admission. Missing independent evidence denies startup."""
from pathlib import Path
import hashlib
import json
import sys
from evidence_contract import admit_receipt

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_BACKLOG_SHA256 = 'e90209a70de6b9569184aaa10c885975e36df7cc9868ca47159f1943693c83ed'
RELEASE_EXTENSION_SHA256 = '5b961ed711088912c2920213185abe6ff9307953e5f0ae5902050d20c7b3ef1e'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def source_snapshot(root):
    """Exact deployable source/config/build inputs; never credentials or evidence."""
    files = set()
    root = root.resolve()
    def reject_link(path):
        # Windows junctions are reparse points even when is_symlink is false.
        import stat
        attributes = path.lstat().st_file_attributes if hasattr(path.lstat(), 'st_file_attributes') else 0
        if attributes & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 1024) or path.is_symlink():
            raise ValueError('Source link or junction not admitted')
    def walk(directory, frontend=False):
        if not directory.exists():
            return
        reject_link(directory)
        for path in directory.iterdir():
            if path.name == '__pycache__' or path.suffix == '.pyc':
                continue
            if frontend and (path.name in {'node_modules', 'dist', '.git', 'build', '.vite'}
                    or path.suffix == '.log' or (path.name.startswith('.env') and path.name != '.env.example')):
                continue
            reject_link(path)
            if path.is_dir():
                yield from walk(path, frontend=frontend)
            elif path.is_file():
                yield path
    for directory in ('src', 'assets', 'scripts', 'database', 'deploy', 'LICENSES'):
        for path in walk(root / directory):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                if path.is_symlink():
                    raise ValueError('Source link not admitted')
                files.add(path)
    for path in walk(root / 'frontend', frontend=True):
        files.add(path)
    for pattern in ('compose*.yaml', 'Dockerfile*', 'requirements*.lock', 'pyproject.toml', '.dockerignore', 'LICENSE', 'NOTICE',
                    'package.json', 'package-lock.json', 'neon.ts', 'hello.ts', '.env.example'):
        for path in root.glob(pattern):
            reject_link(path)
            files.add(path)
    return {p.relative_to(root).as_posix(): digest(p.read_bytes()) for p in sorted(files)}

def read_json(path):
    data = path.read_bytes()
    if len(data) > 16 * 1024 * 1024:
        raise ValueError('Oversized admission artifact')
    return json.loads(data), data


def validate_extension_acceptance(plan, payload, *, reference_plan_sha256):
    """Check all appended requirements, not merely an aggregate PASS string."""
    errors=[]
    try:
        if payload.get('schema_version')!='nsai.release-extension-acceptance/1' or payload.get('extension_sha256')!=RELEASE_EXTENSION_SHA256:
            errors.append('Release extension specification binding missing')
        if payload.get('reference_plan_sha256')!=reference_plan_sha256:
            errors.append('Research plan binding mismatch')
        if payload.get('independent_review') is not True or not isinstance(payload.get('reviewer'),str) or not 1<=len(payload['reviewer'])<=200:
            errors.append('Release extension independent reviewer missing')
        expected={r['id']:r for r in plan['requirements']}
        entries=payload['requirements']
        current={r['id']:r for r in entries}
        if len(expected)!=209 or len(entries)!=209 or len(current)!=209 or set(current)!=set(expected):
            errors.append('Release extension requirement inventory mismatch')
        for identity,row in current.items():
            original=expected.get(identity)
            if original is None:continue
            status=row.get('disposition')
            if status=='NOT_APPLICABLE':
                # Current scope explicitly defers only voice and actual AMD qualification.
                if original['section'] not in (9,12) or not isinstance(row.get('reason'),str) or len(row['reason'])<20:
                    errors.append(identity+': exclusion not authorized by current CPU scope')
            elif status!='PASS' or not isinstance(row.get('evidence_id'),str) or not 1<=len(row['evidence_id'])<=200:
                errors.append(identity+': fresh criterion evidence missing')
        references=payload['reference_cards']
        if len(references)!=9 or {r['id'] for r in references}!={f'REF-{n:02d}' for n in range(1,10)}:
            errors.append('Research card acceptance inventory mismatch')
        if any(r.get('accepted') is not True or not isinstance(r.get('evidence_id'),str) or not 1<=len(r['evidence_id'])<=200 for r in references):
            errors.append('Research card independent acceptance missing')
    except (KeyError,TypeError,AttributeError):
        errors.append('Invalid release extension acceptance schema')
    return errors

def validate(root=ROOT):
    errors = []
    try:
        backlog, raw = read_json(root / 'plans/implementation/backlog.json')
        ledger, _ = read_json(root / 'plans/implementation/execution-status.json')
        if digest(raw) != ORIGINAL_BACKLOG_SHA256 or ledger.get('backlog_sha256') != ORIGINAL_BACKLOG_SHA256:
            raise ValueError('Original backlog binding mismatch')
        original = {c['id']: c for c in backlog['cards']}
        current = {c['id']: c for c in ledger['cards']}
        if len(original) != 89 or len(current) != 89 or set(original) != set(current):
            raise ValueError('Authoritative card inventory mismatch')
        required = {f'NSAI-{i:03}' for i in range(1, 33)}
        pending = list(required)
        while pending:
            for dependency in original[pending.pop()]['dependencies']:
                if dependency not in required:
                    required.add(dependency)
                    pending.append(dependency)
        for identity in sorted(required):
            card, specification = current[identity], original[identity]
            criteria = card.get('criteria', [])
            if card.get('accepted') is not True:
                errors.append(identity + ': independent acceptance missing')
            if card.get('dependencies') != specification['dependencies']:
                errors.append(identity + ': dependency declaration mismatch')
            unaccepted = card.get('unaccepted_dependencies')
            if unaccepted != []:
                errors.append(identity + ': unaccepted dependencies: ' + ', '.join(map(str, unaccepted or ['unspecified'])))
            actual_criteria = [c.get('criterion') for c in criteria]
            if actual_criteria != specification['acceptance_criteria']:
                errors.append(identity + ': original criterion inventory mismatch')
            unconfirmed = [
                f"{c.get('index', index + 1)}={c.get('status', 'missing')}"
                for index, c in enumerate(criteria)
                if c.get('status') != 'CONFIRMED'
            ]
            if unconfirmed:
                errors.append(identity + ': original criteria not confirmed: ' + ', '.join(unconfirmed))
        required_artifacts = (
            'evidence/implementation/release-admission.json',
            'evidence/implementation/release-foundation.json',
            'evidence/implementation/release-extension-acceptance.json',
            'evidence/implementation/release-canonical-security-scan.json',
            'evidence/implementation/canonical-security-scan-artifact.json',
        )
        missing_artifacts = [name for name in required_artifacts if not (root / name).is_file()]
        if missing_artifacts:
            errors.extend('Required admission artifact missing: ' + name for name in missing_artifacts)
            return {'status': 'DENY', 'errors': errors, 'mutations_performed': False,
                    'scope': 'Foundation full-feature startup; existing qualified privacy-only runtime remains untouched'}
        admission, _ = read_json(root / 'evidence/implementation/release-admission.json')
        if admission.get('backlog_sha256') != ORIGINAL_BACKLOG_SHA256 or admission.get('ledger_sha256') != digest((root / 'plans/implementation/execution-status.json').read_bytes()):
            errors.append('Independent admission ledger/backlog mismatch')
        snapshot = source_snapshot(root)
        if admission.get('source_hashes') != snapshot:
            errors.append('Current deployable source snapshot mismatch')
        snapshot_sha = digest(json.dumps(snapshot, sort_keys=True, separators=(',', ':')).encode())
        expected = admission.get('identity', {})
        if expected.get('source_sha256') != snapshot_sha:
            errors.append('Independent receipt source identity mismatch')
        extension,extension_raw=read_json(root/'plans/implementation/release-validation-extension.json')
        if digest(extension_raw)!=RELEASE_EXTENSION_SHA256:
            errors.append('Appended checklist specification changed without requalification')
        extension_evidence,extension_bytes=read_json(root/'evidence/implementation/release-extension-acceptance.json')
        reference_hash=digest((root/'docs/implementation/REFERENCE_RESEARCH_EXTENSION.md').read_bytes())
        errors.extend(validate_extension_acceptance(extension,extension_evidence,reference_plan_sha256=reference_hash))
        if extension_evidence.get('source_sha256')!=snapshot_sha:
            errors.append('Appended checklist source identity mismatch')
        if admit_receipt(admission.get('release-extension',{}).get('receipt',{}),extension_bytes,expected)['status']!='PASS_SCOPED':
            errors.append('Appended checklist content-bound receipt missing')
        for name in ('foundation', 'canonical-security-scan'):
            bundle = admission.get(name, {})
            # Fixed locations prevent caller-selected PASS substitutes or traversal.
            evidence, payload = read_json(root / f'evidence/implementation/release-{name}.json')
            receipt = bundle.get('receipt', {})
            if admit_receipt(receipt, payload, expected)['status'] != 'PASS_SCOPED':
                errors.append(name + ': missing fresh content-bound scoped receipt')
            if evidence.get('independent_review') is not True or evidence.get('source_sha256') != snapshot_sha:
                errors.append(name + ': independent current-source review missing')
            if name == 'foundation' and (evidence.get('accepted_cards') != sorted(required) or evidence.get('all_original_criteria_and_dependencies_accepted') is not True):
                errors.append('Foundation acceptance evidence incomplete')
            if name == 'canonical-security-scan' and (evidence.get('canonical') is not True or evidence.get('verdict') != 'PASS' or evidence.get('unresolved_required_findings') != 0 or not evidence.get('canonical_artifact_sha256')):
                errors.append('Canonical security scan not clear')
        # A canonical scan JSON body alone is insufficient: retain and bind actual artifact bytes.
        scan, _ = read_json(root / 'evidence/implementation/release-canonical-security-scan.json')
        artifact = (root / 'evidence/implementation/canonical-security-scan-artifact.json').read_bytes()
        if not artifact or digest(artifact) != scan.get('canonical_artifact_sha256'):
            errors.append('Actual canonical scan artifact missing or mismatched')
    except OSError as error:
        path = Path(error.filename) if error.filename else None
        try:
            location = path.relative_to(root).as_posix() if path else 'unknown path'
        except ValueError:
            location = str(path)
        errors.append(f'Admission input unavailable: {location} ({error.strerror or type(error).__name__})')
    except (ValueError, KeyError, TypeError) as error:
        errors.append(f'Admission evidence invalid: {type(error).__name__}: {error}')
    return {'status': 'DENY' if errors else 'ADMITTED', 'errors': errors, 'mutations_performed': False,
            'scope': 'Foundation full-feature startup; existing qualified privacy-only runtime remains untouched'}

def main():
    report = validate()
    print(json.dumps(report, indent=2))
    return 1 if report['status'] == 'DENY' else 0

if __name__ == '__main__':
    sys.exit(main())
