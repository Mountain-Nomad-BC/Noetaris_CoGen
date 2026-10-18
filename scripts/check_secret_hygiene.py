"""Exact local secret leakage check + narrow key patterns; not a full credential scanner."""
from pathlib import Path
import hashlib
import json
import re


def main():
    from datetime import datetime,timezone

    ROOT=Path(__file__).resolve().parents[1]
    secrets=[p.read_bytes().strip() for p in (ROOT/'secrets').glob('*.txt')]
    findings=[];count=0
    for path in ROOT.rglob('*'):
        if not path.is_file() or any(part in {'.venv','secrets','state','__pycache__','.pytest_cache','.git'} for part in path.relative_to(ROOT).parts):continue
        if path.suffix.lower() in {'.png','.pdf','.zip','.pyc'}:continue
        data=path.read_bytes();count+=1
        if any(secret and secret in data for secret in secrets):findings.append(dict(file=path.relative_to(ROOT).as_posix(),kind='local-secret-value'))
        if re.search(rb'\bsk-proj-[A-Za-z0-9_-]{40,}',data):findings.append(dict(file=path.relative_to(ROOT).as_posix(),kind='possible-provider-key'))
    report=dict(status='PASS' if not findings else 'FAIL',captured_at=datetime.now(timezone.utc).isoformat(),scanned_files=count,findings=findings,
        limitation='Checks exact current local secret values and narrow provider key patterns, not complete secret detection')
    (ROOT/'evidence/implementation/secret-hygiene-current.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2));raise SystemExit(1 if findings else 0)


if __name__ == "__main__":
    main()
