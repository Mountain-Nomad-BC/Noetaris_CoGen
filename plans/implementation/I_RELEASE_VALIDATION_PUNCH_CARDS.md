# Release validation checklist: appended punch cards

Planning date: 2026-10-14 (America/New_York). Reviewed all 353 lines of the supplied checklist. Its SHA-256 is `460b303de2aa6bc1aa47d3ac90e12cd192ddb5afaec0678d05f41b8868baa181`.

This extension adds **18 release-validation work packages** with **209 individually traced requirements**. It supplements the original 89 cards and nine REF cards; it does not accept, replace or renumber them. No item is PASS by inheritance from a prior test count.

The machine-readable [extension ledger](release-validation-extension.json) contains exact source lines, requirements, existing-card allocations, dispositions, owners, evidence placeholders and dependencies. [CSV tracker](release-validation-tracker.csv) supports review. Requirement text is from the user-supplied checklist, not private reference code.

## Scope decisions before implementation

- CPU-first foundation and refinement remain first. AMD/Evolus and optional voice remain deferred and excluded from current claims. AMD checks remain required for any future AMD claim.
- Central security hooks remain disabled; effective local authentication stays enabled. Activation design and negative tests do not authorize activation.
- Section 7 applies to engineering issue-to-flow assembly, not a transcript product.
- The existing 14-paper corpus is development/evaluation material already inspected. It cannot be relabeled untouched holdout. The final challenge needs a new subject beyond these seven topics.
- No Git metadata currently exists. Use an explicit unavailable disposition plus a full artifact/source manifest; never invent a commit or treat missing traceability as a pass.
- Canonical security scan has not started because the host lacks a managed filesystem permission profile. Resolve that prerequisite for security acceptance; independent implementation can continue.
- Existing source hashing, 620 unit passes, 453 corpus/database checks and 31 stack checks are candidate evidence in their exact scopes. They do not prove all authorization, answer-support, OCR accuracy or release requirements.

## Execution order and stop conditions

1. REL-C00: freeze planning baseline, assign implementer and separate verifier, inventory claims and admit scoped existing receipts. Preserve failed evidence.
2. REL-C01?03: architecture/provenance, Docker/runtime and identity/governance contracts; resolve source-ACL and lifecycle design before dependent feature claims.
3. REL-C04?08: execute existing original implementation cards plus REF additions for extraction, graph/memory, retrieval, engineering flows and browser UX. Use separate versioned artifacts and bounded CPU workers.
4. REL-C10?11 and REL-C14: adversarial matrix, faults, benchmarks and evidence schema mature alongside each slice; do not wait until the end to add tests.
5. REL-C13, REL-C15 and REL-C17: frozen demos, seven independent audit passes and unseen-subject challenge. No tuning on sealed holdouts.
6. REL-C16: final CPU release decision only after all applicable mandatory requirements, rights, archive inspection and independent sign-off. Any permitted code/config/dependency change reopens affected gates.

Before each implementation slice: settle public schemas/state transitions, specify owned resources and cleanup, predeclare quality/resource thresholds, choose an independent oracle and rollback, reproduce the gap, then implement and retest. Values not yet measured remain unqualified. No unrequested live deletion, key rotation, provider activation or publication.

## Punch cards

### REL-C00: Release baseline and traceability — P0

Priority: P0. Status: PLANNED. Owner: release coordinator. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-001, NSAI-002, NSAI-047, NSAI-081. Reference additions: none.

Dependencies: none.

1. Freeze candidate source/configuration/image/model hashes and environment inventory; this tree has no Git repository, so record Git fields as unavailable and bind a complete source manifest instead of inventing commit IDs.
2. Build claim-level traceability and disabled-feature matrix; preserve existing receipts as candidate evidence only.

