# B: Required CPU foundation repairs

Status: planning artifacts only. No card is accepted by this document.

## NSAI-004 — Make startup and readiness observational

**P1 · PLANNED · REQUIRED**

Finding: OPS-04. Dependencies: NSAI-003, NSAI-002. Owner: Implementation engineer; independent verifier accepts.

Scope: scripts/start-cpu.ps1.

### Work

1. Reproduce or specify the current contract in scripts/start-cpu.ps1; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Make startup and readiness observational. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- 100 repeated starts/readiness checks add no documents, claims, sessions or policy changes.
- acceptance data uses a disposable database.

### Evidence

Store private receipts in `evidence/implementation/NSAI-004/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-005 — Consolidate supported local entrypoints

**P1 · PLANNED · REQUIRED**

Finding: OPS-05. Dependencies: NSAI-004. Owner: Implementation engineer; independent verifier accepts.

Scope: scripts, root startup documents.

### Work

1. Reproduce or specify the current contract in scripts, root startup documents; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Consolidate supported local entrypoints. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Every retained Windows/shell launcher performs parser, roles, migration and CPU readiness on clean volumes.
- obsolete paths redirect or reject clearly.

### Evidence

Store private receipts in `evidence/implementation/NSAI-005/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-006 — Stage checks before journaled compatible migrations

**P1 · PLANNED · REQUIRED**

Finding: OPS-08. Dependencies: NSAI-003. Owner: Implementation engineer; independent verifier accepts.

Scope: scripts/migrate.py, database migrations.

### Work

1. Reproduce or specify the current contract in scripts/migrate.py, database migrations; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Stage checks before journaled compatible migrations. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Build/check failure performs no schema mutation.
- upgrade and compatible prior-image recovery pass on cloned data.
- incompatible downgrade is denied with restore instructions.

### Evidence

Store private receipts in `evidence/implementation/NSAI-006/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-007 — Converge database privileges and rotate credentials

**P1 · PLANNED · REQUIRED**

Finding: OPS-09. Dependencies: NSAI-006. Owner: Implementation engineer; independent verifier accepts.

Scope: scripts/migrate.py, database role provisioning.

### Work

1. Reproduce or specify the current contract in scripts/migrate.py, database role provisioning; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Converge database privileges and rotate credentials. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Seed excess grants/memberships/attributes and prove removal.
- immutable tables cannot be updated/deleted.
- explicit rotation preserves availability without logging secrets.

### Evidence

Store private receipts in `evidence/implementation/NSAI-007/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-008 — Protect private state with Windows ACLs

**P1 · PLANNED · REQUIRED**

Finding: OPS-10. Dependencies: NSAI-005. Owner: Implementation engineer; independent verifier accepts.

Scope: scripts/protect-secrets.ps1, startup, backup directories.

### Work

1. Reproduce or specify the current contract in scripts/protect-secrets.ps1, startup, backup directories; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Protect private state with Windows ACLs. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Intended account and SYSTEM access only.
- existing/inherited grants and children checked.
- hostile account read fails.
- startup checks actual DACL rather than chmod.

### Evidence

Store private receipts in `evidence/implementation/NSAI-008/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-009 — Write bounded exclusive recoverable backups

**P1 · PLANNED · REQUIRED**

Finding: OPS-07. Dependencies: NSAI-008, NSAI-006. Owner: Implementation engineer; independent verifier accepts.

Scope: scripts/verify_recovery.py, backup tooling.

### Work

1. Reproduce or specify the current contract in scripts/verify_recovery.py, backup tooling; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Write bounded exclusive recoverable backups. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Same-second/concurrent dumps never overwrite.
- streaming size/time/disk bounds enforced.
- protected temporary output atomically finalized with SHA256 manifest.
- failed dumps never marked successful.

### Evidence

Store private receipts in `evidence/implementation/NSAI-009/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-010 — Validate credentials and secure every error response

**P0 · PLANNED · REQUIRED**

Finding: CORE-03. Dependencies: NSAI-003. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/security.py, src/nsai/api.py.

### Work

1. Reproduce or specify the current contract in src/nsai/security.py, src/nsai/api.py; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Validate credentials and secure every error response. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Non-ASCII, oversized, malformed and absent bearer credentials return controlled 401/403 with required security headers.
- constant-time comparison retained.

### Evidence

