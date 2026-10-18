# Typed JSON source preservation

Candidate: `sha256:623ba7f638dab0c55a17145be39cc4c2fe7ab67cb036941f85b99367b6f9ff11`. JSON is now accepted through the actual existing upload UI, API, isolated parser and immutable source store. It remains source evidence; arbitrary JSON does not become a canonical object, account, instruction, approval or graph authority. No provider activation, live migration or cash request occurred.

## Exact data contract

Every original byte and SHA-256 remain retained/downloadable. UTF-8/BOM decoding is strict. Records retain types and numeric lexemes, including null versus false versus zero, negative zero, decimal scale/exponents, empty strings, empty containers and object-member order. Strings use JSON literals so controls/surrogate escape text do not become unsupported PostgreSQL text. Each value/container has a source-bound RFC 6901 URI-fragment pointer, with ~ and / escaping and UTF-8 percent encoding. A container records its child count and every child is retained; no arbitrary user dictionary is injected into system provenance fields.

Duplicate keys, nonstandard NaN/Infinity, trailing garbage, malformed encoding, excessive nesting/records/text/chunks/numeric lexeme length or pointer size reject the whole source. Bounds: existing original-byte/200,000-character limits; depth16, 5,000 typed records/chunks, 128-character numeric lexeme and 200-character source locator. No late value is silently dropped. Independent validation reconstructs every typed record and chunk from original bytes and rejects altered types/numbers/pointers, omissions, extra authority and boolean/integer shape substitutions.

JSON numeric evidence is not automatically a business table or a canonical family record. CSV/TSV calculations remain explicitly selected Decimal operations; JSON table analysis and JSONL family admission remain separate work.

## Files and checks

`src/nsai/json_sources.py`: bounded decoder, duplicate/nonstandard-number rejection, type/number/pointer records and reconstruction validator. `src/nsai/ingestion.py`: JSON dispatch and custody seam. `src/nsai/api.py`: format-aware reparse/capability description. `assets/index.html`, `assets/app.js`: accurate file chooser/descriptions and original extension. Existing `workflow_store.py` retains structured metadata transactionally without a new identity/data system.

`tests/test_json_sources.py`, `test_structured_sources.py`, `structured_sources_pg_fixture.py`: type/empty/precision/pointer/no-authority/bounds/omission checks, real parser subprocess and actual private original/manifest isolation. `evidence/implementation/json-source-focused.xml`: 143 focused checks before the final real-parser parameter; `json-source-database.xml`: 48 checks pass including the real child and PostgreSQL. Earlier no-tests commands using nonexistent test filenames are retained in tool history and do not count as verification.

`evidence/structured-sources/01ba51cb904a4e25b4883bf0cc8c73f8/receipt.json`: 15 scoped actual Chromium/API/parser/PostgreSQL checks, including prior CSV analysis/chart plus JSON upload, stored null/false/zero/decimal/empty-array distinctions and byte-identical JSON download. No application API interception/external requests/JavaScript exceptions; source/cleanup guards pass.

`evidence/operational-cost-recovery/d621868017ae44af98177268f79f589f/receipt.json`: fresh restore preserves all 50 table fingerprints, definitions/ACLs/sequences/settings, active/revoked sessions, OAuth state, cost/queue state, application-created CSV/JSON originals and exact stored JSON types. Recomputed CSV analysis has the identical analysis hash and exact 0.3 answer. Quiescent synthetic clones are not host-power-loss, off-host backup or RPO/RTO certification.

Full regression `evidence/private-access/d15c3e1b566a40758171eedfce997f4c/receipt.json` passed 1,287 tests, zero failures/errors/skips, with exact packaged source and unchanged inputs verified for this image. Prior full regression 4bc2fdf77002490db965f4caecbb3d09 passed 1,259 tests on image21a6d93 before JSON; never reuse that count as exact-image proof for this candidate.

## Remaining and rollback

XLSX, central defective-corpus exclusion/health inventory, numeric JSON table selection, filters/joins/multiple-source comparisons, report downloads, semantic/canonical/voice/target deployment work and independent acceptance remain unfinished. Current individual-user content admission remains closed. Keep the section-4 notice/report prerequisites.

Originals/backup manifests remain unchanged. Retain matching older candidate/database clones; do not downgrade a schema-sealed image onto an upgraded database or delete migration/account/audit/source history. No live rollout occurred.