Acceptance: all 8 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C00/`. No overall acceptance from one passing subtest.

### REL-C01: Architecture and repository integrity — P0

Priority: P0. Status: PLANNED. Owner: component implementer. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-031, NSAI-024, NSAI-047, NSAI-060. Reference additions: REF-01, REF-02.

Dependencies: REL-C00.

1. Reconstruct routes, imports, SQL states, worker and UI contracts from actual executable paths; classify placeholders and unreachable paths.
2. Resolve provenance of existing vendor files and exact distribution rights; reference research alone is not clean-room proof.

Acceptance: all 10 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C01/`. No overall acceptance from one passing subtest.

### REL-C02: Docker security and deployment — P0

Priority: P0. Status: PLANNED. Owner: component implementer. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-021, NSAI-022, NSAI-023, NSAI-025, NSAI-027. Reference additions: none.

Dependencies: REL-C00.

1. Rebuild and inspect exact images, runtime mounts/capabilities/network/limits; run hostile probes in owned sandbox.
2. Exercise storage exhaustion, startup races, restart, shutdown and actual restore; scan exact new images rather than transferring historical scan results.

Acceptance: all 14 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C02/`. No overall acceptance from one passing subtest.

### REL-C03: Authentication, RBAC, administration, governance — P0

Priority: P0. Status: PLANNED. Owner: component implementer. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-010, NSAI-007, NSAI-064, NSAI-065, NSAI-061, NSAI-046, NSAI-089. Reference additions: REF-04.

Dependencies: REL-C00.

1. Define supported local role/object boundaries and test every read/write/export/promotion path. Current shared role credentials do not establish cross-user or tenant isolation.
2. Specify separate source ACL and session identity contracts before claiming isolation. Keep central integration disabled; test its future authenticated activation contract without enabling it.
3. Trace deletion/withdrawal across derived data, caches, audit and backups; document retention/holds without authorizing destructive live cleanup.

Acceptance: all 13 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C03/`. No overall acceptance from one passing subtest.

### REL-C04: PDF ingestion, parsing, OCR, NLP — P1

Priority: P1. Status: PLANNED. Owner: component implementer. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-013, NSAI-014, NSAI-029, NSAI-038, NSAI-053, NSAI-055, NSAI-056. Reference additions: REF-01, REF-02, REF-09.

Dependencies: REL-C00.

1. Register untouched holdouts and manual truth independently before tuning; include scanned/skewed/multicolumn/table/formula and hostile cases.
2. Measure text, OCR, table and formula quality separately; retain unanchored and unsupported records. Two rotated pages and degraded tables remain gaps until actual oracles pass.

Acceptance: all 13 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C04/`. No overall acceptance from one passing subtest.

### REL-C05: Knowledge graph, mapping, memory and autonomous learning — P1

Priority: P1. Status: PLANNED. Owner: component implementer. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-034, NSAI-039, NSAI-017, NSAI-036, NSAI-061, NSAI-088. Reference additions: REF-06, REF-07.

Dependencies: REL-C00.

1. Specify typed schema coverage and distinguish observations, similarity edges, hypotheses, contradiction and accepted claims; do not advertise general entity/event extraction from term mentions.
2. Prove deterministic lineage and source withdrawal invalidation; scope temporal/layered-memory claims to integrated features.
3. Evaluate learning improvement with contamination-controlled holdouts and independent promotion/rejection/rollback review; no autonomous trust amplification.

Acceptance: all 15 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C05/`. No overall acceptance from one passing subtest.

### REL-C06: Retrieval, query, reasoning, math and citations — P1

Priority: P1. Status: PLANNED. Owner: component implementer. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-040, NSAI-087, NSAI-041, NSAI-057, NSAI-058, NSAI-016. Reference additions: REF-03, REF-07.

Dependencies: REL-C00.

1. Benchmark implemented dense/lexical/fusion paths on frozen independent labels, including known mathematics miss; only expose modes supported by evidence.
2. Evaluate citation support and abstention with actual model outputs. Source identity alone is not entailment; existing strict-citation failures remain relevant.
3. Independently check symbolic transcription and dimensioned allowlisted calculations; no TeX or arbitrary expression execution.

