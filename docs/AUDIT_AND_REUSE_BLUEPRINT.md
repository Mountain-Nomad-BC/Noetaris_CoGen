# NSAI: Remy + Pacify-X source audit and reuse blueprint

**Audit baseline:** source ZIPs supplied October 12, 2026. **Status:** source-inspection and focused static assessment, not a certified whole-repository audit. All 50 paths in `SOURCE_USAGE_MATRIX.csv` were checked against the archive central directories. Docker was unavailable in the analysis environment; no actual container or AMD GPU was started. No Remy implementation code is distributed in this starter.

**Archive counts:** Remy 19,833 actual files (21,302 ZIP entries including directories; ~1.17 GB uncompressed); PX 7,634 files (8,636 ZIP entries including directories; ~405 MB uncompressed). These are repository inventories, not proof of deployable code.

## Executive architecture decision

Build a small standalone NSAI public repository with the following ownership:

| Concern | Owner | Source influence | Current level |
|---|---|---|---|
| Human-facing chat / document review | NSAI clean-room frontend | Remy admin frontend designs | Original mini-console created |
| TurnBurn-style autodidactic corpus intake | NSAI ingestion and index lifecycle | Remy TurnBurn pipeline | Design only; narrow deterministic ingestion stub exists |
| Evidence, contradictory claims and provenance | NSAI evidence store with PX-style controls | PX `nsai_knowledge`, `knowledge_refinery`, trusted evidence | Original candidate-evidence stub created |
| Versioned, bounded memory and query context | NSAI memory interfaces | PX memory fabric, broker, learning promotion | Planned; not integrated |
| Agent/skill governance | NSAI candidate workflow + separate executor | PX work admission, knowledge foundry | Planned, disabled in starter |
| Persistence | PostgreSQL locally; Supabase later | Neither giant native storage stack | Local Compose schema created |
| Model inference | Explicit OpenAI-compatible connector | Remy remote-client design; AMD vLLM | Endpoint adapter created; not exercised against real GPU |
| Linux host isolation | Docker + dedicated sandbox service | Remy hardening patterns; PX sandbox policy concepts | Compose security controls created; runtime untested |
| Deep Gremlin monitoring | Future Linux-specific enforcement adapter | PX Gremlin architecture | Not imported; Windows backend excluded |

This does **not** mean copying Remy wholesale or treating the RIE app as the backend. Remy's current architecture depends on company-specific identity, multiple stages, services, and knowledge directories. NSAI should not reproduce that dependency graph for the event.

## Legal/IP boundary — release blocker for Remy direct source

The archive root `Rie_Remy_codebase/LICENSE` explicitly labels the codebase and associated assets proprietary/confidential to Rheem Manufacturing Company and requires an authorized written agreement for copying, modification, publication, or redistribution. Some frontend files contain older license comments that do not override the root restriction. Treat all Remy code and knowledge data as internal-only unless the relevant owners grant explicit permission. This document identifies conceptual functional patterns for original NSAI development. It does **not** grant a license to transfer proprietary source.

PX root `Pacify-X-main/LICENSE` is Apache-2.0. The presence of the license does not remove obligations to preserve notices or verify third-party assets. If copying specific PX files, check `THIRD_PARTY_NOTICES.md`, attribution, dependencies and any non-Apache material individually. PX licensing and provenance should be reviewed before publication.

## Source-side observations

### Remy: strongest reusable design ideas

