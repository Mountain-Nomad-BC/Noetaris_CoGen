"""Read-only starter-kit checksum verification with explicit input handling."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def verify(kit: Path):
    manifest = kit / 'MANIFEST.sha256'
    if not manifest.is_file():
        raise FileNotFoundError(f'Kit manifest not found: {manifest}')
    results = []
    for line in manifest.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        name = name.lstrip('*').strip()
        path = kit / name
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        results.append(dict(file=name, passed=actual == digest))
    return dict(
        status='PASS' if results and all(r['passed'] for r in results) else 'FAIL',
        checked_files=len(results),
        results=results,
        limitation='Self-contained kit checksum consistency, not a signed authenticity proof',
    )


def main(argv=None):
    root = Path(__file__).resolve().parents[1]
    default = root.parent / 'NSAI_LOCAL_AI_DOCKER_FIRST_BUILD_KIT_2026-10-12' / 'NSAI_Local_AI_Docker_First_2026-10-12'
    parser = argparse.ArgumentParser()
    parser.add_argument('--kit', type=Path, default=default, help='Starter kit directory containing MANIFEST.sha256')
    args = parser.parse_args(argv)
    try:
        report = verify(args.kit.resolve())
    except (OSError, ValueError) as error:
        report = dict(status='BLOCKED', checked_files=0, results=[], error=str(error), limitation='Input kit was unavailable or malformed')
    evidence = root / 'evidence' / 'raw' / 'kit-integrity.json'
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
