# Deployment and rollback

Current verdict: DENY. These are preparation commands, not authority to publish. Run from the repository root. The local isolated Docker review URL is http://127.0.0.1:8790.

## Local review

```powershell
.\.venv\Scripts\python.exe scripts/start_integration.py --model-config state/integration/gemma-cpu.json
.\.venv\Scripts\python.exe scripts/qualify_integration_regressions.py
node state/integration/browser-navigation.mjs
node state/integration/browser-live-operations.mjs
.\.venv\Scripts\python.exe scripts/check_deployment_stages.py
```

## Firebase preparation

Copy `deploy/firebase/config.example.json` into a private configuration file and replace every placeholder with owner-confirmed public values. Build with matching `VITE_NOETARIS_MODE=live`, `VITE_API_ORIGIN`, `VITE_APP_ORIGIN` and `VITE_DEPLOYMENT_SITE`. Run `npm --prefix frontend/noetaris run build`, then `python scripts/prepare_firebase.py --config <private-config.json>`. The resulting state/firebase-preparation bundle contains only allowlisted static assets, Hosting configuration and hashes. It is PREPARED_NOT_DEPLOYED. Do not upload the whole repository or evidence directory.

After independent acceptance and explicit publication approval, use Firebase CLI from the prepared bundle with the confirmed project and site (`firebase deploy --only hosting --project <confirmed-project>`). Verify production-origin Chromium and Firefox OAuth/cookie/CSRF and deep-link behavior. Keep the previous qualified Hosting release available for rollback through Firebase Hosting release history. A preview URL does not qualify production cookies or private-user content.

## OCI preparation

Complete `deploy/oci/deployment.env.example` externally with exact ARM64 registry digests, owned origins and restricted secret paths. Render the Nginx host placeholder to the approved API hostname. Keep secrets under /etc/noetaris with least privilege. Run `python scripts/check_oci_profile.py --env-file <private-env> --with-oauth`; it deliberately denies startup while the canonical release gate denies admission. Do not bypass it. Inspect the Compose base plus Google/GitHub OAuth overlays and `deploy/oci/noetaris.service` before installation on actual Linux.

After approved provisioning and acceptance, install the reviewed candidate at /opt/noetaris/current and restricted config at /etc/noetaris. The unit runs both release/profile checks before Compose startup. Expose HTTPS only; keep PostgreSQL, parser and encoder private. Prove firewall/TLS/least privilege and actual ARM64 readiness before public traffic.

## Migration and recovery

Before any approved production change, take a quiescent encrypted off-host backup, capture exact image/config/schema identities, and restore it to an owned disposable target. Synthetic local restore receipts do not qualify production backups or concurrent-write/PITR recovery. Do not copy integration data into production. Confirm migration compatibility before promotion.

Rollback retains the previous qualified immutable image set and matching configuration. Stop affected services, restore the prior reviewed release/config, and resume only after health and data compatibility checks. Never use `down --volumes` on production. Schema rollback may require an approved restore and entails data loss since backup; no automatic destructive rollback is supplied. Retain failed evidence and monitor audit integrity, queues, memory and provider allowance.
