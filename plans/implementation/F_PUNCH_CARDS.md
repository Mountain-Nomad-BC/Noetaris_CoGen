# F: Optional local transcript and business capabilities

Status: planning artifacts only. No card is accepted by this document.

## NSAI-069 — Build independent source-bound transcript observations

**P2 · PLANNED · OPTIONAL_AFTER_BASELINE**

Finding: REF-19. Dependencies: NSAI-068. Owner: Implementation engineer; independent verifier accepts.

Scope: optional transcript module.

### Work

1. Reproduce or specify the current contract in optional transcript module; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Build independent source-bound transcript observations. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Original synthetic turns with speaker/time/offset/session manifest.
- duplicate/reordered/unknown-speaker/spoof cases.
- reversible aliases are proposals.
- no upstream source, dictionary or corporate transcript copied.

### Evidence

Store private receipts in `evidence/implementation/NSAI-069/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-070 — Link questions, measurements, actions and outcomes conservatively

**P2 · PLANNED · OPTIONAL_AFTER_BASELINE**

Finding: REF-20. Dependencies: NSAI-069, NSAI-034. Owner: Implementation engineer; independent verifier accepts.

Scope: optional transcript assembly.

### Work

1. Reproduce or specify the current contract in optional transcript assembly; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Link questions, measurements, actions and outcomes conservatively. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Assertion/question/negated/historical/conditional/action/outcome states separated.
- quantities include instrument/location/conditions.
- request-answer links measured.
- manual specification not treated as observed measurement.

### Evidence

Store private receipts in `evidence/implementation/NSAI-070/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-071 — Qualify transcript replay and withheld reports

**P2 · PLANNED · OPTIONAL_AFTER_BASELINE**

Finding: REF-21. Dependencies: NSAI-070, NSAI-067. Owner: Implementation engineer; independent verifier accepts.

Scope: optional transcript evaluation/UI.

### Work

1. Reproduce or specify the current contract in optional transcript evaluation/UI; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Qualify transcript replay and withheld reports. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Source-family/revision/session split, deterministic semantic corpus signatures, accepted/withheld/unsupported ledger, corrected-turn replay and uncertainty metrics.
- report existence alone fails certification.

### Evidence

Store private receipts in `evidence/implementation/NSAI-071/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-072 — Define operational metrics before business conclusions

**P2 · PLANNED · OPTIONAL_AFTER_BASELINE**

Finding: REF-22. Dependencies: NSAI-068, NSAI-046. Owner: Implementation engineer; independent verifier accepts.

Scope: optional reporting, metric registry.

### Work

1. Reproduce or specify the current contract in optional reporting, metric registry; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Define operational metrics before business conclusions. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Metric owner/version/grain/numerator/denominator/window/freshness/exclusions explicit.
- duplicates/missing/stale/zero denominator produce unknown or failure.
- utilization and throughput use actual task cohorts.

### Evidence

Store private receipts in `evidence/implementation/NSAI-072/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-073 — Distinguish continuation, recurrence and new tasks

**P2 · PLANNED · OPTIONAL_AFTER_BASELINE**

Finding: REF-23. Dependencies: NSAI-069, NSAI-044. Owner: Implementation engineer; independent verifier accepts.

Scope: optional session/task linkage.

### Work

1. Reproduce or specify the current contract in optional session/task linkage; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Distinguish continuation, recurrence and new tasks. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Actor-owned source-bound linkage with ambiguity/unknown states and explicit confirmation.
- false-association precision/recall measured.
- no inferred corporate/customer identity.

### Evidence

Store private receipts in `evidence/implementation/NSAI-073/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-074 — Account for local resource budgets and usage

**P2 · PLANNED · OPTIONAL_AFTER_BASELINE**

Finding: REF-24. Dependencies: NSAI-015, NSAI-072. Owner: Implementation engineer; independent verifier accepts.

Scope: inference/task ledger, optional reporting.

### Work

1. Reproduce or specify the current contract in inference/task ledger, optional reporting; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Account for local resource budgets and usage. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Durable UTC reservation/settlement/expiry, retries/day rollover/crash reconciled.
- actual attempts/tokens/time recorded.
- no guessed currency cost.
- pricing contract finite Decimal/version/currency staged.

### Evidence

Store private receipts in `evidence/implementation/NSAI-074/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-075 — Report reviewed outcomes and hypothetical scenarios honestly

**P2 · PLANNED · OPTIONAL_AFTER_BASELINE**

Finding: REF-25. Dependencies: NSAI-074, NSAI-072, NSAI-063. Owner: Implementation engineer; independent verifier accepts.

Scope: optional business projection.

### Work

1. Reproduce or specify the current contract in optional business projection; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Report reviewed outcomes and hypothetical scenarios honestly. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Real eligible outcome denominator and attribution needed.
- unknown/zero denominator never manufactured as zero.
- no model success equated to verified resolution/ROI/causality.
- fixed-variable scenarios labeled assumptions.

### Evidence

Store private receipts in `evidence/implementation/NSAI-075/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-076 — Qualify optional transcript and operational reporting

**P2 · PLANNED · OPTIONAL_AFTER_BASELINE**

Finding: GAP-05. Dependencies: NSAI-071, NSAI-073, NSAI-075. Owner: Implementation engineer; independent verifier accepts.

Scope: optional acceptance suites.

### Work

1. Reproduce or specify the current contract in optional acceptance suites; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Qualify optional transcript and operational reporting. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Optional modules off until a selected workflow.
- independently written fixtures and measured lineage.
- useful original local capabilities accepted without adopting corporate terminology or full enterprise integrations.

### Evidence

Store private receipts in `evidence/implementation/NSAI-076/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-087 — Qualify optional local semantic retrieval generations

**P2 · PLANNED · OPTIONAL_AFTER_BASELINE**

Finding: REF-29. Dependencies: NSAI-049, NSAI-039, NSAI-061. Owner: Implementation engineer; independent verifier accepts.

Scope: local embedding adapter, candidate index lifecycle.

### Work

1. Reproduce or specify the current contract in local embedding adapter, candidate index lifecycle; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Qualify optional local semantic retrieval generations. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Model/tokenizer/license/hash identity bound to index.
- scoped source-family holdout compares lexical versus hybrid Recall@k/MRR/support/refusal and resource cost.
- shadow validation before explicit activation.
- rollback to lexical verified.
- no unapproved download or provider fallback.

### Evidence

Store private receipts in `evidence/implementation/NSAI-087/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-088 — Specify valid-time and observation-time memory queries

**P2 · PLANNED · OPTIONAL_AFTER_BASELINE**

Finding: REF-30. Dependencies: NSAI-036, NSAI-039, NSAI-034. Owner: Implementation engineer; independent verifier accepts.

Scope: optional temporal projection contracts.

### Work

1. Reproduce or specify the current contract in optional temporal projection contracts; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Specify valid-time and observation-time memory queries. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Historical validity and observation time separated.
- revisions/conditions and stale records tested.
- optional bitemporal projection uses current immutable events rather than parallel authority.
- unsupported historical query abstains.

### Evidence

Store private receipts in `evidence/implementation/NSAI-088/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.
