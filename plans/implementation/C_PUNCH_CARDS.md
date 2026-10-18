# C: Evidence, retrieval and performance refinement

Status: planning artifacts only. No card is accepted by this document.

## NSAI-033 — Compare finite quantities with dimensions and intervals

**P1 · PLANNED · REQUIRED**

Finding: CORE-05. Dependencies: NSAI-032. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/models.py, claim contracts.

### Work

1. Reproduce or specify the current contract in src/nsai/models.py, claim contracts; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Compare finite quantities with dimensions and intervals. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- 85 C and 185 F, 85 C and 85.0 C are equivalent.
- incompatible dimensions/conditions do not falsely compare.
- signs, intervals and rounding have independent oracle tests.
- raw spans retained.

### Evidence

Store private receipts in `evidence/implementation/NSAI-033/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-034 — Represent negation, conditions, time and uncertainty

**P1 · PLANNED · REQUIRED**

Finding: CORE-06. Dependencies: NSAI-033. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/models.py, source claims.

### Work

1. Reproduce or specify the current contract in src/nsai/models.py, source claims; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Represent negation, conditions, time and uncertainty. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Negative/historical/conditional/question/table observations remain typed.
- unsupported forms abstain.
- generic entity handling uses original fixtures without corporate dictionaries.

### Evidence

Store private receipts in `evidence/implementation/NSAI-034/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-035 — Apply one conflict policy to reflection and learning

**P1 · PLANNED · REQUIRED**

Finding: CORE-07. Dependencies: NSAI-034, NSAI-017. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/workflow_store.py, src/nsai/memory.py.

### Work

1. Reproduce or specify the current contract in src/nsai/workflow_store.py, src/nsai/memory.py; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Apply one conflict policy to reflection and learning. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Verified 85 plus new 75 generates bounded deduplicated conflict proposal.
- same active conflict rule applies across retrieval/memory/reflection.

### Evidence

Store private receipts in `evidence/implementation/NSAI-035/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-036 — Rank eligible memory and invalidate stale dependencies

**P1 · PLANNED · REQUIRED**

Finding: CORE-08. Dependencies: NSAI-035. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/memory.py, src/nsai/workflow_store.py.

### Work

1. Reproduce or specify the current contract in src/nsai/memory.py, src/nsai/workflow_store.py; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Rank eligible memory and invalidate stale dependencies. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- 13+ approved facts select by query relevance rather than hash ordering.
- eligible canon/hypothesis/reflection included deliberately.
- changed review/source/rules invalidate projection.

### Evidence

Store private receipts in `evidence/implementation/NSAI-036/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-037 — Measure complete memory envelopes and omissions

**P1 · PLANNED · REQUIRED**

Finding: CORE-10. Dependencies: NSAI-036, NSAI-016. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/memory.py, serialization.

### Work

1. Reproduce or specify the current contract in src/nsai/memory.py, serialization; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Measure complete memory envelopes and omissions. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Full JSON/envelope and tokenizer budgets include IDs/status/schema overhead.
- 1,300-byte envelope cannot claim compliance with 1,024-byte budget.
- every omitted initial slice listed.

### Evidence

Store private receipts in `evidence/implementation/NSAI-037/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-038 — Persist reversible normalization and chunk geometry

**P1 · PLANNED · REQUIRED**

Finding: SUP-12. Dependencies: NSAI-032. Owner: Implementation engineer; independent verifier accepts.

Scope: ingestion, migrations, source/chunk models.

### Work

1. Reproduce or specify the current contract in ingestion, migrations, source/chunk models; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Persist reversible normalization and chunk geometry. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- NFC, whitespace, aliases and chunk offsets round-trip to immutable raw spans.
- overlap remains word-safe.
- page geometry never inferred from line numbers.

### Evidence

Store private receipts in `evidence/implementation/NSAI-038/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-039 — Version extraction, indexes and projections independently

**P1 · PLANNED · REQUIRED**

