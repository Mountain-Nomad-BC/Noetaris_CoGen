# D: Private PDF workspace, OCR and formulas

Status: planning artifacts only. No card is accepted by this document.

## NSAI-050 — Add server-validated document/revision/page questions

**P2 · PLANNED · REQUIRED**

Finding: REF-02. Dependencies: NSAI-049. Owner: Implementation engineer; independent verifier accepts.

Scope: API, retrieval, UI.

### Work

1. Reproduce or specify the current contract in API, retrieval, UI; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Add server-validated document/revision/page questions. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Selected source/revision/page is the retrieval universe.
- cross-document comparison explicit.
- wrong/stale/unauthorized scopes rejected.
- completeness shown with answers.

### Evidence

Store private receipts in `evidence/implementation/NSAI-050/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-051 — Build a private PDF workspace and exact citation navigation

**P2 · PLANNED · REQUIRED**

Finding: REF-03. Dependencies: NSAI-050, NSAI-043, NSAI-031. Owner: Implementation engineer; independent verifier accepts.

Scope: assets, authenticated original endpoints.

### Work

1. Reproduce or specify the current contract in assets, authenticated original endpoints; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Build a private PDF workspace and exact citation navigation. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Pinned locally bundled renderer/worker.
- navigation/zoom/text pane opens exact revision/page.
- no PDF JavaScript/actions/forms/attachments/external fetch.
- CSP preserved.
- auth on HEAD/range/cache/thumb/error paths.
- logout clears buffers.

### Evidence

Store private receipts in `evidence/implementation/NSAI-051/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-052 — Build bounded owned OCR jobs and leases

**P2 · PLANNED · REQUIRED**

Finding: REF-04. Dependencies: NSAI-051, NSAI-029, NSAI-023. Owner: Implementation engineer; independent verifier accepts.

Scope: isolated worker, API job contract, deploy.

### Work

1. Reproduce or specify the current contract in isolated worker, API job contract, deploy; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Build bounded owned OCR jobs and leases. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Bounded queue/lease/expiry/cancel/restart/idempotency.
- no DB/model secrets or external network.
- CPU/RAM/time/pixel limits before allocation.
- cancellation and child crash leave worker reusable.

### Evidence

Store private receipts in `evidence/implementation/NSAI-052/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-053 — Choose native extraction or OCR for each page

**P2 · PLANNED · REQUIRED**

Finding: REF-05. Dependencies: NSAI-052, NSAI-014. Owner: Implementation engineer; independent verifier accepts.

Scope: ingestion, OCR worker.

### Work

1. Reproduce or specify the current contract in ingestion, OCR worker; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Choose native extraction or OCR for each page. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Native/blank/scanned/mixed classification per page.
- orientation/deskew actual transforms recorded.
- English printed baseline explicit.
- unsupported languages/handwriting flagged.
- OCR observations never approved automatically.

### Evidence

Store private receipts in `evidence/implementation/NSAI-053/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-054 — Preserve raw OCR, boxes and coordinate transforms

**P2 · PLANNED · REQUIRED**

Finding: REF-06. Dependencies: NSAI-053, NSAI-038. Owner: Implementation engineer; independent verifier accepts.

Scope: OCR contracts, source map, viewer overlays.

### Work

1. Reproduce or specify the current contract in OCR contracts, source map, viewer overlays; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Preserve raw OCR, boxes and coordinate transforms. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- UserUnit/crop/rotation/deskew/DPI transforms and inverse all corners tested.
- raw/normalized text and engine score meaning retained.
- corrections append with lineage rather than rewriting originals.

### Evidence

Store private receipts in `evidence/implementation/NSAI-054/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-055 — Implement independently checked OCR metrics and holdouts

**P2 · PLANNED · REQUIRED**

Finding: REF-07. Dependencies: NSAI-054. Owner: Implementation engineer; independent verifier accepts.

Scope: quality harness, labeled original/authorized fixtures.

### Work

1. Reproduce or specify the current contract in quality harness, labeled original/authorized fixtures; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Implement independently checked OCR metrics and holdouts. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- CER/WER edit counts include insertions and may exceed 1.
- blank reference scored separately.
- critical digits/signs/units/negation/exponents and layout/table metrics reported.
- source-family split prevents leakage.

### Evidence

Store private receipts in `evidence/implementation/NSAI-055/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-056 — Calibrate OCR admission and resource targets

**P2 · PLANNED · REQUIRED**

Finding: REF-08. Dependencies: NSAI-055, NSAI-052. Owner: Implementation engineer; independent verifier accepts.

Scope: benchmark profiles, OCR quality gates.

### Work

1. Reproduce or specify the current contract in benchmark profiles, OCR quality gates; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Calibrate OCR admission and resource targets. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Proposed 200 pages/50 documents, clean CER<=1% WER<=3%, degraded CER<=3% WER<=8%, critical exact>=99.5%, geometry roundtrip<=0.5pt/IoU median>=0.9/p95 boundary<=2pt are evaluated as uncalibrated targets.
- confidence not presumed probability.
- 10s/page at 300DPI/512MiB calibrated with total-job limits.

### Evidence

Store private receipts in `evidence/implementation/NSAI-056/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-057 — Represent recognized formula candidates safely

**P2 · PLANNED · REQUIRED**

Finding: REF-09. Dependencies: NSAI-054, NSAI-033. Owner: Implementation engineer; independent verifier accepts.

Scope: formula observation contracts, viewer.

### Work

1. Reproduce or specify the current contract in formula observation contracts, viewer; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Represent recognized formula candidates safely. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Verbatim symbols, normalized notation, variables/dimensions/assumptions/source boxes stored.
- superscripts/fractions/table links tested.
- ambiguous/unsupported formula recognition explicitly withheld.

### Evidence

Store private receipts in `evidence/implementation/NSAI-057/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-058 — Validate finite allowlisted calculations without execution

**P2 · PLANNED · REQUIRED**

Finding: REF-10. Dependencies: NSAI-057, NSAI-041. Owner: Implementation engineer; independent verifier accepts.

Scope: pure formula validator, answer support.

### Work

1. Reproduce or specify the current contract in pure formula validator, answer support; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Validate finite allowlisted calculations without execution. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Small grammar rejects Python/eval/functions outside allowlist.
- finite Decimal/dimensions/sign/rounding independently verified.
- formula/version/input spans recorded.
- 100% exact only for declared finite fixture set, no generic math recognition claim.

### Evidence

Store private receipts in `evidence/implementation/NSAI-058/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-059 — Qualify the complete PDF/OCR/formula workflow

**P2 · PLANNED · REQUIRED**

Finding: GAP-03. Dependencies: NSAI-051, NSAI-056, NSAI-058. Owner: Implementation engineer; independent verifier accepts.

Scope: PDF browser and containment suites.

### Work

1. Reproduce or specify the current contract in PDF browser and containment suites; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Qualify the complete PDF/OCR/formula workflow. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Native/scanned/mixed/rotated/multicolumn/table/formula/encrypted/malformed fixtures.
- source auth, private renderer, correction review, scoped QA and containment pass with per-subgroup failures and unsupported states visible.

### Evidence

Store private receipts in `evidence/implementation/NSAI-059/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.