- **Chat interface**: `4_admin_tooling/admin_frontend/src/ai/remy/RemyAssistant.tsx`, `RemyContext.tsx`, `RemyInteraction.tsx`; user-facing interactions, chat session state, feedback, source citation, and optional voice integration. **Do not lift directly**: frontend has a company-specific dependency graph and proprietary license. NSAI should implement its own chat/evidence interface.
- **TurnBurn**: `7_Remy/remy/turnburn/corpus_builder.py` is a substantial corpus builder with source collection, semantic/structured chunk processing, embeddings, FAISS index logic, clustering and graph-related artifacts. `service.py` tracks candidate indexes, validation, promotion and rollback. `search.py` integrates multiple retrieval strategies. Separate **index promotion** from **knowledge promotion** in NSAI; a good index does not make its contents true.
- **Source-aware retrieval**: `turnburn/source_links.py`, `turnburn/corpus_validation.py`, `retrieval/controlled_retriever.py`, `knowledge/provenance.py` suggest source lineage, policy-scoped retrieval and evaluated recall. Make citations mandatory in proposed answers.
- **Graph**: `7_Remy/remy/graph/service.py` has alias resolution, graph neighbors, paths, and provenance-aware visibility. Keep out of the initial demo until the underlying claim ontology is stable.
- **Learning**: `7_Remy/remy/learning/service.py` explicitly documents *governed feedback capture only* and does not self-modify production truth. Therefore **do not describe the present implementation as a trained, autonomous self-improving model**.
- **Memory**: `7_Remy/remy/memory/service.py` handles session ownership, user preferences and durable items; this is not a replacement for PX-style multi-hypothesis and bitemporal memory.
- **Inference**: `7_Remy/remy/models/remote_client.py` offers useful provider patterns; implement a small original OpenAI-compatible adapter rather than porting the full gateway.
- **Observability**: Remy telemetry and audit events provide useful patterns; keep identities and customer traces out of any public demo.

### Pacify-X: strongest portable candidates

- **Existing NSAI schemas**: `contracts/nsai/knowledge-object.schema.json`, `formula-object.schema.json`, `runtime/nsai_knowledge.py` already implement deterministic object IDs, canonical JSON hashing, contract validation, bounded library scanning, provenance checks and explicitly `authority_granted=false` semantics. The `knowledge/nsai` corpus contains representative knowledge objects. These deserve first review, not a fresh incompatible object format.
- **Refinery**: `runtime/knowledge_refinery.py` implements novelty and similarity classification and proposes merges/graph updates without writing directly to canonical truth. Use it as the foundation for a candidate review workflow, not automatic source replacement.
- **Foundry**: `runtime/knowledge_foundry.py` includes structured knowledge artifacts and checked calculation ASTs. Reuse validation ideas, but use separate Linux execution isolation if future generated skills become executable.
- **Memory**: `runtime/memory_fabric.py` supplies memory classes, shard identity, admission/correction semantics; `runtime/memory_broker.py` constructs bounded, provenance-aware context materialization. `memory_broker.py` directly imports `memory_fabric`, `memory_intelligence`, and hash helpers, so it is **not** a copy-one-file library.
- **Learning**: `runtime/learning_promotion.py` has formal candidate hypotheses, confidence gates, revision freeze and promotion decisions. Keep its authority checks independent from agent or model output.
- **Trust**: `runtime/trusted_evidence.py`, `runtime/event_ledger.py` are worth reviewing for signed evidence/custody and append-only tracking. The initial SQL scaffold is not equivalent to full signed PX evidence.
- **Addressing and routing**: `runtime/compact_address.py`, `capability_routing.py` are optional optimization layers after data shape stabilizes. In the six-day slice, simple typed IDs and deterministic routes are sufficient.
- **Sandbox**: `runtime/isolated_sandbox.py` defines policy semantics. `runtime/gremlin/containment.py` has receipts and a containment facade, but `runtime/gremlin/host_enforcement_backend.py` invokes Windows Job Objects and Win32 APIs; this is not Linux AMD host enforcement. Do not claim containment on Linux merely because a policy report says it is enabled.
- **Docker model runtime**: `runtime/docker_model_runtime.py` handles modeled OCI identity and lifecycle planning; useful future management pattern but not a substitute for actual AMD GPU container setup.

## Role and authority decomposition

```text
[Original NSAI Console]
      | auth, uploads, evidence views
      v
[NSAI API] --- [PostgreSQL: documents + candidate claims + claim events]
      |                        ^
      v                        |
[Ingestion / TurnBurn-inspired builder] --- [candidate index]
      |                               |
      v                               v
[PX-inspired refinery] ----------> [Review / evidence gate]
      | candidate proposals             |
      v                                 v
[Reasoning + bounded memory] <---- [approved knowledge projection]
      |
      +--> [Private AMD ROCm vLLM endpoint]
      |
      +--> [policy gate] --> [isolated executor: separate Linux service, no network]

All cross-component interfaces are versioned, with model output treated as proposals.
```

