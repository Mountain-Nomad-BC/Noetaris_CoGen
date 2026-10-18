# Source exclusion and read-only data-health increment

Candidate: `sha256:29a977c7edbe19ae45a31b518616ffc0443f8d7a141dff2cc54d606f8b20c992`. No live stack, originals, backups, database schema or user ownership was changed. This is part of implementation-stage source admission and inventory (NX-03), not the comprehensive section-4 audit or independent acceptance.

## Implemented behavior and file map

`src/nsai/source_admission.py` centrally excludes available path components beginning NSAI_MASTER_CORPUS, including named rebuild variants, case variants, compatibility-normalized Unicode and trailing Windows spaces/dots. Exclusion is refusal of trusted processing, never deletion. `admit_filesystem_source` refuses symlinks and reparse ancestors, including an aliased selected base. `read_source_bytes` enforces a bounded regular-file read and detects identity/size/mtime changes; it does not silently truncate sources.

`src/nsai/ingestion.py` applies the name exclusion before the public parser dispatch. `scripts/ingest_arxiv_corpus.py`, `enrich_arxiv_corpus.py` and `query_arxiv_corpus.py` check manifest/source paths before import, enrichment, encoding or querying. Corpus-relative traversal guards remain. Trusted manifests/artifacts now reject duplicate JSON members and nonfinite or excessive structures through the existing strict decoder, without rewriting retained source JSON.

This checks available path provenance, not the unknowable origin of renamed/copied opaque bytes. No filename check establishes originality or factual authority. Independently retained source snapshots can be reviewed outside excluded generated trees; arbitrary uploaded data still cannot promote itself into canonical knowledge. Existing database sources were not bulk rewritten or newly certified.

`src/nsai/source_health.py` inspects bounded JSON/JSONL and generic graph shapes without importing or indexing them. It detects malformed/duplicate-key records, missing/duplicate IDs, declared mixed families, explicit duplicate active heads and unresolved generic graph endpoints. Physical JSONL records are LF/CRLF based; blank/invalid records are not silently skipped. Reports cap issue output and explicitly mark omitted findings/incompleteness. Unclassified schemas stay unclassified; annotations do not prove canonical schema validity, reference closure, semantic truth or complete extraction.

`scripts/audit_source_health.py` and `tests/test_source_health_inventory.py` select/verify explicit workspace data/datasets/evaluations roots, refuses links, writes detailed affected paths/IDs only under a protected private state directory and emits an aggregate public receipt. It never changes originals, deletes excluded trees, invokes an encoder or writes canonical/graph state. It bounds files, bytes and processing time and rechecks selected original hashes. Source/arrival races and unsupported family checks remain explicit limitations; no general system certification is inferred.

## Fresh evidence

- `evidence/implementation/source-exclusion-tests.xml`: 71 focused tests passed for initial path exclusion and existing parser/import behavior.
- `evidence/implementation/source-path-admission-tests.xml`: 46 passed for linked-base refusal, bounded original reads and neighboring parser/import behavior.
- `evidence/implementation/source-health-tests.xml`: 28 passed for duplicate/mixed/head/orphan/blank-line/issue-budget data cases, preserved bytes and path admission. Invalid fixture records remain retained, not repaired or deleted.
- `evidence/structured-sources/ea549fc202224cca966818a1febe38ba/receipt.json`: 16 actual Chromium/API/parser/PostgreSQL checks pass on this image. The additional known-defective-name upload returns422 and creates no document; CSV/JSON originals and analysis/chart behavior still pass. Owned cleanup and unchanged source checks pass.
- `evidence/source-health/4e0021e633b74965a7e3db1bfc44959b/receipt.json`: 278 selected JSON/JSONL files, 211,701,526 bytes, zero parse/read failures and zero detected generic graph/record findings; all selected bytes and tool sources unchanged. 222 files are schema-unclassified. Detailed findings are private; `private-report-acl.json` verifies current-account/SYSTEM-only access and protected parent inheritance. The literal status PASS_INVENTORY_WITH_FINDINGS denotes an inventory result with a findings field, which is zero here.
- `evidence/release-validation/REF-07/8a133d2bac3b4bb28a78b46c20e65f28/lineage.json`: read-only native structural oracle passes for all14 prepared research documents, including declared artifact/original hashes, quoted source spans, graph endpoints, formula source binding, embedding token coverage and candidate memory membership. This establishes structural association only, not scientific truth, OCR/formula accuracy or semantic relevance.

Exact-image full regression `evidence/private-access/09bb72d7ecad4bb499f1c770363103da/receipt.json` passed1,307 tests with zero failures/errors/skips, packaged-source identity and unchanged inputs verified. Prior1,287 belongs to image623ba7f6. After that snapshot, the operator-only inventory walker gained streaming scandir enumeration and explicit directory/entry/time bounds plus generic public filesystem error messages. `source-health-walk-tests.xml` passes22 focused checks; fresh inventory `evidence/source-health/bf978ea302a54f97b1e9ab5cf0644e04/receipt.json` again covers278 files with no detected defects and unchanged bytes. This later operator-script change does not change packaged application code or independently accept any criterion.

## Remaining and rollback

NX-03 remains IN_PROGRESS: canonical-family schemas, cross-file active-head/source-reference closure, semantic review and broader approved-scope inventory are not complete. XLSX and the wider operational expansion remain unfinished. A new XML parser wheel/license has only been staged and hash verified; it is not activated or a claim of workbook support.

No live deployment occurred. Keep older exact images and matching database clones; never delete excluded corpora as cleanup or downgrade a schema-sealed image onto an upgraded database. Current individual-user content admission and independent acceptance prerequisites remain closed.
