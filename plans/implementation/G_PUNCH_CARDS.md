# G: Independent qualification and controlled release

Status: planning artifacts only. No card is accepted by this document.

## NSAI-077 — Resolve dedicated security scan worker prerequisite

**P2 · EXTERNAL_PREREQUISITE · REQUIRED**

Finding: GAP-06. Dependencies: none. Owner: Implementation engineer; independent verifier accepts.

Scope: Codex Security environment configuration.

### Work

1. Reproduce or specify the current contract in Codex Security environment configuration; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Resolve dedicated security scan worker prerequisite. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Managed read-only filesystem permission profile available.
- actual tool error retained: Deep Scan cannot safely start a read-only worker: the parent must provide a managed filesystem permission profile.
- no global permission weakening or scan PASS invented.

### Evidence

Store private receipts in `evidence/implementation/NSAI-077/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-078 — Run independent security qualification and revalidate fixes

**P2 · PLANNED · REQUIRED**

Finding: GAP-07. Dependencies: NSAI-077, NSAI-068. Owner: Implementation engineer; independent verifier accepts.

Scope: dedicated Codex Security workflow.

### Work

1. Reproduce or specify the current contract in dedicated Codex Security workflow; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Run independent security qualification and revalidate fixes. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Actual successful multi-pass scan artifacts bound to final immutable source.
- findings independently validated, tracked in local backlog and addressed.
- required runtime adversarial tests separately linked.
- blocked/missing scan prohibits security-ready claim.

### Evidence

Store private receipts in `evidence/implementation/NSAI-078/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-079 — Close remaining adversarial, branch and load coverage gaps

**P2 · PLANNED · REQUIRED**

Finding: SUP-19. Dependencies: NSAI-032. Owner: Implementation engineer; independent verifier accepts.

Scope: test/eval/browser harnesses.

### Work

1. Reproduce or specify the current contract in test/eval/browser harnesses; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Close remaining adversarial, branch and load coverage gaps. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- All active functions/routes/actions have positive/negative contracts.
- property/fuzz parser/protocol/quantity tests, sustained load, full browser/a11y and growing corpus checked.
- disabled Evolus not invoked.
- coverage limitations retained.

### Evidence

Store private receipts in `evidence/implementation/NSAI-079/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-080 — Validate the actual submission archive

**P2 · PLANNED · REQUIRED**

Finding: SUP-20. Dependencies: NSAI-031, NSAI-030, NSAI-047. Owner: Implementation engineer; independent verifier accepts.

Scope: packaging scripts, artifact staging.

### Work

1. Reproduce or specify the current contract in packaging scripts, artifact staging; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Validate the actual submission archive. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Exact allowlisted members with digest manifest, secret/privacy/license scans and member review.
- excluded private corpus/backups/keys/models.
- claims match evidence.
- no automatic publication.

### Evidence

Store private receipts in `evidence/implementation/NSAI-080/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-081 — Reconcile guides and current capability statements

**P2 · PLANNED · REQUIRED**

Finding: SUP-21. Dependencies: NSAI-005, NSAI-047, NSAI-080. Owner: Implementation engineer; independent verifier accepts.

Scope: START_HERE, LOCAL guides, NOTICE, status ledger.

### Work

1. Reproduce or specify the current contract in START_HERE, LOCAL guides, NOTICE, status ledger; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Reconcile guides and current capability statements. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- One supported workflow.
- old baseline PASS distinguished from fresh qualification.
- clean-room/source-origin wording truthful.
- PDF/OCR/central/AMD capability states accurate.
- testing/evidence has its own section.

### Evidence

Store private receipts in `evidence/implementation/NSAI-081/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-082 — Rehearse controlled CPU deployment and submission readiness

**P2 · PLANNED · REQUIRED**

Finding: GAP-08. Dependencies: NSAI-078, NSAI-079, NSAI-080, NSAI-081, NSAI-025, NSAI-059, NSAI-068. Owner: Implementation engineer; independent verifier accepts.

Scope: release checklist, deployment receipts.

### Work

1. Reproduce or specify the current contract in release checklist, deployment receipts; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Rehearse controlled CPU deployment and submission readiness. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Tests/evidence reviewed separately.
- immutable image/config, backup, migration plan and rollback rehearsed.
- deploy only accepted CPU release.
- post-deploy source/image binding and smoke checks.
- unresolved required findings block release.

### Evidence

Store private receipts in `evidence/implementation/NSAI-082/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.