Store private receipts in `evidence/implementation/NSAI-010/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-011 — Clear all private browser state on identity changes

**P1 · PLANNED · REQUIRED**

Finding: OPS-06. Dependencies: NSAI-010. Owner: Implementation engineer; independent verifier accepts.

Scope: assets/app.js.

### Work

1. Reproduce or specify the current contract in assets/app.js; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Clear all private browser state on identity changes. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- All six observed draft fields, file selections, rendered private content and object URLs clear.
- pending old-epoch responses cannot repopulate state.

### Evidence

Store private receipts in `evidence/implementation/NSAI-011/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-012 — Handle malformed provider and secret failures

**P0 · PLANNED · REQUIRED**

Finding: CORE-11. Dependencies: NSAI-010. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/inference.py, model inventory endpoints.

### Work

1. Reproduce or specify the current contract in src/nsai/inference.py, model inventory endpoints; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Handle malformed provider and secret failures. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- JSON list/null/invalid envelopes, missing secret, I/O error, timeout and cancellation return bounded typed failures without accidental 500 or secret disclosure.

### Evidence

Store private receipts in `evidence/implementation/NSAI-012/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-013 — Bound PDF decoding before allocation

**P0 · PLANNED · REQUIRED**

Finding: CORE-01. Dependencies: NSAI-003. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/ingestion.py, src/nsai/parser_child.py.

### Work

1. Reproduce or specify the current contract in src/nsai/ingestion.py, src/nsai/parser_child.py; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Bound PDF decoding before allocation. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- False-valued ContentStream, compressed arrays/object streams, huge expansion and malformed objects reject before excessive allocation.
- parser recovers for next valid job.

### Evidence

Store private receipts in `evidence/implementation/NSAI-013/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-014 — Record every PDF page and its completeness

**P0 · PLANNED · REQUIRED**

Finding: CORE-13. Dependencies: NSAI-013, NSAI-006. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/ingestion.py, source schema, assets/app.js.

### Work

1. Reproduce or specify the current contract in src/nsai/ingestion.py, source schema, assets/app.js; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Record every PDF page and its completeness. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Mixed native/raster fixture accounts for all pages as native/blank/OCR-required/failed/unsupported.
- omitted pages never imply complete evidence.

### Evidence

Store private receipts in `evidence/implementation/NSAI-014/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-015 — Make inference terminal transitions idempotent

**P0 · PLANNED · REQUIRED**

Finding: CORE-04. Dependencies: NSAI-006, NSAI-003. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/workflow_store.py, src/nsai/inference.py.

### Work

1. Reproduce or specify the current contract in src/nsai/workflow_store.py, src/nsai/inference.py; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Make inference terminal transitions idempotent. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Concurrent finish/retry yields one terminal transition and one settlement event.
- stale actors denied.
- failed attempts charged.
- abandoned reservations reconciled durably.

### Evidence

Store private receipts in `evidence/implementation/NSAI-015/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-016 — Admit the complete prompt using the actual tokenizer

**P0 · PLANNED · REQUIRED**

Finding: CORE-16. Dependencies: NSAI-012, NSAI-015. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/inference.py, model configuration.

### Work

1. Reproduce or specify the current contract in src/nsai/inference.py, model configuration; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Admit the complete prompt using the actual tokenizer. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- System/schema/question/history/evidence plus reserved output fit model context.
- 4,632-token adversarial fixture is refused or explicitly reduced before reservation.
- omissions observable.

### Evidence

Store private receipts in `evidence/implementation/NSAI-016/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-017 — Discover conflicts beyond retrieved top-k

**P0 · PLANNED · REQUIRED**

Finding: CORE-02. Dependencies: NSAI-006. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/workflow_store.py, src/nsai/api.py.

### Work

1. Reproduce or specify the current contract in src/nsai/workflow_store.py, src/nsai/api.py; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Discover conflicts beyond retrieved top-k. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Authorized active alternatives outside rank limits still conflict.
- quarantined/disputed values cannot become answer facts.
- revision/history retained.

### Evidence

Store private receipts in `evidence/implementation/NSAI-017/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-018 — Align Unicode and serialized transport budgets

**P1 · PLANNED · REQUIRED**

Finding: CORE-14. Dependencies: NSAI-013. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/parser.py, parser response contract.

### Work

1. Reproduce or specify the current contract in src/nsai/parser.py, parser response contract; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Align Unicode and serialized transport budgets. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- 150,000 supplementary-codepoint fixture has a deliberate supported/rejected result consistent with UTF-8 transport and child/API limits.
- no oversized buffered response.

### Evidence

