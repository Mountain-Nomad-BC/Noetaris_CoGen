# Local deployment

**Historical deployment runbook — not current operating instructions.** As of 2026-10-17 11:48 EDT, the existing Docker services have no host-published ports, host `/healthz` is unreachable, the release gate is **DENY**, and the runtime Compose overlay is unresolved. Do not run any startup, shutdown, build, migration, or recovery commands against the existing stack. See [current deployment state](implementation/DEPLOYMENT_STATE.md) and [Start here](../START_HERE.md). The procedures below are not current deployment evidence or approval.

The Ollama path below is retained as an alternative; runtime validation remains pending.

Use Docker Desktop Linux containers. Run `powershell -ExecutionPolicy Bypass -File scripts/start.ps1`
from the project root. The script installs into a project virtual environment, bootstraps secrets without
printing values, checks manifests/config, starts DB, applies additive migrations, runs tests, builds
application/parser/model services, waits for health, downloads the model, and runs actual acceptance.

Open `http://127.0.0.1:8787`. Operator token: `secrets/api_token.txt`; reviewer:
`secrets/reviewer_token.txt`; admin: `secrets/admin_token.txt`; viewer: `secrets/viewer_token.txt`.
Keep credentials private. On Windows run `scripts/protect-secrets.ps1` to restrict directory ACLs.
Do not use kit `first-run.ps1` or `local-start.ps1` for the upgraded schema; use this runbook.

Database uses a named volume and a separate non-superuser app identity. Migration executes using
the local DB owner through the host Docker CLI; no container receives a Docker socket. Preserve
the owner and app secrets: replacing password files does not rotate an initialized database role.
Back up before schema changes with the backup helper. Repeating migration is additive and idempotent.

Observe `docker compose -f compose.yaml -f deploy/local/compose.ollama.yaml --profile local-ai ps`.
Only API `127.0.0.1:8787` is published. API/parser/DB/model must be healthy before calling the system ready.
Model downloads are external network activity; weights stay in a Docker volume and are not bundled.
Set `NSAI_LOCAL_MODEL` before startup to choose a supported Ollama model. Set limits with the admin UI.

Stop with `scripts/stop.ps1`. It preserves named volumes. Never add `-v` for routine shutdown.
For rollback, stop application services, retain immutable evidence and backups, and restore only in a
separate explicitly approved recovery environment. Prefer forward-compatible migrations over destructive
in-place rollback. This local deployment is not approved for internet exposure.

Testing and submission evidence are documented separately in `docs/submission/TESTING_AND_EVIDENCE.md`
and rendered in the application's Testing & evidence section.