Finding: SUP-13. Dependencies: NSAI-038. Owner: Implementation engineer; independent verifier accepts.

Scope: source schema, workflow store.

### Work

1. Reproduce or specify the current contract in source schema, workflow store; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Version extraction, indexes and projections independently. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Same original bytes can be reparsed without replacing originals.
- generation IDs bind parser/rules/source.
- stale index/projection excluded.
- replay and rollback verified.

### Evidence

Store private receipts in `evidence/implementation/NSAI-039/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-040 — Improve measured scoped lexical recall

**P1 · PLANNED · REQUIRED**

Finding: CORE-12. Dependencies: NSAI-038, NSAI-039, NSAI-034. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/workflow_store.py, retrieval/fusion.py.

### Work

1. Reproduce or specify the current contract in src/nsai/workflow_store.py, retrieval/fusion.py; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Improve measured scoped lexical recall. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Paraphrase/revision-qualified held-out queries measured with Recall@k/MRR/citation precision.
- scope filtered before ranking.
- lexical alternates/overlap and optional RRF accepted only on paired quality evidence.

### Evidence

Store private receipts in `evidence/implementation/NSAI-040/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-041 — Check factual support beyond citation identity

**P1 · PLANNED · REQUIRED**

Finding: CORE-09. Dependencies: NSAI-033, NSAI-040, NSAI-037. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/inference.py, answer contracts.

### Work

1. Reproduce or specify the current contract in src/nsai/inference.py, answer contracts; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Check factual support beyond citation identity. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Valid citation with invented quantity/entity is withheld.
- supported quotes/conversions retain exact provenance.
- held-out refusal/support metrics.
- model drafts always unverified.
- no second model as truth authority.

### Evidence

Store private receipts in `evidence/implementation/NSAI-041/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-042 — Bound database work and unblock async handlers

**P1 · PLANNED · REQUIRED**

Finding: CORE-15. Dependencies: NSAI-032, NSAI-040. Owner: Implementation engineer; independent verifier accepts.

Scope: src/nsai/store.py, workflow store, API.

### Work

1. Reproduce or specify the current contract in src/nsai/store.py, workflow store, API; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Bound database work and unblock async handlers. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Bounded pool/coherent snapshot/offload or async chosen from matched measurements.
- event-loop lag/connection count/SQL plans recorded.
- permission/conflict/transaction behavior unchanged.

### Evidence

Store private receipts in `evidence/implementation/NSAI-042/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-043 — Return safe original filename and media type

**P1 · PLANNED · REQUIRED**

Finding: SUP-14. Dependencies: NSAI-038, NSAI-010. Owner: Implementation engineer; independent verifier accepts.

Scope: source API, assets/app.js.

### Work

1. Reproduce or specify the current contract in source API, assets/app.js; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Return safe original filename and media type. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Viewer and download paths separated.
- safe Content-Disposition handles Unicode/control characters.
- original bytes/hash preserved.
- no automatic active-content embedding.

### Evidence

Store private receipts in `evidence/implementation/NSAI-043/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-044 — Make conversation failures and retries ordered

**P1 · PLANNED · REQUIRED**

Finding: SUP-15. Dependencies: NSAI-011, NSAI-015, NSAI-039. Owner: Implementation engineer; independent verifier accepts.

Scope: assets/app.js, session APIs.

### Work

1. Reproduce or specify the current contract in assets/app.js, session APIs; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Make conversation failures and retries ordered. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Failed asks exit pending state.
- delayed/out-of-order evidence/model calls cannot append to wrong session.
- retry idempotent.
- active/pending/closed object switches explicit.

### Evidence

Store private receipts in `evidence/implementation/NSAI-044/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-045 — Paginate and lazily render large views accessibly

**P1 · PLANNED · REQUIRED**

Finding: SUP-16. Dependencies: NSAI-042, NSAI-044. Owner: Implementation engineer; independent verifier accepts.

Scope: API list endpoints, assets/app.js.