Store private receipts in `evidence/implementation/NSAI-018/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-019 — Replace UI presence checks with observed outcomes

**P1 · PLANNED · REQUIRED**

Finding: OPS-11. Dependencies: NSAI-011, NSAI-001. Owner: Implementation engineer; independent verifier accepts.

Scope: browser acceptance scripts, verification receipts.

### Work

1. Reproduce or specify the current contract in browser acceptance scripts, verification receipts; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Replace UI presence checks with observed outcomes. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Wait on state/results rather than fixed sleeps.
- role ingestion/review/answer/logout flows prove source binding and completed actions.
- receipts include run/time/source/image identities.

### Evidence

Store private receipts in `evidence/implementation/NSAI-019/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-020 — Verify model identity, licensing and endpoint configuration

**P1 · PLANNED · REQUIRED**

Finding: OPS-12. Dependencies: NSAI-012. Owner: Implementation engineer; independent verifier accepts.

Scope: scripts/prepare_cpu_model.py, model helpers.

### Work

1. Reproduce or specify the current contract in scripts/prepare_cpu_model.py, model helpers; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Verify model identity, licensing and endpoint configuration. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Mandatory digest and explicit metadata/license match actual GGUF.
- symlink policy checked before resolve.
- alternate configured port works throughout.
- arbitrary GGUF not mislabeled Qwen.

### Evidence

Store private receipts in `evidence/implementation/NSAI-020/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-021 — Make container package resolution reproducible

**P1 · PLANNED · REQUIRED**

Finding: SUP-01. Dependencies: NSAI-002. Owner: Implementation engineer; independent verifier accepts.

Scope: Dockerfiles, deploy.

### Work

1. Reproduce or specify the current contract in Dockerfiles, deploy; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Make container package resolution reproducible. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Base digest and installed OS package closure recorded/pinned or snapshot-controlled.
- two matched builds explain any drift.
- SBOM and current CVE dispositions retained.

### Evidence

Store private receipts in `evidence/implementation/NSAI-021/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-022 — Lock runtime, build, test and CI dependencies

**P1 · PLANNED · REQUIRED**

Finding: SUP-02. Dependencies: NSAI-021. Owner: Implementation engineer; independent verifier accepts.

Scope: pyproject, lock files, CI configuration.

### Work

1. Reproduce or specify the current contract in pyproject, lock files, CI configuration; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Lock runtime, build, test and CI dependencies. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Runtime Python 3.12 checks plus declared host compatibility pass.
- build/test hashes locked.
- commissioned CI uses lock and pinned action SHAs.
- deprecations have explicit disposition.

### Evidence

Store private receipts in `evidence/implementation/NSAI-022/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-023 — Validate Docker's effective profile-aware configuration

**P1 · PLANNED · REQUIRED**

Finding: SUP-03. Dependencies: NSAI-002. Owner: Implementation engineer; independent verifier accepts.

Scope: scripts/check_compose.py, deploy.

### Work

1. Reproduce or specify the current contract in scripts/check_compose.py, deploy; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Validate Docker's effective profile-aware configuration. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Effective CPU JSON rejects unknown services, added mounts/ports/egress or missing limits.
- deferred profiles not mistaken for commissioned CPU services.

### Evidence

Store private receipts in `evidence/implementation/NSAI-023/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-024 — Remove import-time script mutations and bound subprocesses

**P1 · PLANNED · REQUIRED**

Finding: SUP-04. Dependencies: NSAI-005. Owner: Implementation engineer; independent verifier accepts.

Scope: scripts.

### Work

1. Reproduce or specify the current contract in scripts; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Remove import-time script mutations and bound subprocesses. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Importing helpers has no host/service mutation.
- explicit main entrypoints.
- deadlines/cancellation/cleanup and typed receipts for every subprocess.

### Evidence

Store private receipts in `evidence/implementation/NSAI-024/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-025 — Qualify recovery from independently verified backups

**P1 · PLANNED · REQUIRED**

Finding: SUP-05. Dependencies: NSAI-009, NSAI-007, NSAI-024. Owner: Implementation engineer; independent verifier accepts.

Scope: scripts/verify_recovery.py, restore harness.

### Work

1. Reproduce or specify the current contract in scripts/verify_recovery.py, restore harness; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Qualify recovery from independently verified backups. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Restore schema, roles, grants, indexes, triggers and data with bounded SHA256 verification.
- concurrent-write snapshot semantics documented.
- interrupted restore recovers.
- PITR remains explicitly unqualified unless separately implemented.

### Evidence

Store private receipts in `evidence/implementation/NSAI-025/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-026 — Enforce database structural invariants

**P1 · PLANNED · REQUIRED**

Finding: SUP-06. Dependencies: NSAI-006, NSAI-007. Owner: Implementation engineer; independent verifier accepts.

