# H: Deferred commissioning boundaries

Status: planning artifacts only. No card is accepted by this document.

## NSAI-083 — Disposition unqualified providers and accelerator profiles

**P2 · PLANNED · DEFERRED_NO_ACTIVATION**

Finding: SUP-22. Dependencies: NSAI-082. Owner: Implementation engineer; independent verifier accepts.

Scope: Ollama/AMD/NVIDIA/Evolus adapters, deploy.

### Work

1. Record the interface/disposition and prerequisites only.
2. Keep code paths, provider activation, generated execution and central enable disabled.
3. Reopen as a separately authorized implementation epic after the listed local gates and selected workload.

### Acceptance and testing

- Keep inactive.
- future selected provider needs pinned image/model, host/TLS/egress policy, license and own quality/security/cost benchmark.
- latest/outbound profiles never silently join CPU baseline.

### Evidence

Store private receipts in `evidence/implementation/NSAI-083/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-084 — Record deferred enterprise features and rejected transplantation

**P2 · PLANNED · DEFERRED_NO_ACTIVATION**

Finding: REF-26. Dependencies: NSAI-068. Owner: Implementation engineer; independent verifier accepts.

Scope: reference adoption ledger.

### Work

1. Record the interface/disposition and prerequisites only.
2. Keep code paths, provider activation, generated execution and central enable disabled.
3. Reopen as a separately authorized implementation epic after the listed local gates and selected workload.

### Acceptance and testing

- Voice/STT/CRM/cloud/device/SCORM/quizzes/training/full PX fabric/full enterprise diagnostics/hostile-code execution excluded now.
- future workflow and independent data/licensing/security gates required.
- corporate source/assets/rules never adopted.

### Evidence

Store private receipts in `evidence/implementation/NSAI-084/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-085 — Define future central identity commissioning prerequisites

**P2 · PLANNED · DEFERRED_NO_ACTIVATION**

Finding: REF-27. Dependencies: NSAI-065, NSAI-082. Owner: Implementation engineer; independent verifier accepts.

Scope: future architecture only.

### Work

1. Record the interface/disposition and prerequisites only.
2. Keep code paths, provider activation, generated execution and central enable disabled.
3. Reopen as a separately authorized implementation epic after the listed local gates and selected workload.

### Acceptance and testing

- OIDC/TLS/individual identity/tenant isolation/revocation/CSRF cookie policy/external audit anchor design and isolated evidence required.
- current enable remains denied.
- later activation needs explicit user instruction.

### Evidence

Store private receipts in `evidence/implementation/NSAI-085/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-086 — Define later AMD and Evolus commissioning boundary

**P2 · PLANNED · DEFERRED_NO_ACTIVATION**

Finding: REF-28. Dependencies: NSAI-083, NSAI-082. Owner: Implementation engineer; independent verifier accepts.

Scope: future AMD/Evolus planning only.

### Work

1. Record the interface/disposition and prerequisites only.
2. Keep code paths, provider activation, generated execution and central enable disabled.
3. Reopen as a separately authorized implementation epic after the listed local gates and selected workload.

### Acceptance and testing

- No AMD changes or external workflows now.
- choose real workload after local gates, validate hardware/protocol/rights, measure matched workload and rollback, obtain explicit activation instruction.
- qualify optional local modules only when needed by the selected workload.

### Evidence

Store private receipts in `evidence/implementation/NSAI-086/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.

## NSAI-089 — Define future independent audit anchoring

**P2 · PLANNED · DEFERRED_NO_ACTIVATION**

Finding: REF-31. Dependencies: NSAI-085, NSAI-067. Owner: Implementation engineer; independent verifier accepts.

Scope: future signed export/anchor contract.

### Work

1. Record the interface/disposition and prerequisites only.
2. Keep code paths, provider activation, generated execution and central enable disabled.
3. Reopen as a separately authorized implementation epic after the listed local gates and selected workload.

### Acceptance and testing

- Local SHA256 chain never called externally signed proof.
- source-bound export and verifier/key-rotation/trust/revocation contract specified.
- future signer/anchor commissioning separately authorized.
- no key generation, external write or activation now.

### Evidence

Store private receipts in `evidence/implementation/NSAI-089/`; publish only reviewed redacted projections.

- receipt.json: source/image/configuration/input hashes, UTC time, tool/runtime versions, command and exit status, isolation scope.
- cases.json: each acceptance criterion, expected/actual result, positive and adversarial cases, retained failures.
- review.md: independent decision, capability limits, privacy/provenance review and recovery result.
- metrics.json where relevant: units, cohorts, sample counts, cold/warm/concurrency labels and paired baseline/challenger measurements.

### Recovery and completion

Revert only this change/image; restore compatible projection/configuration. For schema changes use tested compatibility path or protected restore. Preserve original records, audit events and user volumes.

All dependencies accepted, every criterion evidenced against exact source/image/configuration, independent review complete, no unresolved required regression. File presence and historical PASS do not qualify.

**Blocked when:** a prerequisite is unaccepted, required evidence is absent/stale, or the required isolation/permission/runtime is unavailable. Record the reason; do not substitute PASS.

Size after inspecting actual change and fixture scope; do not promise time from audit measurements. Split if independently recoverable changes exceed one reviewable patch.