### Canonical ownership

- `document_store`: source bytes/hash/version and source locator. No model-driven mutation.
- `candidate_ledger`: immutable observations and conflict links.
- `knowledge_canon`: versioned promoted objects; human/owner authority required.
- `index_store`: disposable embeddings/FAISS/pgvector, with source+embedding-version binding.
- `working_memory`: per-job temporary hypotheses, independent from published knowledge.
- `capability_registry`: executable code candidates, test receipts and signed release authorization.
- `execution_service`: actual OS isolation; no direct model access to Docker daemon.
- `audit_ledger`: append-only with issuer, timestamp, digest, action, outcome.

## Normalized NSAI interfaces

| Interface | Inputs | Outputs | Invariants |
|---|---|---|---|
| `DocumentIngestor.ingest` | bytes, MIME, source identity, revision, actor | document manifest + candidate claims | bounded file size; deterministic hash; raw source preserved |
| `ClaimExtractor.extract` | source + parse segments | candidate claims + locators | no claimed verification; text treated as untrusted |
| `IndexBuilder.build` | specific document revisions and embedder digest | candidate index manifest | immutable index generation; rebuildable |
| `RetrievalProvider.search` | actor, scope, query, budgets | cited passages + score | no cross-tenant/source leakage |
| `Refinery.assess` | candidates, existing records, policy | duplicate/variant/conflict/novel proposals | no canonical write |
| `KnowledgeApprover.promote` | proposals, evidence bundle, actor authorization | signed revision event | independent permission check, rollback lineage |
| `MemoryBroker.materialize` | query plan, scopes, trust floor, revisions | bounded context, evidence IDs | no untrusted claim presented as canonical |
| `ModelGateway.generate` | authorized context and budgets | model text, usage/latency | endpoint configured by operator only |
| `SkillCandidate.validate` | source, contract, tests, resource limits | test evidence and review request | no direct live execution from model response |
| `SandboxExecutor.run` | approved artifact digest, job identity, resource policy | exit status, bounded logs, custody receipt | network disabled unless explicitly authorized |

## First implementation order

- **P0 / already included in starter**: independent UI, local authenticated API, deterministic claim extraction, source-line locators, conflict groups, candidate-only state, PostgreSQL schema, local Compose baseline and a network-disabled sandbox smoke service.
- **P1 / next**: generic document parser (MD/TXT/PDF with page references), TurnBurn-inspired chunk/index lifecycle, hybrid retrieval, automated source hash verification, independent knowledge approval, live AMD vLLM smoke, owner-scoped identity.
- **P2 / only after working P1**: PX `nsai_knowledge` schemas/refinery adapters, per-job memory materialization, timed versioning, bounded autonomous proposal loop, cross-model evaluation.
- **P3 / post-hackathon**: full graph exploration, complex adaptive routing, durable process custody, Gremlin Linux enforcement host implementation, voice, training/fine-tuning and full plugin ecosystems.

### Engineering acceptance gates

**Gate 0 (legal):** no company-proprietary source or documents in public repo, Docker image or demo. **Gate 1 (reproducibility):** compose config, local build, health/ready, migrations, smoke tests succeed. **Gate 2 (evidence):** doc dedupe and source locators work, contradictory claims remain separate, no candidate auto-promotion. **Gate 3 (security):** no Docker socket/privileged mode/host networking/unguarded ports, network-disabled executor proven, secrets not logged, scan passes. **Gate 4 (AMD):** ROCm GPU visible inside inference container, model endpoint accessible only to API, real AMD invocation logged and reproduced. **Gate 5 (demo):** scripted 85C vs 75C conflict, traceable evidence, model correctly labels uncertainty, repeatable numbers.

**Accuracy notes:** The source archive inspection verifies existence and code shape, not that each component is tested, deployable, licensed for reuse, or suitable for extraction without repair. Starter generated code has a ten-test Python baseline; no whole-source regression suite or real Docker deployment was performed in this pass.
