# Local first boot — Windows PowerShell and Linux

**Historical first-boot runbook — not current authorization to start this checkout.** As of 2026-10-17 11:48 EDT, the existing Docker stack has no host-published ports, authentication is unavailable, exact Compose provenance is unresolved, and release admission is **DENY**. The commands below install dependencies and start/build/migrate services; do not run them against the current persistent stack. See [current deployment state](../implementation/DEPLOYMENT_STATE.md) and [Start here](../../START_HERE.md).

## Preconditions

- Python 3.12+; Docker Desktop configured with WSL2/Linux containers on Windows, or current Docker Engine and Compose plugin on Linux.
- Ports: `127.0.0.1:8787` free, unless changed via `NSAI_HOST_PORT`.
- Fresh cloned folder with **no copied Remy source**; synthetic demo input only.
- Running Docker Desktop/Engine. You do **not** need AMD GPU to test baseline.

### Windows (exact order)

```powershell
# From extracted package root
python --version
python scripts/preflight.py
python -m pip install -e ".[test]"
powershell -ExecutionPolicy Bypass -File scripts/local-start.ps1
docker compose ps
python scripts/verify_local.py
python -m pytest -q
python scripts/validate_compose_security.py
```

Visit `http://127.0.0.1:8787`; load local token from `secrets/api_token.txt` into the authorization field. Do not share this token or use it for a public demo. The local start script creates two random secrets with safe file creation semantics and won't overwrite them on subsequent starts.

### Linux (exact order)

```bash
python3 --version
python3 -m pip install -e '.[test]'
python3 scripts/bootstrap_secrets.py
cp -n .env.example .env || true
python3 scripts/preflight.py
docker compose config --quiet
docker compose up -d --build
docker compose ps
python3 scripts/verify_local.py
python3 -m pytest -q
python3 scripts/validate_compose_security.py
```

The Linux host must have Docker daemon running and correct access. Do not run `chmod 666 /var/run/docker.sock` to bypass permissions.

## Smoke verification commands

```bash
docker compose logs --tail=80 api
docker compose ps
curl -sS http://127.0.0.1:8787/healthz
curl -sS http://127.0.0.1:8787/readyz
# Deliberate negative auth test; returns 401
curl -i -H 'Authorization: Bearer wrong' http://127.0.0.1:8787/v1/claims
# Isolated smoke service (does NOT safely execute generated code)
docker compose --profile sandbox run --rm sandbox-smoke
```

`verify_local.py` sends synthetic conflicting docs, tests auth reject/accept and reports conflicts. Before/after a restart, the document counts must remain stable (`docker compose restart`). A `docker compose down` is safe for persistent demo data **unless** you add `-v`, which destroys the named DB volume. Never use `docker compose down -v` when preserving data.

## Troubleshooting

| Symptom | Test | Action |
|---|---|---|
| Docker daemon unavailable | `docker version` | Start Docker Desktop/Engine, verify Linux containers |
| Port 8787 busy | `docker compose ps` / `netstat` | Change `NSAI_HOST_PORT` in `.env` and use same port for smoke |
| DB unhealthy | `docker compose logs db` | Check secret file and volume permissions; never delete volume as first fix |
| API 503 ready | `docker compose logs api` | Verify DB health and service secret mount |
| API 401 | Header/token | Use local token file; avoid putting it in logs or screenshots |
| UI works but not model | `/v1/capabilities` | Expected; AMD vLLM not configured by default |
| Docker Compose can't parse `env_file.required` | `docker compose version` | Upgrade Compose plugin; do not silently strip security settings |
| Windows permissions on secrets | Windows ACL | Keep folder private and no shared repository export |

## Local stopping and reset

```powershell
powershell -ExecutionPolicy Bypass -File scripts/local-stop.ps1
```

Use `docker compose stop` to pause without removing containers, or `docker compose down` to remove containers while preserving the volume. Back up database before migration changes. For an intentional data reset, take a manual backup then delete volume explicitly and document why.

## Evidence to attach to Task BASE-04

Host and Compose version, `docker compose ps` and health logs, test output, synthetic claim/conflict counts, restart persistence counts. Do not archive credentials or full environment variables.
