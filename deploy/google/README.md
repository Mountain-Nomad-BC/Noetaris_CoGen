# Historical provisional target

Superseded by the operator contract: use Firebase Hosting -> OCI ARM64 -> protected AMD, with optional Evolus. This Compute Engine draft is retained for history and must not be used as the selected deployment plan. See docs/deployment/DEPLOYMENT_AND_ROLLBACK.md.

# Google deployment preparation

The current preparation target is a private Linux Compute Engine VM running the six-service Docker Compose application. This preserves the existing service layout while the Google target and two database services are being specified. No VM, firewall, registry repository or billable resource is created by the preparation command. Cloud Run/GKE deployments are not implied by this bundle.

## Prepare a reviewable bundle

1. Identify the Google project, zone, instance, budget and domain/identity requirements. Install and qualify Docker/Compose on the intended Linux host. Keep the instance private while commissioning.
2. Publish reviewed images to your project's Artifact Registry only when authorized. Record the **registry** digest of each image. A local Docker image ID is not proof of its registry digest. Google documents [image naming, authentication and pushing](https://docs.cloud.google.com/artifact-registry/docs/docker/pushing-and-pulling).
3. Copy `compute.example.json` into ignored `state/google-deployment/config.json`; replace every project/image placeholder with actual registry identities and the intended Linux artifact paths. The renderer rejects mutable tags, foreign project registries and model paths outside `/srv/noetaris/models/`.
4. Run `.venv\Scripts\python.exe scripts/prepare_google_deployment.py --config state/google-deployment/config.json` from the project root. It writes a new `compose.json` and `preparation.json` under `state/google-deployment/<run>/`. The result intentionally remains **NOT_READY** while commissioning and independent release admission are incomplete. It does not run Compose or deploy anything.
5. Transfer and verify the licensed Gemma artifact/checksum and complete MiniLM artifacts independently. The bundle copies neither model bytes nor corpus/database contents. Install newly commissioned secrets by their manifest names under `/etc/noetaris/secrets/`; source keys never enter the bundle. Do not reuse shared local demo role tokens for public production access.
6. Commission an owned database with the exact journal/schema and least-privilege role contract; rehearse target backup/restore and audit checks. The renderer is not a migration tool. Do not point a migration command at either external database until its intended role, ownership and backup plan are confirmed.
7. Commission OAuth/OIDC, TLS, cloud IAM, networking, monitoring, persistent storage, retention and independent release/security/rights acceptance before public traffic. The generated UI binds only `127.0.0.1:8790` and other service ports remain private. Do not simply change this to `0.0.0.0` to bypass commissioning.

For private commissioning access, use an authorized SSH tunnel, for example `gcloud compute ssh INSTANCE --project PROJECT --zone ZONE --tunnel-through-iap -- -N -L 8790:127.0.0.1:8790`. This requires the relevant IAM/firewall/OS Login setup; see Google's [IAP SSH documentation](https://docs.cloud.google.com/compute/docs/connect/ssh-using-iap). It is not public deployment admission.

## Two external database services

Their service names and roles are not yet supplied. Do not assume both are PostgreSQL or replace the application's owned transactional database with a vector/document service. Record each service's role (primary transactional storage, vector search, analytics, archive, etc.), provider, endpoint, database/schema, authentication, TLS CA, network access, data region, migrations and backup policy before configuring an adapter.

The primary PostgreSQL connector now supports `NSAI_DB_HOST`, `NSAI_DB_PORT`, `NSAI_DB_NAME`, `NSAI_DB_USER`, `NSAI_DB_PASSWORD_FILE`, `NSAI_DB_SSLMODE` and `NSAI_DB_SSLROOTCERT_FILE`. Nonlocal database endpoints require `verify-full` and a readable CA certificate file; TLS downgrade and multi-host/DSN values are rejected. CA changes invalidate idle-pool identity. Actual external-service compatibility and TLS handshakes have not been qualified. The second service has no invented adapter or replicated writes.

## Evolus setup

Copy `evolus.example.json` into ignored `state/integration/evolus.json`, replacing every binding with the actual application, workflow, agent and extractor identity. Set the exact SHA-256 of the verified workspace payload schema. These are configuration bindings, not credentials; the sample intentionally fails validation until completed.

Run `.venv\Scripts\python.exe scripts/check_evolus_setup.py --config state/integration/evolus.json`. The credential defaults to ignored `secrets/evolus_api_key.txt`. This command validates bounded local configuration without partner requests, printing neither keys nor file contents. A zero exit code means only that local configuration is complete; `commissioned` and `dispatch_enabled` remain false.

The isolated Docker launcher mounts available partner credentials into the API only, read-only, and mounts valid Evolus bindings if present. `/app/integrations` reads redacted server-side setup status. Refreshing makes no Evolus request. The configured workflow payload/output, credit allowance, durable execution accounting, retry/unknown outcomes, source-export authorization and end-to-end workspace execution still require commissioning. Do not enable generic corpus export or claim that a credential/configuration check is a working Evolus workflow.

## Remaining frontend features

Model status, integration setup, measured analytics/runtime observations, audit, security policy and effective settings now have live read-only API screens with the existing backend roles. Workflow/agent catalogs and execution, templates, evaluations/evidence tooling and other preview-backed features still need actual governed backend implementations. Their unavailable boundaries remain in place; a route render is not feature acceptance.
