# NSAI — Master Build Plan

**Plan basis:** two supplied archives, October 12 starter, event site reviewed October 12 2026. **This is an execution specification, not a claim that the whole project has been built.**

## Technical north star

Build one standalone evidence-governed knowledge pipeline: synthetic supplier documents -> immutable source/version -> candidate claims -> contradiction graph -> source-grounded retrieval -> AMD-hosted open-model explanation -> optional human-approved Evolus business workflow. Remy is design/reference only while proprietary; PX components are candidates for licensed selective adaptation but **not imported** here.

### Non-negotiable invariants

1. Candidates are never canonical truth just because a model says so.
2. An activated retrieval index is not a promoted claim.
3. Proposed skills cannot execute themselves.
4. The execution sandbox is not the ordinary API container; a smoke container proves only its own configuration.
5. Real GPU usage and partner usage must be measured, not asserted.
6. Public repo cannot include Remy proprietary source, company data, personal information, or secrets.
7. Each task is atomic; complete prerequisites and gate before advancing.

## Program gates

| Gate | Purpose | Exit criteria |
|---|---|---|
| G0 | Local baseline | Docker/DB/API boot, authentication, two revisions, persistence, security baseline |
| G1 | Knowledge | Strict contracts, source locators, deterministic manifest, immutable revision schema |
| G2 | Trust | Conflict review, unauthorized promotion blocked, full claim history |
| G3 | AMD | Real AMD ROCm/vLLM host served at private or secured URL, request+timing log |
| G4 | Demo | Golden dataset, baseline+NSAI metrics, traceable end-to-end user journey |
| G5 | Public | Auth/TLS, secret/license scans, incident rollback and release checks |

## Critical path

`BASE-01 → BASE-03 → BASE-04 → BASE-08 → DATA-02 → DATA-03 → ING-01 → ING-02 → ING-03 → EVD-01 → AMD-01 → AMD-02 → AMD-03 → OPS-01 → OPS-02 → OPS-03`

The GPU work can run in parallel to source processing. Partner Evolus work must never block the primary AMD demonstration.

## Work package instructions

### P0 Foundation

| ID | Priority | Task | Dependencies | Status |
|---|---|---|---|---|
| BASE-01 | BLOCKER | Verify platform prerequisites | — | SCAFFOLD_READY |
| BASE-02 | BLOCKER | Sanitize repo and license boundaries | BASE-01 | SCAFFOLD_READY |
| BASE-03 | BLOCKER | Validate local secrets / no default tokens | BASE-01 | SCAFFOLD_READY |
| BASE-04 | BLOCKER | Start DB and API via Compose | BASE-01,BASE-03 | EXISTING_UNVERIFIED |
| BASE-05 | BLOCKER | Harden container baseline and prove it | BASE-04 | STATIC_PASS_RUNTIME_UNVERIFIED |
| BASE-06 | P0 | Create CI/check command | BASE-01 | SCAFFOLD_READY |
| BASE-07 | P0 | Record dependency lock & image provenance | BASE-06 | NOT_STARTED |
| BASE-08 | P0 | Baseline deterministic demo | BASE-04 | EXISTING_UNVERIFIED |
| BASE-09 | P1 | Implement health and capability truth reporting | BASE-04 | PARTIAL_EXISTING |
| SEC-01 | BLOCKER | Enforce least-privilege DB and networks | BASE-04 | BASELINE_ONLY |

#### BASE-01 — Verify platform prerequisites

**Edit/create:** `scripts/preflight.py; docs/runbooks/LOCAL_FIRST_BOOT.md`

**Implementation:** Record Python 3.12+, Docker Engine/Desktop, Compose plugin, free disk, available ports; do not claim GPU unless device visible.

**Acceptance:** Preflight report saved with actual versions; prerequisites met.

**Prerequisites:** None · **Current state:** SCAFFOLD_READY

#### BASE-02 — Sanitize repo and license boundaries

**Edit/create:** `LICENSE; .gitignore; docs/IP_RELEASE_BOUNDARY.md; scripts/release_audit.py`

**Implementation:** Use independent NSAI code only; no Remy source/data or unreviewed PX additions; verify license and public asset ownership.

**Acceptance:** No forbidden files, PII, tokens, employee/customer records or company-specific knowledge.

**Prerequisites:** BASE-01 · **Current state:** SCAFFOLD_READY

#### BASE-03 — Validate local secrets / no default tokens

