# Copy/paste handoff — phases 1–2: data, ingestion and evidence

Complete DATA-01..03, ING-01..05, RET-01, EVD-01..02 with explicit prerequisites from ledger. Read `docs/modules/REMY_SELECTION.md`, `docs/modules/PX_SELECTION.md`, `docs/modules/INDEX_AND_MEMORY_LIFECYCLES.md`.

- Use independent clean-room TurnBurn-inspired source pipeline: TXT/Markdown/PDF MIME checks, bounded file parsing, exact source page/section spans, stable hashes and revisions, deterministic chunk manifest; no Remy code or data transfer.
- Adopt PX-inspired object semantics via strict isolated Pydantic types; do not import whole `runtime.*`. Preserve Apache notices if source actually ported, or implement independent equivalents.
- Develop DB migration+backfill with explicit versioned records and append-only events. `database/migrations/0002_evidence_candidates.sql` is **draft, not applied or tested**; staging-test and fix it.
- Contradiction detection handles unit normalization, old/new revisions, duplicate-source suppression, uncertainty, source authority and missing citations.
- Human review requires independent authenticated reviewer and event receipt. A model response or schema object alone does not grant permission.
- Produce golden tests, negative tests and genuine provenance round trips. No automatic candidate promotion.

Target: a simple real upload of fictional conflicting vendor documents yields two traceable candidate claims and a review queue, with a hard fail on unauthorized promotion.
