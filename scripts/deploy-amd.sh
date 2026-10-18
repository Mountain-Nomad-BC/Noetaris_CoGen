#!/bin/sh
# Prepared only; requires admitted native AMD host and digest/model/license environment.
set -eu
cd "$(dirname "$0")/.."
PYTHON="${NSAI_PYTHON:-.venv/bin/python}"
"$PYTHON" scripts/amd_preflight.py
"$PYTHON" scripts/bootstrap_secrets.py
"$PYTHON" scripts/validate_compose_security.py
"$PYTHON" -m pytest -q
docker compose -f compose.yaml -f deploy/amd/compose.amd.yaml --profile amd config --quiet
docker compose -f compose.yaml -f deploy/amd/compose.amd.yaml --profile amd up -d --build --wait db parser
"$PYTHON" scripts/migrate.py
docker compose -f compose.yaml -f deploy/amd/compose.amd.yaml --profile amd up -d --build --wait api vllm
echo 'AMD services launched; actual GPU utilization, inference and performance evidence still required.'
