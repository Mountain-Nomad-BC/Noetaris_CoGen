# Integrated direct OAuth: implementation and operator runbook

This extends the earlier provider/state foundation with canonical accounts, revocable browser sessions, explicit linking, logout cancellation epochs and the actual UI. The candidate is `sha256:bd13c6939057acc6d750a042b78cf9d50508d1528de1c7a2a64c20d53557e6c7`. No live migration, provider activation or cash-funded request has occurred. Real Google/GitHub callback qualification and independent acceptance remain open; individual-user content admission remains withheld.

## Changed-file map

| Files | Purpose |
| --- | --- |
| `src/nsai/oauth_accounts.py`; migrations `0034_oauth_accounts_and_sessions.sql`, `0035_oauth_browser_cancellation.sql` | Canonical provider bindings, hash-only opaque sessions, retained revocation/audit history, registry role revalidation and per-browser transaction-locked cancellation epochs. No email matching or automatic account merging. |
| `src/nsai/oauth_http.py`, `oauth_state.py`, `oauth_providers.py` | Maintained Authlib S256 code exchange; Google signed OIDC / GitHub verified stable identity; one-use bounded PostgreSQL state; exact origin/CSRF checks; signup/login/link/logout; HTTPS-only signed cookie. |
| `src/nsai/security.py`, `api.py`, `shared_rate_limit.py` | Preserve full registry validation and ownership; accept verified browser sessions; reject stale actor claims; count rejected authenticated API attempts toward ordinary limits; separate bounded three-window authentication admission, atomically shared through Redis. |
| `src/nsai/schema_contract.py`, `scripts/migrate.py`, `database/access-contract.json` | Explicit sealed RLS/grants for 50 tables and 70 functions; no app direct access to identity tables. |
| `assets/index.html`, `app.js`, `index.css` | Google/GitHub login/signup and explicit linking, local credential fallback, memory-only browser auth state, cross-tab view invalidation, stale-response protections and server-confirmed logout status. |
| `deploy/local/compose.oauth*.yaml`, `compose.edge-tls.yaml`, `deploy/nginx/{nginx.conf,local-tls.conf}`, `scripts/bootstrap_secrets.py` | Optional disabled-by-default provider overlays, independent signing/provider secret files and supplied local TLS certificates. Bootstrap does not rotate existing secrets. |
| `pyproject.toml`, `requirements.lock`, `LICENSES/oauth-*`, `scripts/lock_runtime.py` | Hash-pinned maintained runtime dependencies and licenses; corrected runtime-root/extra traversal and conflict refusal before lock writes. |
| `tests/test_oauth_*.py`, `oauth_*_pg_fixture.py`, `test_runtime_lock_roots.py`, `test_private_access_database.py`, `scripts/verify_ui_implementation.py` | Library, real database, packaged HTTP, cancellation-race, UI and regression coverage. Evidence-only HTTPS/restore/Redis runners are retained alongside their receipts. |

## Configuration and activation prerequisites

Default provider flags are false. Preserve that state until registered provider applications and approved HTTPS hosting are available. Layer `deploy/local/compose.coordination.yaml`, `compose.edge.yaml`, `compose.edge-tls.yaml`, `compose.oauth.yaml`, then the selected `compose.oauth-google.yaml` / `compose.oauth-github.yaml` over the root Compose configuration. Resolve the Compose model from the repository root before any future activation. These files prepare a candidate; they do not authorize replacing the running stack.

`NSAI_PUBLIC_ORIGIN` must be an operator-controlled HTTPS origin, with no path, query, fragment or user information. Valid nondefault TLS ports are supported. Register exactly `<origin>/auth/google/callback` and/or `<origin>/auth/github/callback`; the callback path is not selected by browser input. Google scopes are openid/email/profile; GitHub scopes read:user/user:email. Client IDs are configuration; client secrets and the distinct cookie signing secret must be supplied through absolute secret-file paths inside the container. Do not place secrets in YAML, browser storage, logs or source control.

The local TLS profile serves only localhost/127.0.0.1, defaults to loopback port 8443 and requires separately supplied certificate/key files. It is not a public-domain deployment profile. Match `NSAI_TLS_HOST_PORT` and `NSAI_PUBLIC_ORIGIN` when changing the port. Browser test certificates are ephemeral synthetic fixtures and must never become operator certificates. Cloud Run / Oracle ARM64 qualification remains separate.