**Edit/create:** `scripts/bootstrap_secrets.py; secrets/; .env.example`

**Implementation:** Generate random DB and API token once; restrict file access; never print tokens.

**Acceptance:** Secrets unique, exist, ignored by git, not in archives.

**Prerequisites:** BASE-01 · **Current state:** SCAFFOLD_READY

#### BASE-04 — Start DB and API via Compose

**Edit/create:** `Dockerfile; compose.yaml; deploy/init.sql`

**Implementation:** Run compose config, up -d --build, readiness, token reject/accept and restart persistence.

**Acceptance:** API responds; DB healthy and private; logs no credentials.

**Prerequisites:** BASE-01,BASE-03 · **Current state:** EXISTING_UNVERIFIED

#### BASE-05 — Harden container baseline and prove it

**Edit/create:** `compose.yaml; docs/runbooks/DOCKER_AND_SANDBOX.md; scripts/validate_compose_security.py`

**Implementation:** Verify non-root, readonly, cap drop, no new privs, limits, no published DB, no docker socket; validate runtime effective settings.

**Acceptance:** Static checker PASS and docker inspect evidence archived.

**Prerequisites:** BASE-04 · **Current state:** STATIC_PASS_RUNTIME_UNVERIFIED

#### BASE-06 — Create CI/check command

**Edit/create:** `scripts/run-checks.*; .github/workflows/ci.yaml; tests/`

**Implementation:** Run tests, syntax, static compose checker, release-audit; fail on errors; lock dependency resolution before release.

**Acceptance:** CI reflects current environment, all gates green with logs.

**Prerequisites:** BASE-01 · **Current state:** SCAFFOLD_READY

#### BASE-07 — Record dependency lock & image provenance

**Edit/create:** `pyproject.toml; Dockerfile; deploy/amd/compose.amd.yaml`

**Implementation:** Freeze dependency hashes; pin container image digests for public deployment; record OS/ROCm/model versions.

**Acceptance:** Reproducible builds and digest inventory; no latest tags.

**Prerequisites:** BASE-06 · **Current state:** NOT_STARTED

#### BASE-08 — Baseline deterministic demo

**Edit/create:** `scripts/demo_seed.py; datasets/demo/; src/nsai/api.py`

**Implementation:** Seed two revisions; query claims/conflicts; seed twice; reboot and check persistence.

**Acceptance:** 2 documents, 2 candidate claims, 1 conflict group; re-seed no growth.

**Prerequisites:** BASE-04 · **Current state:** EXISTING_UNVERIFIED

#### BASE-09 — Implement health and capability truth reporting

**Edit/create:** `src/nsai/api.py; docs/STATUS_MATRIX.md`

**Implementation:** Expose detailed versioned capability statuses live/disabled/unverified and logs of actual running mode.

**Acceptance:** Never report AMD/PX/TurnBurn live if not exercised.

**Prerequisites:** BASE-04 · **Current state:** PARTIAL_EXISTING

#### SEC-01 — Enforce least-privilege DB and networks

**Edit/create:** `compose.yaml; database/migrations/`

**Implementation:** DB not publicly reachable, API on dedicated networks, separate DB roles before production, no untrusted container joins data network.

**Acceptance:** Network probes from sandbox fail; migration role separated.

**Prerequisites:** BASE-04 · **Current state:** BASELINE_ONLY

### P1 Knowledge

| ID | Priority | Task | Dependencies | Status |
|---|---|---|---|---|
| DATA-01 | BLOCKER | Review PX NSAI schema source | BASE-02 | ANALYZED_NOT_PORTED |
| DATA-02 | BLOCKER | Versioned strict NSAI evidence contracts | DATA-01 | SCAFFOLD_READY |
| DATA-03 | BLOCKER | Migrate DB for revisions and claim events | DATA-02,BASE-08 | NOT_STARTED |
| DATA-04 | P0 | Add per-project auth and isolation | DATA-03 | NOT_STARTED |
| ING-01 | BLOCKER | Upload pipeline with size/MIME caps | DATA-03,DATA-04 | NOT_STARTED |
| ING-02 | BLOCKER | Text/PDF/Markdown parsers + locators | ING-01 | NOT_STARTED |
| ING-03 | P0 | Content-addressed chunking + manifest | ING-02 | NOT_STARTED |
| ING-04 | P0 | Candidate claim extraction via AMD model | ING-03,AMD-03 | NOT_STARTED |
| ING-05 | P0 | Source lineage and revisions | ING-03 | NOT_STARTED |
| RET-01 | P0 | Start lexical FTS index | ING-03,DATA-03 | NOT_STARTED |
| EVD-01 | P0 | Novelty/dedup/conflict refinery | ING-05 | BASIC_DEMO_EXISTS |

