# Direct OAuth provider and durable state increment

This increment implements the Google/GitHub transport and durable callback-state foundations. It does not yet expose OAuth login routes, create provider-bound NSAI accounts, issue browser sessions, or qualify real provider callbacks. Existing identities, ownership, permissions and the individual-user content admission gate remain unchanged. No provider credentials or cash-funded services were used.

## Changed files

| Files | Behavior |
| --- | --- |
| `src/nsai/oauth_providers.py` | Disabled-by-default provider configuration, fixed official endpoints, operator-controlled HTTPS callback origin, secret-file credentials, Authlib S256 PKCE and signed Google OIDC validation; GitHub stable numeric identity with verified primary email. No email-based account merging or provider-assigned roles. |
| `src/nsai/oauth_state.py` | PostgreSQL-backed Authlib cache with browser binding, five-minute lifetime, bounded keys/payloads and atomic one-time consumption. Refuses authenticated request-context privilege elevation. |
| `database/migrations/0033_durable_oauth_state.sql` | Additive ephemeral state table with RLS, no direct app access, three sealed service-only functions and bounded global/per-browser admission. Does not modify content or existing principals. |
| `src/nsai/schema_contract.py`, `scripts/migrate.py`, `database/access-contract.json` | Explicit RLS/function grants and regenerated clean-database access contract. |
| `pyproject.toml`, `requirements.lock`, `LICENSES/oauth-*` | Authlib 1.9.1 plus pinned cryptography/joserfc/cffi/pycparser closure and upstream license files. Existing runtime locks retained. |
| `tests/test_oauth_providers.py`, `tests/test_oauth_state.py`, `tests/test_oauth_state_database.py` | Real maintained-library PKCE/code exchange and signed-token negatives; actual isolated PostgreSQL expiry, browser binding, single-use, capacity, permission and conflict checks. |

## Evidence

`evidence/oauth-foundation/provider-state-tests.xml`: **80 passed**, including existing local-identity and content-gate regressions. Tests use synthetic provider responses and locally generated RSA signatures, not real provider accounts. The earlier `provider-tests.xml` records a premature run before isolated dependency installation completed; `provider-tests-installed.xml` passed 25 checks after installation. Both historical artifacts are retained.

`evidence/private-access/6fc911ad0e9146c29c4020a808480424/receipt.json`: **1,175 passed, zero failures/errors/skips**, exact packaged source verified, source unchanged and owned cleanup complete. The run was substantially slower than its preceding baseline. The scoped same-host migration diagnostic `evidence/oauth-foundation/migration-timing-a7d034f10cf64ea6a1a21857eb0988b2/receipt.json` measured the previous journal at 6.83 seconds and current journal at 5.05 seconds; it does not explain the broader timing variance or establish application latency/capacity acceptance.

`evidence/oauth-foundation/dependency-provenance.json`: downloaded Windows and Linux ARM64 wheel hashes verified against exact-version PyPI metadata. This establishes artifact availability, not native ARM64 execution or package-risk clearance.

`evidence/access-contract-builds/059e5e21f38146459ff66000ea45b793/receipt.json`: clean owned PostgreSQL contract generation passed; cleanup verified; live resources untouched.

Candidate build `4ffe2ba0985c4e2593e7ce58ddf77a43` passed:
`sha256:e384740ba3871fcccd3dbdbf70165d09c1afe3a0d6dc01beb00e925cb4ffee67`.
Previous candidate `sha256:04ce9e0f911eb8fa22418136ed861c6296ed5d2ed4828c1162c23b0d2368fee6` retained under its exact `nsai-candidate-hold` tag. Neither was deployed to the live stack.

`evidence/oauth-foundation/packaged-df3ecabcfd8e48ffa49db02ce06d2c0e/receipt.json`: the exact candidate imports all five pinned OAuth distributions and generates both S256 authorization requests with Docker network disabled. Cleanup verified. This is a packaged-library smoke check, not an actual provider callback.

`evidence/operational-cost-recovery/9421d5ee633a4c6fbaa4e327372b1aeb/receipt.json`: fresh synthetic restore passes exact fingerprints for all 45 tables, access definitions/ACLs, sequence state/settings and standard role privilege convergence. The packaged app verifies retained AMD credit history, unresolved reservations, the durable queue and one-time consumption of restored OAuth state. Cash stays disabled. Both clones were cleaned up; this is not an off-host or host-power-loss recovery qualification.

## Remaining integration and rollback

Continue with canonical provider bindings, explicit linking, revocable opaque browser sessions, CSRF/origin checks, login/signup/logout UI and endpoints, shared unauthenticated admission, provider cancellation/error handling and actual configured callback qualification. Do not treat this foundation as completed OAuth or private-access certification.

Rollback before activation is to keep provider settings disabled and use the retained prior candidate against its matching pre-upgrade clone. Do not point an older schema-sealed image at an upgraded database or reverse/delete migration history. A future live upgrade must first capture and verify a protected backup, including all new tables; no live migration occurred in this increment.

After that full-suite snapshot, operator maintenance `scripts/lock_runtime.py` was corrected to derive runtime roots from pyproject, honor extras discovered later in dependency traversal and reject installed-version conflicts before rewriting the lock. Three new focused checks pass (`runtime-lock-after.xml`); `runtime-lock-before.xml` retains the missing-helper gap demonstration. The offline exact-image check `evidence/oauth-foundation/lock-closure-9d765403c80a4b8b9923a40f85cc3e4f/receipt.json` confirms all 28 packaged Linux distributions match the existing lock. No lock or global host package was rewritten, and the packaged application is unchanged by this operator-only fix.

References: [Authlib web clients](https://docs.authlib.org/en/latest/oauth2/client/web/), [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect), [GitHub authorization code and PKCE](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps).
