# Additional reference research and implementation punch cards

## Research boundary and evidence

The requested RH segmentation script, ingestion/retrieval libraries, RIE test roots and component library were inspected as local research only. `evidence/reference-research/new-reference-inventory.json` records file hashes, AST counts and markers. The inventory covers 463 Python test files (2,582 test functions and 12,994 assertions), 16 ingestion Python files, nine retrieval Python files, the segmentation script, and 362 component text files. Inventory coverage does not mean every body received a manual semantic review. Styles and binary fixtures were excluded. None of these reference suites was executed or imported; their environment/bootstrap code could touch unrelated systems.

Targeted body review covered segmentation/classification and reports, AST schema, chunking, retrieval fusion/filtering, embedding guardrails, revision governance, queue contracts, memory/source/graph authorization contracts, runtime claim handling, PDF workspace routing and responsive-state tests. No source bodies, proprietary dictionaries, business examples or fixtures were incorporated into this project.

## Findings and acceptance cards

These are additions to the existing plan, not replacements or accepted cards. All cards below are OPEN. Implement each with original fixtures and retain its own evidence receipt. Existing frozen corpus generations must remain reproducible.

| Card | Priority / dependency | Original implementation outcome | Acceptance evidence |
|---|---|---|---|
| REF-01 | P1; independent | Add a versioned section/block layer alongside existing exact spans: heading, paragraph, list, table candidate and unknown. Preserve original offsets and multilingual/math content; uncertain types remain candidates. | Synthetic Unicode/Greek/math, headings, multi-column ambiguity and inserted-section cases; every emitted quote maps to original spans; no silent data loss or mutation of existing generations. |
| REF-02 | P1; REF-01 | Report multiple independent quality signals and review reasons; keep quality separate from destination and semantic authority. | Corrupt text and clean non-ASCII controls; no ASCII-only corruption rule; no uncalibrated confidence represented as probability. |
| REF-03 | P1; independent | Evaluate existing reciprocal-rank fusion against dense and lexical retrieval on a frozen, independently labeled mixed corpus before wiring a new production route. Avoid duplicate fusion implementation. | Held-out recall/rank metrics and latency/resource receipts; mathematics miss included; missing dense channel permits bounded lexical fallback; source restrictions apply before and after fusion. |
| REF-04 | P1; identity design prerequisite | Design source ACL/ABAC extension with node and edge provenance filtering, including shared graph nodes, exports, originals, caches and memory. Keep central security integration disabled. | Cross-user/source denial matrix, missing-scope fail-closed cases and hidden-node bridge tests. Existing role-based access must not be described as per-user/source isolation. |
| REF-05 | P2; REF-04 | Add durable bounded encoder jobs with explicit queued/running/failed/retried status, idempotent document/model generation keys and backpressure. | Restart/retry/duplicate-submission tests with real isolated storage; no duplicate evidence, no always-running heavy model and documented CPU/storage caps. |
| REF-06 | P2; REF-05 | Separate staged, reviewed, active and historical index generations with consumer pins and reversible activation. | Concurrent activation and rollback tests; queries bind one generation; historical source references remain resolvable; no automatic promotion from similarity or ingestion success. |
| REF-07 | P1; independent | Extend original evidence oracles for graph endpoints, source quote offsets, embeddings-to-passage bijection, formula references and governance links. | Deliberate mutations rejected by actual executable checks. Some reference tools named validate_graph_sync, validate_embeddings and validate_calculations only parse arguments; they provide no validation evidence. |
| REF-08 | P2; independent | Extend PDF workspace acceptance matrix for authenticated extensionless originals, catalog/non-PDF rejection, document switch, page bounds and narrow layouts. Use MIME/owned routes rather than reference URL substring heuristics. | Actual browser checks with locally authored PDF and JSON fixtures, logout/expired access denial and source/page citation navigation. Existing 31-case stack receipt supplies baseline coverage, not completion of this card. |
| REF-09 | P1; independent | Qualify rotated OCR coordinate transforms using an independent geometry oracle before supporting the two refused pages. | Known rotated/cropped synthetic pages with expected boxes and round-trip source mapping; rerun actual refused pages only after oracle passes. OCR language/formula accuracy remains a separate qualification. |

## Patterns deliberately not adopted

Reference heading/classification code mixes domain keyword precedence, ASCII-oriented quality checks, positional identifiers and sometimes line-zero fallbacks. Those choices can obscure uncertainty or lose provenance. One retrieval filter treats missing metadata as visible; this is unsuitable for authority decisions. Mock-heavy reference tests show intended contracts but do not demonstrate runtime security or mathematical correctness. Reference PDF URL heuristics also require stricter origin/MIME contracts in a new implementation.

## Current implementation versus remaining work

Current original code already provides immutable source-bound knowledge, separate native/author mathematical JSON, candidate memory, complete-window CPU embeddings, semantic mappings, supplemental review records and real isolated restoration checks. The cards above address additional structural and operational improvements; they are not silently declared implemented by the reference inventory. No private reference suite results are included in the project's passed-test counts. No enterprise MFA, training service or central control-plane code was copied or activated.

## Final checklist integration

All nine research cards are now allocated to the [appended release-validation plan](../../plans/implementation/I_RELEASE_VALIDATION_PUNCH_CARDS.md). Its machine ledger maps the supplied checklist's individual requirements to both the original NSAI cards and this research-card namespace. Those allocations do not change any card's OPEN status or authorize implementation before planning review.