#### DATA-01 — Review PX NSAI schema source

**Edit/create:** `contracts/nsai/* [reference only]; docs/modules/PX_SELECTION.md`

**Implementation:** Inspect PX knowledge/formula schema and nsai_knowledge.py + dependencies, note exact fields/semantic gaps; only adopt with legal notice handling.

**Acceptance:** Document schema field map, tests and compatibility decision.

**Prerequisites:** BASE-02 · **Current state:** ANALYZED_NOT_PORTED

#### DATA-02 — Versioned strict NSAI evidence contracts

**Edit/create:** `src/nsai/contracts/evidence.py; src/nsai/contracts/lifecycle.py`

**Implementation:** Define source ref, claim event, canonical hashing, timezone and status; reject unknown authority flags.

**Acceptance:** Pure contract tests including NaN, timestamps, unknown fields and stable hashes.

**Prerequisites:** DATA-01 · **Current state:** SCAFFOLD_READY

#### DATA-03 — Migrate DB for revisions and claim events

**Edit/create:** `database/migrations/; deploy/init.sql; src/nsai/store.py`

**Implementation:** Separate source document identity/version, immutable claim revision, valid and observed time, claim relations and actor-bound audit; no DROP or destructive changes.

**Acceptance:** Migration up/down staging, constraints, dedupe and restart tests.

**Prerequisites:** DATA-02,BASE-08 · **Current state:** NOT_STARTED

#### DATA-04 — Add per-project auth and isolation

**Edit/create:** `src/nsai/auth/; services/api/; database/migrations/`

**Implementation:** Require per-user/project scoping and authorization before public hosting; current token is LOCAL DEMO ONLY.

**Acceptance:** 403 across projects; audit access; authorization tests.

**Prerequisites:** DATA-03 · **Current state:** NOT_STARTED

#### ING-01 — Upload pipeline with size/MIME caps

**Edit/create:** `src/nsai/ingestion/upload.py; services/api/routes/ingest.py`

**Implementation:** Use bounded streams, filename normalization, allowlisted MIME and content sniffing; limit PDF pages/size; reject archive bombs and external references.

**Acceptance:** Oversized/malformed/unsupported upload returns errors without side effects.

**Prerequisites:** DATA-03,DATA-04 · **Current state:** NOT_STARTED

#### ING-02 — Text/PDF/Markdown parsers + locators

**Edit/create:** `src/nsai/ingestion/parsers.py; tests/fixtures/`

**Implementation:** Add text and Markdown with locators; PDF with controlled parser and page references; fail or quarantine scans until OCR present.

**Acceptance:** Exact line/page citations round trip to source material.

**Prerequisites:** ING-01 · **Current state:** NOT_STARTED

#### ING-03 — Content-addressed chunking + manifest

**Edit/create:** `src/nsai/ingestion/chunker.py; src/nsai/ingestion/manifest.py`

**Implementation:** Chunk deterministically with overlap, hash each source/chunk and retain page/section/offset; enforce max chunk count.

**Acceptance:** Identical input produces same manifests and chunks.

**Prerequisites:** ING-02 · **Current state:** NOT_STARTED

#### ING-04 — Candidate claim extraction via AMD model

**Edit/create:** `src/nsai/ingestion/extract.py; src/nsai/inference.py`

**Implementation:** Use schema-validated structured extraction with direct source spans; cross-check source substrings; reject invented citations; define deterministic fallback.

**Acceptance:** Golden extraction cases; fail closed on unsupported model output.

**Prerequisites:** ING-03,AMD-03 · **Current state:** NOT_STARTED

#### ING-05 — Source lineage and revisions

**Edit/create:** `src/nsai/evidence/provenance.py`

**Implementation:** Preserve exact source hash/version plus immutable evidence locator; avoid any direct auto-promotion.

**Acceptance:** Stale/altered source rejected, prior versions retrievable.

**Prerequisites:** ING-03 · **Current state:** NOT_STARTED

#### RET-01 — Start lexical FTS index

**Edit/create:** `src/nsai/retrieval/lexical.py; database/migrations/`

**Implementation:** Implement PostgreSQL tsvector or constrained local FTS; tenant-filter query first; explain ranking.

