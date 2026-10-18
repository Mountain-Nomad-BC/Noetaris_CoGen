# Next structured-format implementation contract

CSV/TSV are now integrated, with explicit Decimal calculations and source-bound result/chart UI. Typed JSON source preservation is now implemented in candidate623ba7f6 (see JSON_SOURCE_PRESERVATION.md); continue XLSX and further table operations as separate actual parser/store/API/UI increments, preserving every original and the existing private-response admission boundary. No schema document or adapter stub establishes support.

## JSON preservation

Use strict UTF-8/BOM decoding, duplicate-key rejection and bounded bytes/depth/value counts before admission. Reject nonstandard NaN/Infinity, trailing input and unsupported text encodings without partial publication. Preserve null, false, zero, empty string, empty object and empty array as distinct typed records. Keep original bytes/hash and numeric lexemes (including negative zero, decimal scale and exponent spelling); binary floats must not become the authoritative representation of source numbers.

Generate source-bound RFC 6901 pointer locators, escaping ~ and / correctly, including array offsets and an explicit root pointer. Preserve source key order as evidence; no email/identity/source-authority fields inside the uploaded JSON can become NSAI control metadata. Retain keys and leaf values in fixed-schema records rather than injecting an arbitrary user dictionary into system provenance traversal. Unsupported PostgreSQL text or locator-budget cases reject the whole source with an explicit reason; never silently erase a key or value.

Validation must independently reconstruct every emitted pointer/type/value from original bytes, reject missing/extra leaves and fake completeness, and preserve chunk coverage. JSON document parsing is separate from JSONL homogeneous canonical-family admission. An arbitrary uploaded object is source evidence, never a canonical object or approval.

## XLSX preservation and attack boundary

Use a maintained pinned reader with retained license/provenance and a complete dependency lock, in the existing isolated parser. Never evaluate formulas, follow external links, invoke macros, fetch URLs or execute workbook content. ZIP/container checks precede workbook parsing: duplicate/traversal/absolute entries, compression/expanded-byte/member-count bounds, malformed/truncated archives, encrypted files, macro/external-link parts and embedded active objects must fail safely. Do not extract archives into the host filesystem.

Record all worksheets including hidden sheets, exact cell coordinates, original cell type, literal value, formula text and available cached value separately. Do not infer dates/units/header rows or replace formulas with an unverified cached result. Preserve merged-cell relationships and explicitly report unsupported drawings/comments/charts/other content instead of advertising complete extraction. Bound sparse dimensions and materialized cells; an incorrect worksheet dimension must not silently hide actual data. No candidate that loses late cells or sheets may be published.

The official [openpyxl security documentation](https://openpyxl.readthedocs.io/en/stable/) states that default XML parsing needs defusedxml protection. Its [read-only documentation](https://openpyxl.readthedocs.io/en/stable/optimized.html) warns that worksheet dimensions may be inaccurate and that workbooks require explicit close. Treat these as implementation requirements, not proof that any selected package/version is already safe or qualified. No XLSX library has yet been added in this increment.

## Analysis/export continuation

Add typed filters, explicit compatible units, group comparisons across authorized source revisions and joins with explicit keys/cardinality/missingness receipts. Every source must be authorized before loading rows, and all dependencies rechecked before releasing a result or export. Do not invent values, causal explanations or numeric conversions. Keep exact Decimal values in reports and disclose rounded browser plotting geometry. Add line/scatter/table presentations and bounded downloadable artifacts tied to request/source/result hashes. Revoke object URLs on identity/source changes and reauthorize new exports; no public CDN cache for analysis content.

## Quarantine and quality gate

The master plan excludes defective generated trees named NSAI_MASTER_CORPUS, NSAI_MASTER_CORPUS_REBUILD and NSAI_MASTER_CORPUS_REBUILD_V2 from trusted ingestion, indexing, embedding and graph production. Implement path/provenance admission centrally and apply it to all import seams, including archive-relative paths and linked/reparse paths. Exclusion never deletes originals. A validated independent original snapshot is distinct from promoting a failed generated tree. Audit approved JSON/JSONL/source/graph scopes with bounded read-only checks and retain exact affected identifiers privately; do not infer semantic truth from syntactic validity or a passing graph shape.

Current missing obligations remain in NX-03 and NX-10/11/12. No independent criterion is accepted by this contract. Sections 1?3 still precede the explicit pre-section-4 audit notification and genuine independent reports.

## XLSX primary specification notes for the next implementation

Microsoft's [SpreadsheetML structure reference](https://learn.microsoft.com/en-us/office/open-xml/spreadsheet/structure-of-a-spreadsheetml-document) describes the workbook-to-worksheet relationship IDs and separate worksheet parts. Validate each relationship and every referenced sheet, not just the selected/visible sheet. Its [shared-string reference](https://learn.microsoft.com/en-us/office/open-xml/spreadsheet/working-with-the-shared-string-table) distinguishes shared strings from valid inline strings; support both without treating the shared-string index as the cell's literal text. Its [formula reference](https://learn.microsoft.com/en-us/office/open-xml/spreadsheet/working-with-formulas) separates formula text from cached values; keep those distinct and never claim the cached result has been recomputed or verified.

Choose the reader only after checking whether it preserves raw numeric lexemes and cell types. A library's Python float/date convenience representation cannot replace the original XML literal. Retain raw source-cell/formula/cache records or an equivalent independently validated original binding. Unsupported metadata/content needs explicit coverage/refusal; do not silently declare complete workbook extraction after reading only visible cells.