Scope: migrations, src/nsai/workflow_store.py.

### Work

1. Reproduce or specify the current contract in migrations, src/nsai/workflow_store.py; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Enforce database structural invariants. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Central-disabled invariant, hash lengths/uniqueness, span-chunk relationships and nonempty reviewer constrained.
- seeded bad rows fail.
- trusted application semantic-forgery boundary documented.

### Evidence

Store private receipts in `evidence/implementation/NSAI-026/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-027 — Bound pre-auth traffic and enforce fair admission

**P1 · PLANNED · REQUIRED**

Finding: SUP-07. Dependencies: NSAI-010, NSAI-015. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/api.py, security policy.

### Work

1. Reproduce or specify the current contract in src/nsai/api.py, security policy; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Bound pre-auth traffic and enforce fair admission. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Unauthenticated streaming body bounded before buffering.
- total deadline and principal fairness tested.
- one-process scope honest.
- no unauthenticated request exhausts all authenticated capacity.

### Evidence

Store private receipts in `evidence/implementation/NSAI-027/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-028 — Unify approved model/parser HTTP transport

**P1 · PLANNED · REQUIRED**

Finding: SUP-08. Dependencies: NSAI-012, NSAI-018. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/inference.py, runtime checks, parser client.

### Work

1. Reproduce or specify the current contract in src/nsai/inference.py, runtime checks, parser client; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Unify approved model/parser HTTP transport. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Approved hosts, TLS policy, no redirects, explicit proxy policy, bounded response and deadlines enforced consistently.
- environment proxy cannot reroute private traffic.

### Evidence

Store private receipts in `evidence/implementation/NSAI-028/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-029 — Verify parser output independently

**P1 · PLANNED · REQUIRED**

Finding: SUP-09. Dependencies: NSAI-014, NSAI-018. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/parser.py, source contracts.

### Work

1. Reproduce or specify the current contract in src/nsai/parser.py, source contracts; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Verify parser output independently. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- API checks original digest, response schema, finite bounds and stage receipt before acceptance.
- forged worker metadata and inconsistent spans rejected.

### Evidence

Store private receipts in `evidence/implementation/NSAI-029/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-030 — Redact logs and verification metadata

**P1 · PLANNED · REQUIRED**

Finding: SUP-10. Dependencies: NSAI-010, NSAI-001. Owner: Implementation engineer; independent verifier accepts.

Scope: API logging, evidence/public projection.

### Work

1. Reproduce or specify the current contract in API logging, evidence/public projection; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Redact logs and verification metadata. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Synthetic secret/source/query payloads absent from normal access/error logs and public verification.
- allowlisted metadata only.
- private diagnostic export explicitly distinguished.

### Evidence

Store private receipts in `evidence/implementation/NSAI-030/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-031 — Resolve existing imported source and compatibility

**P1 · PLANNED · REQUIRED**

Finding: SUP-11. Dependencies: NSAI-029. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/vendor, import scripts, NOTICE, docs.

### Work

1. Reproduce or specify the current contract in src/nsai/vendor, import scripts, NOTICE, docs; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Resolve existing imported source and compatibility. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Independent replacement specification and implementation.
- old hash/span records remain readable.
- unused filesystem loaders and brittle replacement imports retired.
- licensing/provenance accurate.
- no public release implied.

### Evidence

Store private receipts in `evidence/implementation/NSAI-031/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-032 — Commission the repaired CPU foundation

**P1 · PLANNED · REQUIRED**

Finding: GAP-01. Dependencies: NSAI-004, NSAI-005, NSAI-006, NSAI-007, NSAI-008, NSAI-009, NSAI-010, NSAI-011, NSAI-012, NSAI-013, NSAI-014, NSAI-015, NSAI-016, NSAI-017, NSAI-018, NSAI-019, NSAI-020, NSAI-021, NSAI-022, NSAI-023, NSAI-024, NSAI-025, NSAI-026, NSAI-027, NSAI-028, NSAI-029, NSAI-030, NSAI-031. Owner: Implementation engineer; independent verifier accepts.

Scope: deploy, isolated qualification suite.

### Work

1. Reproduce or specify the current contract in deploy, isolated qualification suite; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Commission the repaired CPU foundation. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- All stage-1 repair cards accepted with fresh receipts.
- clean boot, upgrade, restart, restore, negative RBAC and real CPU model work pass.
- original user volumes preserved.
- security qualification shown separately.

### Evidence

Store private receipts in `evidence/implementation/NSAI-032/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.