**Acceptance:** Top-k baseline golden queries and tenant boundary tests.

**Prerequisites:** ING-03,DATA-03 · **Current state:** NOT_STARTED

#### EVD-01 — Novelty/dedup/conflict refinery

**Edit/create:** `src/nsai/evidence/refinery.py; src/nsai/models.py`

**Implementation:** Normalize subject+predicate+units; detect contradiction and revision precedence; preserve alternatives; adapt PX semantics separately.

**Acceptance:** Golden conflicting/duplicate/ambiguous cases pass, nothing auto-verified.

**Prerequisites:** ING-05 · **Current state:** BASIC_DEMO_EXISTS

### P2 Retrieval

| ID | Priority | Task | Dependencies | Status |
|---|---|---|---|---|
| RET-02 | P1 | Introduce embedding adapter and vector index | RET-01,AMD-03 | NOT_STARTED |
| RET-03 | P1 | Hybrid fusion + citation checking | RET-01,RET-02 | HELPER_READY |
| RET-04 | P1 | TurnBurn-style index candidate lifecycle | RET-03 | CONTRACT_READY |
| AMD-04 | P0 | Quantitative inference evaluation | AMD-03 | NOT_STARTED |

#### RET-02 — Introduce embedding adapter and vector index

**Edit/create:** `src/nsai/retrieval/embedder.py; database/migrations/`

**Implementation:** Model/version digest, dimension compatibility, bounded batch and vector retrieval; preserve model-independent authoritative claim store.

**Acceptance:** Index version matches embedding identity, reindex roundtrip.

**Prerequisites:** RET-01,AMD-03 · **Current state:** NOT_STARTED

#### RET-03 — Hybrid fusion + citation checking

**Edit/create:** `src/nsai/retrieval/fusion.py`

**Implementation:** Combine authorized ranked results with deterministic fusion, dedupe, source presence check, bounded context.

**Acceptance:** Score stability, missing source refusal and golden precision checks.

**Prerequisites:** RET-01,RET-02 · **Current state:** HELPER_READY

#### RET-04 — TurnBurn-style index candidate lifecycle

**Edit/create:** `src/nsai/retrieval/index_lifecycle.py; src/nsai/contracts/lifecycle.py`

**Implementation:** Build staged generation from hashed corpus; evaluate golden retrieval; activate explicitly; keep previous generation rollback pointer.

**Acceptance:** No activation without tests; rollback after bad index; independent from claim promotion.

**Prerequisites:** RET-03 · **Current state:** CONTRACT_READY

#### AMD-04 — Quantitative inference evaluation

**Edit/create:** `evaluations/; docs/validation/METRIC_DEFINITIONS.md`

**Implementation:** Benchmark on fixed fixtures with timestamps, real token usage, latency distributions, source support rate, contradiction catch.

**Acceptance:** Saved JSON+CSV results and reproducible commands, no invented improvements.

**Prerequisites:** AMD-03 · **Current state:** NOT_STARTED

### P2 Governance

| ID | Priority | Task | Dependencies | Status |
|---|---|---|---|---|
| EVD-02 | P0 | Human review queue and promotion state machine | EVD-01,DATA-03,DATA-04 | PURE_GATE_READY |
| EVD-03 | P0 | Trusted receipts and ledger anchoring | EVD-02 | HELPER_ONLY |
| EVD-04 | P1 | Bitemporal query behavior | DATA-03,EVD-02 | NOT_STARTED |
| SEC-03 | P0 | Prompt-injection and data contamination suite | ING-04,EVD-02 | SMOKE_ONLY |

#### EVD-02 — Human review queue and promotion state machine

**Edit/create:** `src/nsai/evidence/promotion.py; src/nsai/learning/gates.py`

**Implementation:** Require authorized reviewer, evaluation receipt, conflict outcome; event-sourced append-only state changes; no direct model approval.

**Acceptance:** Unauthorized/expired/replayed approval rejected; history verifiable.

**Prerequisites:** EVD-01,DATA-03,DATA-04 · **Current state:** PURE_GATE_READY

#### EVD-03 — Trusted receipts and ledger anchoring

**Edit/create:** `src/nsai/audit/; database/migrations/`

**Implementation:** Record actor identity, source digest and decision; enforce append-only DB permissions; optionally externally anchor signed root digest.

**Acceptance:** Tamper attempt detected; claims cannot silently rewrite history.

**Prerequisites:** EVD-02 · **Current state:** HELPER_ONLY

