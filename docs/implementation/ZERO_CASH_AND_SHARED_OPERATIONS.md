# No cash and shared operational controls

The user's latest instruction prohibits cash use. Earlier USD 20 allocation decisions are historical context for an admin demonstration, not authority to spend. This increment is implemented and tested; the full expansion remains an active objective.

## Implemented

Migration 0031 preserves historical accounting and disables cash accounts. Both the Python reservation seam and the SQL reservation function reject new cash reservations, including zero-value requests and accounts an owner has manually re-enabled. Historical settlement/reconciliation remains available so old records cannot silently disappear. AMD/Evolus credits remain separate, disabled until verified and configured; no actual provider credits were used by tests.

The governance view now has an admin-only “Cost governance demonstration” panel. Its endpoint returns clearly labeled illustrative values without reading or modifying monetary ledgers. Actual usage is governed by ordinary request rates, per-user daily generation allowances and operation concurrency. Local computation has no cumulative token allowance. Model configuration rejects cash funding and requires an explicit free/credit classification for remote endpoints; no remote provider is activated.

The optional coordination Docker overlay enables Redis-backed atomic request windows and durable PostgreSQL operation admission. Two independent processes share one principal's 120-request allowance. Other principals have separate allowances. Redis errors fail closed with 503; request handlers do not revert to per-process allowances. Redis uses authenticated internal networking, no exposed port, non-root/read-only containers, tmpfs configuration, no eviction, bounded memory and logs. Passwords are not command-line arguments or key contents. Redis restarts clear ephemeral request windows; durable daily generation records remain in PostgreSQL.

Migration 0032 adds durable generation/ingestion admissions. A short global transaction lock bounds distinct principals with live operations, per-user ingestion/generation operations, active inference operations and the FIFO waiting queue. Defaults are 5 live operational principals, 1 operation of each kind per user, 1 global generation slot and 10 waiting generation operations. A queued request waits at most 30 seconds and receives 429 when capacity is unavailable. Ten-minute leases fence abandoned requests; this is request admission, not proof that an external GPU has physically stopped. Long-lived streams need renewal before using these leases. Completion and cancellation release admissions; a cancelled database await waits for its in-flight transaction outcome before cleanup to avoid late orphan commits.

The existing base compatibility profile leaves operation admission disabled. `deploy/local/compose.coordination.yaml` enables it and shared request limiting. Cloud Run startup fails unless both are configured. Existing private-user HTTP admission remains closed; resource-coordination flags do not open content access.

The Nginx edge overlay removes the API's direct published port. The gateway alone publishes a loopback port, with a front network separated from its internal API network. It supports dynamic Docker DNS and multiple backends, rejects unapproved Host values, disables automatic request replay/cache/buffering, preserves application body limits and forwards WebSocket upgrade headers. Non-root/read-only operation uses bounded tmpfs for all temporary paths. Access logs contain route families and timings, not query strings, source identifiers, client addresses or credentials. The local configuration is not public TLS or an OAuth deployment qualification.

## Fresh evidence

Current API candidate: `sha256:04ce9e0f911eb8fa22418136ed861c6296ed5d2ed4828c1162c23b0d2368fee6`.

- [1,138 tests](../../evidence/private-access/9807d11b08ae4f61a28d3f37a69eb0d1/receipt.json), zero failures/errors/skips, packaged source verified and exact collected coverage.
- [Real-service browser with operation coordination enabled](../../evidence/grounded-application/af05a43649e040f2a74abb905008ddca/grounded-receipt.json), including API/database/parser/OCR/encoder/local model. No API interception or private-gate bypass.
- [Redis concurrency and outage](../../evidence/shared-coordination/10e19de527e6485ab42d9a5a15f1a65a/receipt.json): two independent processes admit exactly 120 combined requests, another principal retains 120, and removal of Redis yields HTTP 503. The current API image is recorded in this fresh shared-limiter receipt.
- [Nginx two-backend routing](../../evidence/edge-qualification/c24593511f5049dc86cf77bf1452ec79/receipt.json): both actual API backends observed, unapproved Host disconnected, original API 413 body bound retained and synthetic query/credential canaries absent from access logs.
- [All-44-table quiescent recovery](../../evidence/operational-cost-recovery/545e339e6f40441ea91760f543cfd210/receipt.json): table rows, access definitions/ACLs and sequence seeds/state/settings match; packaged application verifies disabled cash, credit history, unresolved reservations and preserved queue state.
- [Existing 20-source library](../../evidence/data-preservation/live-current-upgrade-a4789e599cba4722880448eda696870d/receipt.json): current migrations preserve every historical column value and all original hashes, followed by real-encoder publication/retrieval, concurrent preparation idempotency and injected rollback.

The [aggregate receipt and 27-file hash map](../../evidence/zero-cash-operations/receipt.json) links the exact artifacts and limits. No live service, original, database volume or protected backup was changed. All owned test containers/networks were cleaned up. Failed proxy runs remain retained: they exposed missing tmpfs paths and fixture network/readiness ordering, which the later checks explicitly correct.

## Configuration and rollback

Validate, without starting services:

```powershell
docker compose -f compose.yaml -f deploy/local/compose.cpu.yaml -f deploy/local/compose.coordination.yaml -f deploy/local/compose.edge.yaml config --quiet
```

The existing release guard remains mandatory before persistent deployment or migration. Bootstrap now defines a Redis password for future authorized startup; it was not run against existing secrets. Do not expose Redis/database ports or treat free-tier/budget alerts as spend permission. Public deployment, OAuth configuration, voice, provider routing and the remaining semantic/business features are subsequent increments.

Migrations 0031/0032 are additive. Do not drop historical ledger rows, queued operations, originals or migration-journal entries to revert an image. Prefer a forward repair. A rollback after future deployment requires a separately restored, verified pre-upgrade database paired with its exact previous application, preserving and reconciling post-backup writes and outstanding operations before cutover. The protected original backups remain unchanged; no live rollback is necessary for these candidate-only tests.

## Remaining objective

Direct Google/GitHub OAuth, local-first ASR/TTS and acoustic qualification, structured business ingestion/analysis/charts, semantic dossiers/canonical identities/typed graph routing, scoped knowledge/memory/procedures, verified optional provider adapters, approved fallback, public/ARM64 deployment configuration and independent assurance are not completed by these tests. Authlib dependency wheels are staged for Windows and Python 3.12 ARM64; wheel availability is not an ARM64 runtime or OAuth callback test. The section-4 audit notification/independent-report prerequisites remain in force. No certification or rollout approval is claimed.
