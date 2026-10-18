# Remy/RIE component-to-NSAI selection, by source and destination

**Reuse policy:** design/reference only until actual authorized written permission exists. The supplied Remy root license is proprietary. This file is a mapping to **independent new NSAI code**, not permission to import or distribute implementation.

## What to retain conceptually

| Remy source | What it does or models | New NSAI boundary | Implementation action | Why / guardrail |
|---|---|---|---|---|
| `4_admin_tooling/admin_frontend/src/ai/remy/RemyAssistant.tsx` | Interactive assistant view | `assets/*`, future `apps/console` | Create original chat shell; evidence-side panel, tokens, job status | Best immediate UX, no company logic/branding |
| `RemyContext.tsx` (same directory) | Chat state and orchestrated interactions | `src/nsai/session/*` and browser view-model | Build scoped sessions, request IDs, cancellation | Don't import React/role/data dependency chain |
| `src/ai/RemyInteraction.tsx` | UI interaction card | `apps/console/chat` | Original document/claim tools in chat, accessible input | Avoid proprietary components |
| `src/ai/remy/RemyMemoryTrace.tsx` | Explanation of memory use | `apps/console/traces` | Show evidence IDs, ages, hypothesis candidates, context tokens | Make trace server-grounded |
| `src/components/ai/SourceCitations.tsx` | Citation interactions | `apps/console/citations` | Render sourced line/page links with hash and revision | No citation to non-retrievable source |
| `src/components/ai/PDFWorkspace.tsx` | Document reading workspace | `apps/console/documents` | Add document preview with safe source highlights | Defer until PDF parsing stable |
| `7_Remy/remy/turnburn/corpus_builder.py` | Corpus collection, semantic chunks, embedding and graph artifacts | `src/nsai/ingestion` / `retrieval` | Original deterministic chunker/manifest and embedding adapter | Preserve provenance; strip all diagnostics roots |
| `7_Remy/remy/turnburn/manifest.py` | Index/source manifests | `src/nsai/ingestion/manifest.py` | Content hashes + independent index generation IDs | Avoid stale index silently replacing source |
| `7_Remy/remy/turnburn/corpus_validation.py` | Golden retrieval evaluation | `evaluations` | Query/expected-citation fixtures and per-case reports | Must precede index activation |
| `7_Remy/remy/turnburn/service.py` | Stage/activate/rollback index | `retrieval/index_lifecycle.py` | State machine candidate → validated → activated, rollback pointer | Index status != claim truth status |
| `7_Remy/remy/turnburn/search.py` | Hybrid search | `retrieval/fusion.py` | Lexical+semantic+provenance combined under authorization | Scope-filter BEFORE fusion |
| `7_Remy/remy/turnburn/source_links.py` | Source references | `evidence/provenance.py` | Source spans, controlled URI resolver | No arbitrary path/url read from model output |
| `7_Remy/remy/graph/service.py` | Entity graph navigation | `graph/query.py` | Later claim relations, graph neighbors, aliases | Not needed to prove initial value |
| `7_Remy/remy/retrieval/controlled_retriever.py` | Permission-aware retrieval | `retrieval/policy.py` | User/project scoping + citation requirement | Never let model choose access scope |
| `7_Remy/remy/knowledge/provenance.py` | Provenance relationships | `evidence/provenance.py` | Hash, actor, evidence source lineage | Use independent code only |
| `7_Remy/remy/memory/service.py` | Chat/session durable memory | `memory/session.py` | Session events; separate from canonical knowledge | No reproduction of company user schema |
| `7_Remy/remy/learning/service.py` | Feedback/consolidation, not free-running model training | `learning/feedback.py` | Record feedback as candidates and evaluation signals | Do not advertise autonomous model training |
| `7_Remy/remy/models/remote_client.py` | Provider client | `inference.py` | Keep standard OpenAI-compatible HTTP adapter | NSAI already implements an independent stub |
| `7_Remy/remy/telemetry/service.py` | Operational traces | `observability/events.py` | Correlation IDs, inference accounting, redaction | Never log customer documents by default |
| `7_Remy/remy/safety/guard.py` | Interaction guard | `security/input.py` | Untrusted-document and prompt-injection tests | Prompt guard != OS sandbox |
| `7_Remy/remy/permissions/service.py` | Permissions service | `auth/policy.py` | OIDC-backed scopes, audit authorizations | Must be standalone for public deployment |
| `7_Remy/Dockerfile` / Compose files | Non-root/limits/health checks, mixed security | `Dockerfile`, `compose.yaml` | Reimplement hardened rules (already scaffolded) | Never import domain containers as-is |
| `7_Remy/docker-compose.gpu.yml` / `gpu-worker/docker-compose.yml` | GPU runtime patterns | `deploy/amd/*` | **Replace** with AMD ROCm/vLLM (not NVIDIA reservations) | Host must prove /dev/kfd etc |
| `docker-compose.monitoring.yml` | Monitoring stack | `deploy/monitoring` after demo | Add socket-free exporters if useful | No Docker socket in agent containers |

## Reject wholesale

Remy diagnostics content, knowledge bases, device workflows, original voice persona, hosted account identities, customer tooling, default credentials, admin backoffice and deployment scripts with employer-specific routing. Only select original *patterns*, not the application itself.

## Practical UI build order

1. Current chat panel + document textarea/JSON evidence panel (existing).
2. Add session/job state, progress and an explicit `model` mode indicator.
3. Make citations clickable to exact source span; use safe HTML escaping.
4. Add conflicting candidates review as separate alternative cards (not false forced truth).
5. Add memory trace and index-generation status after backend APIs exist.

**No direct Remy code port is authorized by this plan.**