#### EVD-04 — Bitemporal query behavior

**Edit/create:** `src/nsai/memory/temporal.py`

**Implementation:** Support as-observed-at and effective-at; backdated revision never erases previous belief.

**Acceptance:** As-of historical queries reproduce versioned results.

**Prerequisites:** DATA-03,EVD-02 · **Current state:** NOT_STARTED

#### SEC-03 — Prompt-injection and data contamination suite

**Edit/create:** `tests/adversarial/; evaluations/golden/`

**Implementation:** Instruction-in-document is data; cannot override system authority or promote truth.

**Acceptance:** Zero unauthorized promotions/executions on defined adversarial fixtures.

**Prerequisites:** ING-04,EVD-02 · **Current state:** SMOKE_ONLY

### P2 Memory

| ID | Priority | Task | Dependencies | Status |
|---|---|---|---|---|
| MEM-01 | P1 | Inspect PX broker/fabric dependency closure | DATA-01 | SOURCE_AUDITED_PARTIAL |
| MEM-02 | P1 | Bounded memory materialization | MEM-01,RET-03,EVD-04 | NOT_STARTED |

#### MEM-01 — Inspect PX broker/fabric dependency closure

**Edit/create:** `docs/modules/PX_SELECTION.md; src/nsai/memory/`

**Implementation:** Trace memory_broker, memory_fabric, memory_intelligence, hash helper and test dependency closure.

**Acceptance:** Decision table with direct import graph, license and tests.

**Prerequisites:** DATA-01 · **Current state:** SOURCE_AUDITED_PARTIAL

#### MEM-02 — Bounded memory materialization

**Edit/create:** `src/nsai/memory/context.py`

**Implementation:** Keep working/session/evidence memory distinct; budget citations and context tokens; filter by project and authority level.

**Acceptance:** Deterministic budget and no unauthenticated cross-scope memory.

**Prerequisites:** MEM-01,RET-03,EVD-04 · **Current state:** NOT_STARTED

### P3 Advanced

| ID | Priority | Task | Dependencies | Status |
|---|---|---|---|---|
| MEM-03 | P2 | Competing hypothesis slots and scoring | MEM-02 | DEFER |

#### MEM-03 — Competing hypothesis slots and scoring

**Edit/create:** `src/nsai/memory/hypotheses.py`

**Implementation:** Optional bounded up to 12 hypotheses per owner, weighted evidence/confidence and revision history; no one-way collapse absent authority.

**Acceptance:** 12-slot boundary and reproducible ranking tests.

**Prerequisites:** MEM-02 · **Current state:** DEFER

### P1 AMD

| ID | Priority | Task | Dependencies | Status |
|---|---|---|---|---|
| AMD-01 | BLOCKER | Allocate AMD host and record ROCm/GPU | BASE-01 | NOT_STARTED |
| AMD-02 | BLOCKER | Start ROCm/vLLM in separate container | AMD-01,BASE-05 | CONFIG_ONLY |
| AMD-03 | BLOCKER | Connect actual AMD inference to API | AMD-02,BASE-09 | CLIENT_ONLY |

#### AMD-01 — Allocate AMD host and record ROCm/GPU

**Edit/create:** `deploy/amd/AMD_HOST_CHECKLIST.md; deploy/amd/amd-preflight.sh`

**Implementation:** Record provider, credits, GPU type, devices, drivers, memory, CUDA-incompatible assumptions, IP/firewall and image details.

**Acceptance:** rocminfo or equivalent, ls device nodes and host inventory saved.

**Prerequisites:** BASE-01 · **Current state:** NOT_STARTED

#### AMD-02 — Start ROCm/vLLM in separate container

**Edit/create:** `deploy/amd/compose.amd.yaml`

**Implementation:** Use verified compatible container digest/model; device passthrough only and no privileged mode; protect endpoint from public access.

**Acceptance:** Model health/chat completion on actual AMD GPU, GPU utilization recorded.

**Prerequisites:** AMD-01,BASE-05 · **Current state:** CONFIG_ONLY

#### AMD-03 — Connect actual AMD inference to API

**Edit/create:** `src/nsai/inference.py; compose.yaml`

**Implementation:** Provide internal private endpoint or secure HTTPS; strict timeout/retry; record actual model digest/token metrics; never make model host arbitrary via request.

**Acceptance:** /v1/reason returns model_unverified or verified-at-source mode accurately; timeout tests.

**Prerequisites:** AMD-02,BASE-09 · **Current state:** CLIENT_ONLY