Acceptance: all 11 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C06/`. No overall acceptance from one passing subtest.

### REL-C07: Issue-to-engineering-flow assembly — P1

Priority: P1. Status: PLANNED. Owner: component implementer. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-069, NSAI-070, NSAI-071, NSAI-063. Reference additions: none.

Dependencies: REL-C00.

1. Use engineering issue descriptions, not a transcript product: symptoms, measurements, hypotheses, candidate checks and outcomes remain distinct.
2. Require source applicability and safety preconditions; evaluate unfamiliar domains, contradictory inputs and missing measurements. Generated flows remain reviewable data without execution privileges.

Acceptance: all 6 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C07/`. No overall acceptance from one passing subtest.

### REL-C08: UI, PDF viewer, graphs and workflow experience — P2

Priority: P2. Status: PLANNED. Owner: component implementer. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-051, NSAI-050, NSAI-044, NSAI-045, NSAI-019, NSAI-067. Reference additions: REF-08.

Dependencies: REL-C00.

1. Exercise upload stages, authenticated PDF rendering, exact citation navigation, graph truthfulness, version changes, permission loss and offline/error states in a real browser.
2. Use independent OCR geometry for highlighting; test keyboard, focus, contrast, narrow layouts and screen-reader labels.

Acceptance: all 11 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C08/`. No overall acceptance from one passing subtest.

### REL-C09: Optional multilingual voice and duplexing — P2/P3

Priority: P2/P3. Status: DEFERRED. Owner: component implementer. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-083. Reference additions: none.

Dependencies: REL-C00.

1. Keep multilingual voice/duplex outside the current CPU release scope; publish no support claims and start no audio service.
2. If separately selected later, register language/consent/retention and per-stage latency/duplex/permission tests before implementation.

Acceptance: all 8 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C09/`. No overall acceptance from one passing subtest.

### REL-C10: Security/adversarial test matrix — P0

Priority: P0. Status: PLANNED. Owner: component implementer. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-077, NSAI-078, NSAI-079. Reference additions: REF-04, REF-07.

Dependencies: REL-C00.

1. Create original harmless fixtures for all 18 adversarial scenarios; map to a version-pinned OWASP LLM taxonomy and actual trust boundaries.
2. Run in owned isolated resources only. Dedicated security scan is blocked by unmanaged filesystem profile; resolve prerequisite before invoking it again. No substitute scan may be labeled canonical.

Acceptance: all 18 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C10/`. No overall acceptance from one passing subtest.

### REL-C11: Testing and evaluation layers — P0/P1

Priority: P1. Status: PLANNED. Owner: component implementer. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-003, NSAI-079, NSAI-025, NSAI-049. Reference additions: REF-05, REF-07, REF-09.

Dependencies: REL-C00.

1. Build a contract/branch/fault coverage matrix including cancellation, interrupted migration, DB/model failure, storage-full and resource saturation.
2. Predeclare benchmark sample sizes and quality/resource thresholds before measurements; no p95 claim from a small maximum.
3. Obtain genuinely separate reviewer replay for major claims; mark unavailable review as blocked, never self-attest independence.

Acceptance: all 14 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C11/`. No overall acceptance from one passing subtest.

### REL-C12: AMD ROCm validation and deployment — P0 for AMD-specific claims

Priority: P0_IF_AMD_CLAIMED. Status: DEFERRED. Owner: component implementer. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-086, NSAI-083. Reference additions: none.

Dependencies: REL-C00.

1. Design future AMD evidence inventory and CPU fallback only. No ROCm installation, GPU service or AMD/Evolus activation in current scope.
2. AMD inference and performance remain NOT VERIFIED until separately authorized real hardware commissioning; CPU proof cannot satisfy them.

