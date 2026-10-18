# Historical governed audit authorization: schema0038

The Docker API candidate `bb6238af` and NOETARIS frontend `40c7da76` passed the scoped checks recorded in [the current evidence index](../../evidence/noetaris-integration/current-evidence.json). This is not release acceptance.

Migration0038 adds a restrictive audit SELECT policy. Governed audit entries must match their exact currently visible immutable governed record, document, origin, complete source dependencies and recognized event type. Revoking any required source hides the entry; regrant restores the same retained entry. Unknown or incomplete references remain withheld. Historical rows, rationales, source metadata and hashes are not rewritten. This does not retroactively certify their factual provenance.

Verification: 1,383 backend tests in one bounded two-worker run; 26 focused checks; 346 assertions through the exact Docker API/frontend pair; 70 frontend contracts from its retained build; 13 actual schema37-to38 upgrade checks; and a 50-table backup/restore comparison. The upgrade preserves existing rows and sequence state, adding the migration journal entry and policy. Reapplication is idempotent. Earlier failures and timeout receipts remain retained. The current single local inference case took31.975seconds; this is not a capacity or latency certification.

The44 original imported UI files and both protected database dumps match their retained hashes. Code/test ZIP and exact Docker image archives were hashed, read back and Docker-loaded locally. Archive receipts are versioned; the historical central receipt was restored to its exact prior hash after a helper reused its path. User database content was untouched by that receipt correction. Local retention is not off-host disaster recovery.

## Rollback constraints

The prior schema37 API correctly refuses a schema38 namespace. Prefer a forward repair preserving the policy, schema and all subsequent writes. Do not remove the privacy guard, drop the migration, or rewind a database to discard later writes. The pre-upgrade clone restoration check demonstrates recovery of that clone; it is not approval for production data rewind. Live containers and live database were not replaced or migrated.

Private individual HTTP content admission remains503. Eleven placeholder routes, broader workflow and authority promotion, semantic integrations, full-duplex voice, external provider qualification, held-out quality, capacity, rights/package review, managed security scanning and independent acceptance remain unfinished. No cash spending or external activation was authorized or performed.

Changed source paths: `database/migrations/0038_governed_audit_parent_visibility.sql`, `database/access-contract.json`, `tests/test_governed_audit_parent_database.py`. Exact hashes and before/after bindings are in [the increment evidence](../../evidence/noetaris-integration/historical-audit-stage/current-evidence.json).