### P3 Deployment

| ID | Priority | Task | Dependencies | Status |
|---|---|---|---|---|
| AMD-05 | P0 | GPU spend and shutdown controls | AMD-02 | NOT_STARTED |
| SEC-04 | BLOCKER | Production identity and TLS | DATA-04,CHAT-01 | NOT_STARTED |
| SEC-05 | P0 | Supply-chain scans and secret tests | BASE-07 | STATIC_BASELINE_ONLY |

#### AMD-05 — GPU spend and shutdown controls

**Edit/create:** `deploy/amd/; docs/runbooks/AMD_DEPLOYMENT.md`

**Implementation:** Record credit budget, idle shutdown command, scheduled manual checks and burn estimates measured from provider billing.

**Acceptance:** Demonstration runs without surprise public GPU bill.

**Prerequisites:** AMD-02 · **Current state:** NOT_STARTED

#### SEC-04 — Production identity and TLS

**Edit/create:** `deploy/production/; src/nsai/auth/`

**Implementation:** OIDC authenticates user and project; HTTPS termination, CSRF/session defenses, CORS limited, request limits.

**Acceptance:** External security checks; no shared local bearer token as public auth.

**Prerequisites:** DATA-04,CHAT-01 · **Current state:** NOT_STARTED

#### SEC-05 — Supply-chain scans and secret tests

**Edit/create:** `scripts/release_audit.py; .github/workflows/ci.yaml`

**Implementation:** Run dependency audit, SBOM, container vulnerability scan and secret scanning; fix findings by severity before publish.

**Acceptance:** Reports included in release evidence bundle.

**Prerequisites:** BASE-07 · **Current state:** STATIC_BASELINE_ONLY

### P1 Console

| ID | Priority | Task | Dependencies | Status |
|---|---|---|---|---|
| CHAT-01 | P0 | Adapt existing clean-room chat layout | BASE-04 | MINI_CONSOLE_EXISTS |

#### CHAT-01 — Adapt existing clean-room chat layout

**Edit/create:** `assets/; src/nsai/api.py`

**Implementation:** Retain original NSAI console; implement session threads, evidence panels, statuses and source links without Remy source/branding.

**Acceptance:** Responsive input/output, source navigation, visible demo vs GPU state.

**Prerequisites:** BASE-04 · **Current state:** MINI_CONSOLE_EXISTS

### P2 Console

| ID | Priority | Task | Dependencies | Status |
|---|---|---|---|---|
| CHAT-02 | P1 | Document viewer and source locator | ING-02,CHAT-01 | NOT_STARTED |
| CHAT-03 | P1 | Conflict and candidate review panel | EVD-02,CHAT-01 | NOT_STARTED |
| CHAT-04 | P1 | Memory and execution trace panel | MEM-02,CHAT-01 | NOT_STARTED |

#### CHAT-02 — Document viewer and source locator

**Edit/create:** `assets/; services/api/routes/documents.py`

**Implementation:** Fetch source only after authorization, highlight actual page or line, HTML escape, sanitize client rendering.

**Acceptance:** Clicking a citation resolves exact original text, no XSS.

**Prerequisites:** ING-02,CHAT-01 · **Current state:** NOT_STARTED

#### CHAT-03 — Conflict and candidate review panel

**Edit/create:** `assets/; services/api/routes/review.py`

**Implementation:** Show alternative claims with version, source, confidence and distinct review controls; no UI-only authority.

**Acceptance:** Reviewer action requires backend authorization and event receipt.

**Prerequisites:** EVD-02,CHAT-01 · **Current state:** NOT_STARTED

#### CHAT-04 — Memory and execution trace panel

**Edit/create:** `assets/; services/api/routes/traces.py`

**Implementation:** Show token budgets, retrieved evidence, decision chain and model/provider.

**Acceptance:** Trace IDs match server audit events, user scopes respected.

**Prerequisites:** MEM-02,CHAT-01 · **Current state:** NOT_STARTED

### P3 Agents

| ID | Priority | Task | Dependencies | Status |
|---|---|---|---|---|
| AGT-01 | P1 | Define non-executable proposed skills | EVD-02 | CONTRACT_READY |
| AGT-02 | P1 | Sandbox execution admission gate | AGT-01,SEC-02 | NOT_STARTED |
| AGT-03 | P2 | Skill generation and evaluation | AGT-02,AMD-03 | NOT_STARTED |
| SEC-02 | BLOCKER | Build real Linux sandbox executor | BASE-05 | NOT_STARTED |

