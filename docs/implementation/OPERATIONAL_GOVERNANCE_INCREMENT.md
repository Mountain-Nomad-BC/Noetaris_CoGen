# Operational accounting increment

Implemented against the [approved architecture](OPERATIONAL_ARCHITECTURE_DECISIONS.md). This is the first expansion increment, not the completed expansion or a rollout approval.

## Implemented behavior

- Validated operator settings include the approved 5-user, 120-request, per-user generation/ingestion, daily generation and GPU queue envelope. Only the request allowance and generation accounting checks are integrated in this increment; five-user admission, ingestion admission and the queue are still pending.
- `/v1/` ordinary request limits now honor `NSAI_REQUESTS_PER_MINUTE`, default 120. This limiter remains process-local until shared coordination is implemented.
- Existing transactional inference reservation now applies `NSAI_GENERATIONS_PER_DAY=20`, `NSAI_GENERATIONS_PER_USER=1` and `NSAI_GPU_ACTIVE_JOBS=1`. The existing project policy remains an additional ceiling. The same PostgreSQL policy-row lock serializes workers. Only an actual inference reservation adds a generation; retrieval and streamed events do not create reservation rows.
- Additive migration 0030 provides durable cost accounts, idempotent reservations, settlements and append-only application-inaccessible events. Cash begins at USD 20 with USD 5/10/5 bucket allocations. AMD/Evolus credit accounts are distinct, unit-labeled and disabled until configured. No currency conversion is inferred.
- Reservations count against exposure immediately. Unknown outcomes have no automatic expiry refund. Settlements record actual usage even on overrun, then freeze further account admission. Integer estimates round upward; floats and ambiguous numeric configuration are rejected.
- `GET /v1/admin/costs` exposes authoritative account limits, reserved/spent units, enabled state and 75/90/ceiling alerts to administrators. Other roles and anonymous users cannot inspect the ledger tables or sequence. Individual-user HTTP admission remains closed.

Paid-provider dispatch, durable provider idempotency/outbox, real price/usage metering, provider-specific switches, controlled overrides and administrative cap synchronization remain unfinished. These primitives do not independently cap charges from requests that have not been integrated with them. No paid request was made during this increment.

## Configuration

`src/nsai/operational_policy.py` lists every operator variable and validation bound. Local compute has no cumulative token ceiling; existing context, output and resource limits remain. Credit-limit values are provider units, not dollars. Environment cash policy validates allocations but does not silently rewrite authoritative database caps; reviewed administrative updates are a subsequent card. Clients cannot choose limits, account balances or role overrides.

## Exact artifacts and evidence

API candidate: `sha256:0c68b83e1f9fccc9a12ee10fb82b8a6a94a036836c2a433a3522fca89bb6700d`.

The [increment receipt and 13-file runtime/test map](../../evidence/operational-governance/receipt.json) records before/after runtime hashes, explicit test additions and evidence paths. Additional documentation changes are this report, the approved architecture record, plan N, its expansion tracker and workspace progress. No source assets or private originals were removed.

- [Full regression](../../evidence/private-access/198a629aa3e94a3fa77bd71b810c6f46/receipt.json): 1,117 tests, zero failures/errors/skips, exact collected coverage, packaged source verified, inputs unchanged and cleanup complete.
- [Real-service browser](../../evidence/grounded-application/b05d61ef218c4ed9b818abea113bb99c/grounded-receipt.json): current API/database/parser/OCR/encoder/CPU-model workflow, DPR 2, no API interception; private-user content remains withheld.
- [Actual legacy-library copy](../../evidence/data-preservation/live-current-upgrade-5ef6e808ec464f08a1b5dba254a7c751/receipt.json): migration through 0030 preserves every original historical column value and all 20 source hashes, then passes real-encoder backfill/publication/retrieval, concurrent idempotency and injected preparation rollback.
- [Synthetic cost-ledger recovery](../../evidence/operational-cost-recovery/3fc7d35d5aa84af0803fa1a12928eae3/receipt.json): all 43 tables, access definitions/ACLs and exact sequence seeds/state/settings match after fresh-container restore and standard role-privilege convergence. The actual packaged app verifies settled cash, unresolved exposure and separate AMD/Evolus balances. No real expenditure or user data is in this fixture.
- `scripts/check_compose.py` passes for the existing profile; no Cloud Run deployment or ARM64 runtime is qualified by that check.

The initial ledger recovery receipts `3000888b...` and `86019767...` remain FAIL. The second isolates sequence ACL differences when the standard role-privilege convergence step was omitted. The later run includes that runbook step and passes; no row mismatch or invoice loss was observed. All owned containers/networks were cleaned up. These are quiescent recovery checks, not host power-loss, off-host backup, PITR or RTO/RPO acceptance.

## Rollback and deployment boundary

The live image, database, volume and protected backups were not modified. The newly built image is a local candidate only. No rollback of live data is necessary for this increment.

Migration 0030 is additive and forward-only. Do not drop accounting tables, erase outstanding reservations or edit the migration journal to run an older image. Older candidates enforce a different schema seal and may deliberately refuse a newer schema. Prefer a reviewed forward repair. If rollback is necessary after future deployment, retain the affected database and financial events, reconcile potentially dispatched requests, restore a verified pre-upgrade backup into a separate cluster, verify originals/rows/ACLs/sequences and match it to its exact previous application image. Post-backup writes must be explicitly preserved or reconciled before any cutover; never silently discard them.

For candidate-only testing, prior images remain retained by `scripts/build_candidate.py` under their recorded hold tags. Repointing the candidate alias does not authorize deploying it or changing a live database. Exact cloud configurations, TLS/network/secret integration, ARM64 builds, real OAuth callbacks and local voice remain next increments. The section-4 comprehensive audit checkpoint has not been reached.