### Work

1. Reproduce or specify the current contract in API list endpoints, assets/app.js; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Paginate and lazily render large views accessibly. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Declared 2,000-claim/100-document workload stays bounded.
- inspector size limited.
- keyboard focus/status/contrast/mobile behaviors tested.
- API pagination preserves authorization.

### Evidence

Store private receipts in `evidence/implementation/NSAI-045/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-046 — Plan capacity, holds and non-destructive retention

**P1 · PLANNED · REQUIRED**

Finding: SUP-17. Dependencies: NSAI-032, NSAI-030. Owner: Implementation engineer; independent verifier accepts.

Scope: audit/session/inference/learning stores, admin UI.

### Work

1. Reproduce or specify the current contract in audit/session/inference/learning stores, admin UI; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Plan capacity, holds and non-destructive retention. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Capacity growth and limits measurable.
- dry-run reports eligible IDs/holds/owners.
- no automatic destructive cleanup.
- future expiry/archive actions require separately reviewed policy.

### Evidence

Store private receipts in `evidence/implementation/NSAI-046/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-047 — Publish honest contracts and capability maturity

**P1 · PLANNED · REQUIRED**

Finding: SUP-18. Dependencies: NSAI-032. Owner: Implementation engineer; independent verifier accepts.

Scope: local registry, API/UI action inventory, docs.

### Work

1. Reproduce or specify the current contract in local registry, API/UI action inventory, docs; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Publish honest contracts and capability maturity. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Active/staged/unsupported/disabled states mapped to requirements, functions, routes, permissions and evidence.
- finite strict schemas.
- dormant helper presence never claims live capability.

### Evidence

Store private receipts in `evidence/implementation/NSAI-047/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-048 — Use source-bound deterministic answers where qualified

**P1 · PLANNED · REQUIRED**

Finding: REF-01. Dependencies: NSAI-041, NSAI-047. Owner: Implementation engineer; independent verifier accepts.

Scope: retrieval, answer projection.

### Work

1. Reproduce or specify the current contract in retrieval, answer projection; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Use source-bound deterministic answers where qualified. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Actual source ID/hash/review/scope validated.
- empty or prefix-only reference rejected.
- stale/unknown source denied.
- exact-answer lane benchmarked against model use without upgrading authority.

### Evidence

Store private receipts in `evidence/implementation/NSAI-048/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-049 — Accept quality and performance refinement

**P1 · PLANNED · REQUIRED**

Finding: GAP-02. Dependencies: NSAI-033, NSAI-034, NSAI-035, NSAI-036, NSAI-037, NSAI-038, NSAI-039, NSAI-040, NSAI-041, NSAI-042, NSAI-043, NSAI-044, NSAI-045, NSAI-046, NSAI-047, NSAI-048. Owner: Implementation engineer; independent verifier accepts.

Scope: quality/benchmark harnesses.

### Work

1. Reproduce or specify the current contract in quality/benchmark harnesses; freeze the audit fixture and relevant source hashes.
2. Write the smallest independent specification for: Accept quality and performance refinement. Review authority, byte/token/time/resource budgets, data lineage and backward compatibility before coding.
3. Implement incrementally in the listed surfaces. Use original synthetic or authorized fixtures; add focused positive, negative, boundary, retry and cancellation cases appropriate to the acceptance criteria.
4. Run targeted checks in owned disposable resources; compare source/output identities and relevant quality/performance contracts. Preserve failures and explain any scope changes.
5. Have an independent verifier review fresh results, recovery and remaining limitations; update the status and evidence links only after acceptance. Deploy through the release gate, not directly from a card.

### Acceptance and testing

- Matched CPU corpus and configuration, cold/warm labels, adequate predeclared samples, concurrency/queue/lag/memory data and failure cases.
- no tail/scalability claim from n=5.
- no quality/RBAC/recovery regression.

### Evidence

Store private receipts in `evidence/implementation/NSAI-049/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.