#### AGT-01 — Define non-executable proposed skills

**Edit/create:** `src/nsai/contracts/lifecycle.py; src/nsai/skills/manifest.py`

**Implementation:** Plan-only skill candidates with strict JSON schema, allowed tools, input/output contracts and tests; no raw Python runtime.

**Acceptance:** Cannot set execution_enabled in proposal; reviewer can inspect spec.

**Prerequisites:** EVD-02 · **Current state:** CONTRACT_READY

#### AGT-02 — Sandbox execution admission gate

**Edit/create:** `src/nsai/security/; services/worker/`

**Implementation:** Require signed authorization, approved immutable artifact digest, denied-by-default capabilities; fail closed on missing sandbox.

**Acceptance:** Bypass, replay, mutation, symlink and denied-network tests.

**Prerequisites:** AGT-01,SEC-02 · **Current state:** NOT_STARTED

#### AGT-03 — Skill generation and evaluation

**Edit/create:** `src/nsai/skills/generator.py; src/nsai/skills/evaluator.py`

**Implementation:** Generate candidates only, static validate, run adversarial tests in isolated runtime, review before release.

**Acceptance:** No generated code runs in API, worker without containment or unaudited state.

**Prerequisites:** AGT-02,AMD-03 · **Current state:** NOT_STARTED

#### SEC-02 — Build real Linux sandbox executor

**Edit/create:** `deploy/security/; services/executor/`

**Implementation:** Rootless or microVM/namespace-isolated executor with seccomp/AppArmor, no network, no Docker socket, readonly mounts, quotas; independent host launch authority.

**Acceptance:** Adversarial execution test proves enforced filesystem/network/process limits.

**Prerequisites:** BASE-05 · **Current state:** NOT_STARTED

### P2 Partner

| ID | Priority | Task | Dependencies | Status |
|---|---|---|---|---|
| EVO-01 | P1 | Create Evolus event workspace | AMD-03 | NOT_STARTED |
| EVO-02 | P1 | Connect self-hosted AMD model to Evolus | EVO-01,AMD-02 | NOT_STARTED |
| EVO-03 | P1 | Implement one business workflow | EVO-02,ING-03 | CLIENT_SCAFFOLD_ONLY |

#### EVO-01 — Create Evolus event workspace

**Edit/create:** `docs/event/EVOLUS_OPTIONAL.md`

**Implementation:** Enter event code from kickoff, create workspace/API key and choose two required building blocks.

**Acceptance:** Workspace ID, credits, app ID and model endpoint verified (secrets private).

**Prerequisites:** AMD-03 · **Current state:** NOT_STARTED

#### EVO-02 — Connect self-hosted AMD model to Evolus

**Edit/create:** `docs/event/EVOLUS_OPTIONAL.md`

**Implementation:** Expose locked-down HTTPS vLLM endpoint that Evolus can reach; auth/allowlist if supported; test agent real inference.

**Acceptance:** Workspace logs show actual AMD model calls and endpoint health.

**Prerequisites:** EVO-01,AMD-02 · **Current state:** NOT_STARTED

#### EVO-03 — Implement one business workflow

**Edit/create:** `src/nsai/integrations/evolus.py; docs/event/EVOLUS_OPTIONAL.md`

**Implementation:** Build document extractor + workflow, e.g. vendor specification discrepancy -> human approval; use REST, no fabricated payload schema.

**Acceptance:** Workflow returns artifact, NSAI stores receipt, human handoff proven.

**Prerequisites:** EVO-02,ING-03 · **Current state:** CLIENT_SCAFFOLD_ONLY

### P3 Partner

| ID | Priority | Task | Dependencies | Status |
|---|---|---|---|---|
| EVO-04 | P2 | Prove partner qualification | EVO-03 | NOT_STARTED |
| GGL-01 | P3 | Verify Google prize rules before implementation | BASE-08 | DEFER |

#### EVO-04 — Prove partner qualification

**Edit/create:** `docs/event/EVOLUS_OPTIONAL.md`

**Implementation:** Validate two building blocks, event workspace usage, AMD vLLM, REST invocations and config log evidence.

**Acceptance:** Recorded demo and verifiable workspace statistics.

**Prerequisites:** EVO-03 · **Current state:** NOT_STARTED

#### GGL-01 — Verify Google prize rules before implementation

**Edit/create:** `docs/event/GOOGLE_OPTIONAL.md`

