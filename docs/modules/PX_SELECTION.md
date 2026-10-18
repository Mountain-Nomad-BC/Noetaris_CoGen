# Pacify-X selected capabilities — explicit use and dependency boundaries

PX has Apache-2.0 root licensing, but per-file imports, notices and third-party provenance still require review. This kit copied no PX implementation. If using verbatim PX code later, preserve notices. The source matrix records exact source paths verified in the supplied archive.

| File | Value to NSAI | Internal dependency/constraint | Implementation choice / priority |
|---|---|---|---|
| `contracts/nsai/knowledge-object.schema.json` | Already defines NSAI knowledge object contract | Verify required fields, object IDs and authority semantics | **P0 inspect** and map to new `contracts` objects, avoid silent incompatibility |
| `contracts/nsai/formula-object.schema.json` | Typed formula representation | Formula evaluation may be dangerous without restricted AST | P2 map, don't execute formulas in API |
| `runtime/nsai_knowledge.py` | Canonical hashing, deterministic ID, bounded schema checking | Imports PX `archive_io`, `bounded_walk`, `contracts`, `json_io` | Extract only verified pure semantics or write adapter; no giant import |
| `runtime/knowledge_refinery.py` | Novelty/dedup/merge candidates | Needs source and similarity rules; proposals vs writes | **P1 evaluate** for `evidence/refinery.py` |
| `runtime/trusted_evidence.py` | Producer, scope and evidence receipt | Signature/identity validation must work outside prompt | P1 evidence receipts with explicit trust root |
| `runtime/event_ledger.py` | Chronological custody events | DB append-only, hash chain anchoring | P1 immutable ledger semantics; current helper not secure ledger |
| `runtime/learning_promotion.py` | Promotion decision gates, revision freeze | Strong admission roles, evidence and independent actors | P1/P2 govern candidate canon; never allow model to sign off |
| `runtime/memory_fabric.py` | Multi-class records, identities, corrections | Shard/store semantics and test dependencies | P2 targeted memory record model |
| `runtime/memory_broker.py` | Context materialization and bounded memory | Imports `memory_fabric`, `memory_intelligence`, `hash_utils` | P2 adapter after tracing dependency closure; no drop-in copy |
| `runtime/knowledge_foundry.py` | Proposed structured skills/calculations | Validation is NOT runtime isolation | P3 declarative skills only until Linux sandbox |
| `runtime/capability_routing.py` | Deterministic capability selection | Registry and policies | P2 only if typed routes needed |
| `runtime/compact_address.py` | Compact deterministic address logic | Requires stable canonical IDs | Defer beyond first 6-day slice |
| `runtime/isolated_sandbox.py` | Resource and policy intent | OS backend needed to enforce | Recreate policy contract and map to Linux executor |
| `runtime/gremlin/containment.py` | Custody/receipt concepts | Host enforcement is platform-specific | Defer Linux Gremlin adapter |
| `runtime/gremlin/host_enforcement_backend.py` | Windows Job Object enforcement | Win32 APIs and kernel32 not Linux compatible | **Exclude** from AMD runtime |
| `runtime/process_supervisor.py` | PX host orchestration | Tight links to PX host/custody | Exclude |
| `runtime/docker_model_runtime.py` | OCI image and lifecycle abstractions | Modeling does not start a ROCm service | Defer; Compose controls v0.1 |
| `runtime/work_admission.py` | Approval scope and process authority | PX release ledger not portable wholesale | P2 narrow NSAI admission contract |
| `runtime/provider_gateway.py` | Provider budget/retry handling | Broad gateway and model routes | Defer until AMD adapter measured |

## Port-or-reimplement gate

1. Verify exact file in archive and license/notice. Read direct import closure and bundled unit tests.
2. Port one pure behavior at a time behind NSAI contract; do not import `runtime.*` wildcard modules.
3. Record baseline/ported behavioral fixtures with byte-for-byte deterministic expected results.
4. Add policy downgrade controls: unknown fields rejected, no implicit grants, mandatory citations.
5. If port includes signing/authority, prove actual verifier/issuer and private-key custody; never fabricate approval records.
6. Benchmark after correctness, not before.

## Recommended memory map

- `working`: current task, proposals, ephemeral context; short TTL.
- PX M01/M02/M03 broker roles are a **specific source behavior to inspect and map**, not evidence this kit already includes the broker. Keep per-process/workflow/agent primary and secondary memory boundaries if source contracts validate that design.
- `evidence`: exact source and claim observations; immutable source hashes.
- `hypotheses`: competing unpromoted versions (optional 12-slot advanced expansion).
- `canon`: independently approved projection, reviewed history retained.
- `reflection`: measured errors/feedback and proposed improvements, not executable instructions.
- `skills`: candidate manifests distinct from approved executable deployment artifacts.

Do not force all layers into one generic vector store. Memory's authority and timestamp logic belongs in persistent relational/versioned tables; embeddings are disposable retrieval aids.