`NSAI_OAUTH_SESSION_HOURS` defaults to 12 and is bounded to 1?24. Signed cookie lifetime is 24 hours, but PostgreSQL session expiry/revocation remains authoritative on every access. Cookie name is `__Host-nsai-session`, Secure, HttpOnly, SameSite=Lax, path `/`, no Domain. The cookie contains opaque NSAI session data and no provider access/refresh tokens. Signed cookies are not encrypted; do not add sensitive profile/token fields.

Authentication limits default to 60 requests/minute globally, 60 per peer and 20 per browser (`NSAI_AUTH_REQUESTS_PER_MINUTE`, `NSAI_AUTH_PEER_REQUESTS_PER_MINUTE`, `NSAI_AUTH_BROWSER_REQUESTS_PER_MINUTE`). They are separate from 120 ordinary API requests/minute/user and the daily AI generation quota. Redis admission fails closed when unavailable. Cloud Run requires shared Redis admission plus durable PostgreSQL operation coordination. Redis restart clears ephemeral request windows, not durable generation history.

## Identity and failure behavior

Signup creates a new ordinary canonical principal. Login requires an existing binding. Link requires the current verified individual identity and an exact expected-actor precondition; it cannot select an account by email. Existing local identity roles are reloaded from the registry and ownership IDs remain unchanged. Provider identities never grant admin roles. Existing sessions can continue when new provider login is disabled if the signing-secret configuration remains active; disabling a provider flag alone is not session revocation.

Browser mutations require exact Origin and CSRF proof. Explicit Bearer credentials retain precedence on protected API routes. Expected actor is only a restriction, never an authentication credential. Logout transactionally cancels in-flight state and revokes all sessions tied to that browser; another device remains independent. If logout cannot be committed, the client reports unconfirmed logout and retains the server revocation handle for retry. No provider failure fabricates a logged-in identity.

## Fresh evidence and practical limits

- `evidence/oauth-browser-tls/710f79c575224595a75b75f7a4d12d8e/receipt.json`: 17 scoped Chromium checks through real HTTPS, UI, API and PostgreSQL on the exact candidate. Only external provider boundaries are simulated; no NSAI API interception. Includes both providers, explicit linking, local identity preservation, cross-tab logout, mobile layout, cookie/storage boundaries and redacted proxy logs.
- `evidence/data-preservation/live-current-upgrade-2f58ce6165f04d54b7805d3ba8da40f8/receipt.json`: protected backup bytes verified, isolated current-schema upgrade, all 20 original sources and legacy record projections retained, real index/retrieval checks, concurrent idempotency and injected rollback. The original backup/live stack were not modified.
- `evidence/shared-coordination/26a7b3bc5d17440bb4320638f1b8a34a/receipt.json`: two real application processes admit exactly 60 authentication requests under a shared limit; global/peer/browser rejection is atomic, rejected attempts do not debit other windows, keys expire, and both ordinary/auth admission fail closed on Redis outage.
- `evidence/oauth-foundation/oauth-only-after.xml`: 89 focused checks pass, including 401 for forged/expired cookies in OAuth-only configuration.

The fresh 50-table restore passed: `evidence/operational-cost-recovery/2e3324c76c174a6bb58410e1cd4fdb3c/receipt.json` records exact row fingerprints, definitions, ACLs, sequences/settings and application-level active/revoked session checks. Full regression is tracked separately until its terminal receipt exists. None of these synthetic-provider checks proves production provider registration, real account permissions, native ARM64 behavior, full voice operation, system capacity, off-host disaster recovery, or independent certification.

## Rollback and custody

No live rollout occurred. Retain the prior candidate image and all original backup/manifests. Before any future live migration, capture and independently verify a protected backup including account bindings, active/revoked sessions, browser epochs, source originals, credit reservations and operation queues. A rollback uses the matching pre-upgrade database restore and exact retained image; do not point an older schema-sealed image at an upgraded database, delete/reverse migrations, or discard account/session/audit history. A later public rollout needs explicit release-gate evidence and a measured restore rehearsal.