Acceptance: all 8 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C12/`. No overall acceptance from one passing subtest.

### REL-C13: Five judge-facing demonstration scenarios

Priority: P2. Status: PLANNED. Owner: component implementer. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-068, NSAI-059, NSAI-082. Reference additions: REF-08.

Dependencies: REL-C04, REL-C05, REL-C06, REL-C07, REL-C08, REL-C10, REL-C11, REL-C14.

1. Define original fixtures and expected outcomes for demos A through E; demos A/B/C/D/E each need duration, hash, inputs, actual result, recording and evidence references.
2. Use only supported text/PDF workflows; omit voice. Freeze the same artifact for live demonstration and recorded fallback.

Acceptance: all 17 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C13/`. No overall acceptance from one passing subtest.

### REL-C14: Evidence package structure

Priority: P0. Status: PLANNED. Owner: release coordinator. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-001, NSAI-080, NSAI-081. Reference additions: none.

Dependencies: REL-C00.

1. Normalize evidence schema with immutable ID, exact requirement/build/config/model/environment/input/expected/actual/exit/artifacts/limitations/reviewer/date.
2. Keep raw private evidence separate from deployment guides and curated redacted submission projection; inspect exact archive membership and licenses.

Acceptance: all 11 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C14/`. No overall acceptance from one passing subtest.

### REL-C15: Independent audit passes

Priority: P0. Status: PLANNED. Owner: component implementer. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-079, NSAI-078, NSAI-081, NSAI-082. Reference additions: none.

Dependencies: REL-C04, REL-C05, REL-C06, REL-C07, REL-C08, REL-C10, REL-C11, REL-C14.

1. Perform seven distinct audit passes: inventory; lineage; security/IP; test quality; performance/deployment; UX/submission; final regression.
2. Assign separate verification and preserve negative results, severity, reproduction, fix identity, changed scope and retest; rerun affected gates after every freeze correction.

Acceptance: all 13 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C15/`. No overall acceptance from one passing subtest.

### REL-C16: Final release authorization — mandatory gates

Priority: P0. Status: PLANNED. Owner: release coordinator. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-082, NSAI-080, NSAI-031. Reference additions: none.

Dependencies: REL-C01, REL-C02, REL-C03, REL-C10, REL-C11, REL-C13, REL-C14, REL-C15, REL-C17.

1. Freeze CPU-only release scope; require every mandatory applicable gate and reviewer sign-off. Optional exclusions require explicit reason and absence from claims.
2. NO-GO on integrity/security defects, private asset leakage, unsupported headline claims or irreproducible essential demos; no current approval implied.

Acceptance: all 9 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C16/`. No overall acceptance from one passing subtest.

### REL-C17: Highest-value acceptance challenge

Priority: P1. Status: PLANNED. Owner: component implementer. Verifier: independent reviewer, not yet assigned.

Existing cards: NSAI-068, NSAI-082. Reference additions: REF-01, REF-03, REF-04, REF-06, REF-08.

Dependencies: REL-C04, REL-C05, REL-C06, REL-C07, REL-C08, REL-C10, REL-C11, REL-C14.

1. After code freeze select a genuinely unseen subject outside the seven development-corpus topics; record sealed provenance, questions and labels without tuning.
2. Without application edits, demonstrate all ten challenge steps through real UI/API, restart and adversarial containment. Any fix invalidates the attempt and requires a new untouched holdout.

Acceptance: all 10 linked requirements in the ledger, with expected and observed results, evidence hashes and reviewer disposition. Evidence: `evidence/release-validation/REL-C17/`. No overall acceptance from one passing subtest.

## Evidence and deployment remain distinct

Use raw private receipts under the card evidence directory. Include immutable evidence ID, requirement IDs, source/image/config/model hashes, environment, original input identity, exact command and exit status, expected threshold, actual observation, failure/retest chain, limitations, verifier and verification date. An absent independent reviewer stays unassigned and blocks acceptance. Curate a separately reviewed redacted submission projection. Deployment/reproduction instructions link to evidence; they do not absorb raw papers, secrets, private references or raw logs.

NO-GO: unresolved critical security/integrity defects, unsupported headline claims, restricted assets or irreproducible essential demonstrations. Conditional GO applies only to excluded optional features whose failures cannot affect required workflows. Current outcome remains **not release-approved**.