**Implementation:** Obtain official Google partner requirements and technology allowed; do not assume merely using Google tools qualifies.

**Acceptance:** Requirements matrix verified with current event instructions.

**Prerequisites:** BASE-08 · **Current state:** DEFER

### P2 Demo

| ID | Priority | Task | Dependencies | Status |
|---|---|---|---|---|
| OPS-01 | BLOCKER | Create synthetic industrial supplier dataset | ING-02 | MINIMAL_FIXTURES_READY |
| OPS-02 | P0 | Golden evaluation harness + baseline | OPS-01,RET-01,EVD-01 | NOT_STARTED |

#### OPS-01 — Create synthetic industrial supplier dataset

**Edit/create:** `datasets/synthetic/; evaluations/golden/`

**Implementation:** Invent clean non-proprietary supplier revisions, PO/inventory conflicts with ground truth and citations.

**Acceptance:** Dataset licenses/claims synthetic and expected outcomes recorded.

**Prerequisites:** ING-02 · **Current state:** MINIMAL_FIXTURES_READY

#### OPS-02 — Golden evaluation harness + baseline

**Edit/create:** `evaluations/; docs/validation/METRIC_DEFINITIONS.md`

**Implementation:** Record true/false positive contradictions, citation match rate, unsupported answer rate and p50/p95 latency.

**Acceptance:** Machine-readable raw per-case results + aggregate summary.

**Prerequisites:** OPS-01,RET-01,EVD-01 · **Current state:** NOT_STARTED

### P3 Demo

| ID | Priority | Task | Dependencies | Status |
|---|---|---|---|---|
| OPS-03 | P0 | End-to-end demo script | OPS-02,AMD-03,CHAT-01 | NOT_STARTED |
| OPS-04 | BLOCKER | Public release preflight and rollback | SEC-04,SEC-05,OPS-03 | NOT_STARTED |
| OPS-05 | P0 | Submission package and measurable claims | OPS-03 | NOT_STARTED |
| OPS-06 | P1 | Hand-off and future roadmap | OPS-05 | NOT_STARTED |

#### OPS-03 — End-to-end demo script

**Edit/create:** `docs/event/DEMO_AND_SUBMISSION.md`

**Implementation:** Screen capture: ingest changed vendor docs -> conflicts -> review -> retrieved answer -> AMD request -> optional Evolus action.

**Acceptance:** Reproducible demo in single session with errors/fallbacks described.

**Prerequisites:** OPS-02,AMD-03,CHAT-01 · **Current state:** NOT_STARTED

#### OPS-04 — Public release preflight and rollback

**Edit/create:** `scripts/release_audit.py; docs/runbooks/PUBLIC_DEPLOYMENT.md`

**Implementation:** Prove license, secret hygiene, upload safety, production auth/TLS, observability, backup and rollback.

**Acceptance:** All blockers green or no public deployment; use local demo otherwise.

**Prerequisites:** SEC-04,SEC-05,OPS-03 · **Current state:** NOT_STARTED

#### OPS-05 — Submission package and measurable claims

**Edit/create:** `docs/event/DEMO_AND_SUBMISSION.md; docs/event/SUBMISSION_COPY.md`

**Implementation:** Prepare GitHub README, hosted app URL, video, slide outline and measured stats; choose primary track.

**Acceptance:** Complete submitted fields; check actual platform deadline time.

**Prerequisites:** OPS-03 · **Current state:** NOT_STARTED

#### OPS-06 — Hand-off and future roadmap

**Edit/create:** `docs/POST_EVENT_ROADMAP.md`

**Implementation:** Separate future multi-hypothesis, 12-slot memory, compact routing, autonomous skill promotion and Gremlin Linux from demo.

**Acceptance:** Future scope never described as implemented now.

**Prerequisites:** OPS-05 · **Current state:** NOT_STARTED

## How to use this ledger

- Keep task statuses as `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `PASS`, or `FAIL`; scaffolds are **not** passes.
- Pick tasks only when all IDs in `depends_on` have passing gates, except documented parallel branches.
- For each task provide actual changed files, commands executed, test output, open risks and rollback.
- There is no requirement to implement P3 advanced autonomy before hackathon submission.

## Scope stops

If time becomes short, **cut** voice, graph visualization, generic executable generated skills, multi-tenant SaaS, and extra partner prize tracks. **Do not cut** source lineage, AMD integration, a real end-to-end demo, Docker safety, and honesty in capability states.
