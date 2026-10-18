#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m compileall -q src scripts
python -m pytest -q
python scripts/validate_compose_security.py
python scripts/release_audit.py .
printf 'Static checks passed; runtime Docker/AMD still must be verified.\n'
