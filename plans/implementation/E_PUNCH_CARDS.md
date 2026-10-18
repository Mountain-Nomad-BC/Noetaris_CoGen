# E: Governed assembly and inactive central integration

Status: planning artifacts only. No card is accepted by this document.

## NSAI-060 — Assemble a small deterministic evidence stage graph

**P2 · PLANNED · REQUIRED**

Finding: REF-11. Dependencies: NSAI-059, NSAI-039. Owner: Implementation engineer; independent verifier accepts.

Scope: local assembly modules, stage receipts.

### Work

1. Reproduce or specify the current contract in local assembly modules, stage receipts; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Assemble a small deterministic evidence stage graph. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Owned bounded DAG rejects cycles/unknown dependencies.
- semantic fingerprints distinct from paths/timestamps.
- replay invalidation binds source/parser/rules/model generations.
- no full PX runtime transplant.

### Evidence

Store private receipts in `evidence/implementation/NSAI-060/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-061 — Govern proposals through holdout, review and rollback

**P2 · PLANNED · REQUIRED**

Finding: REF-12. Dependencies: NSAI-060, NSAI-047. Owner: Implementation engineer; independent verifier accepts.

Scope: learning store, evaluation registry.

### Work

1. Reproduce or specify the current contract in learning store, evaluation registry; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Govern proposals through holdout, review and rollback. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Observation/candidate/shadow-evaluation/independent-review/revision transitions explicit.
- paired frozen baseline/challenger and holdout isolation.
- stale evidence denied.
- promotion reversible.
- no training or generated execution enabled.

### Evidence

Store private receipts in `evidence/implementation/NSAI-061/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-062 — Use strict data-only manifests and procedure proposals

**P2 · PLANNED · REQUIRED**

Finding: REF-13. Dependencies: NSAI-061, NSAI-031. Owner: Implementation engineer; independent verifier accepts.

Scope: knowledge/formula/skill contracts, local registry.

### Work

1. Reproduce or specify the current contract in knowledge/formula/skill contracts, local registry; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Use strict data-only manifests and procedure proposals. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Unknown fields, duplicate JSON keys, depth/size excess, nonfinite values, missing hashes and forged authority denied.
- no pickle/untrusted code.
- procedures declare I/O/effects/tests but remain nonexecutable.

### Evidence

Store private receipts in `evidence/implementation/NSAI-062/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-063 — Track scoped correction and outcome uncertainty

**P2 · PLANNED · REQUIRED**

Finding: REF-14. Dependencies: NSAI-061, NSAI-044. Owner: Implementation engineer; independent verifier accepts.

Scope: feedback API, review UI.

### Work

1. Reproduce or specify the current contract in feedback API, review UI; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Track scoped correction and outcome uncertainty. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Response/source/claim IDs and bounded reason taxonomy.
- dedupe and before/after lineage.
- reviewer outcomes do not imply verified causal resolution.
- unknown causes remain unknown.

### Evidence

Store private receipts in `evidence/implementation/NSAI-063/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-064 — Complete local governance management controls

**P2 · PLANNED · REQUIRED**

Finding: REF-15. Dependencies: NSAI-061, NSAI-046, NSAI-010. Owner: Implementation engineer; independent verifier accepts.

Scope: policy/review/limits/capability UI, API.

### Work

1. Reproduce or specify the current contract in policy/review/limits/capability UI, API; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Complete local governance management controls. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Risk-tiered local role/action matrix.
- actual actor/old-new policy revision/expiry/idempotency and independent approval for sensitive changes.
- stale/forged/self approval rejected.
- natural language grants no authority.
- central remains disabled.

### Evidence

Store private receipts in `evidence/implementation/NSAI-064/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-065 — Stage central authorization interfaces without activation

**P2 · PLANNED · REQUIRED**

Finding: REF-16. Dependencies: NSAI-064. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/security.py, integration contract tests.

### Work

1. Reproduce or specify the current contract in src/nsai/security.py, integration contract tests; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Stage central authorization interfaces without activation. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Validated actor/resource/policy/reason/expiry/revocation contracts.
- malformed/unavailable/stale provider fails closed in isolated tests.
- configuration imports data only.
- all live central enable attempts denied.

### Evidence

Store private receipts in `evidence/implementation/NSAI-065/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-066 — Specify scoped integration secret lifecycle

**P2 · PLANNED · REQUIRED**

Finding: REF-17. Dependencies: NSAI-065, NSAI-008. Owner: Implementation engineer; independent verifier accepts.

Scope: disabled adapter contracts, local secret management.

### Work

1. Reproduce or specify the current contract in disabled adapter contracts, local secret management; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Specify scoped integration secret lifecycle. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Dedicated scoped credentials, expiry/revocation/rotation receipt.
- no global key or plaintext fallback.
- no new external connector activated.

### Evidence

Store private receipts in `evidence/implementation/NSAI-066/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-067 — Render bounded accepted and withheld evidence traces

**P2 · PLANNED · REQUIRED**

Finding: REF-18. Dependencies: NSAI-060, NSAI-030, NSAI-063. Owner: Implementation engineer; independent verifier accepts.

Scope: UI trace projection, export contract.

### Work

1. Reproduce or specify the current contract in UI trace projection, export contract; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Render bounded accepted and withheld evidence traces. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Stable run/version/source/claim identity.
- mismatched receipts never merged.
- approved/disputed/withheld/unsupported shown.
- optional CSV export formula-injection neutralized and redacted.
- renderer cannot grant truth/authority.

### Evidence

Store private receipts in `evidence/implementation/NSAI-067/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-068 — Accept governed assembly and disabled central contracts

**P2 · PLANNED · REQUIRED**

Finding: GAP-04. Dependencies: NSAI-062, NSAI-063, NSAI-064, NSAI-065, NSAI-066, NSAI-067. Owner: Implementation engineer; independent verifier accepts.

Scope: learning/admin end-to-end suites.

### Work

1. Reproduce or specify the current contract in learning/admin end-to-end suites; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Accept governed assembly and disabled central contracts. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Replay, promotion denial, rollback, action ownership, scoped key contracts and forbidden activation verified.
- registry/graph/proposal existence never implies execution permission.

### Evidence

Store private receipts in `evidence/implementation/NSAI-068/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.
