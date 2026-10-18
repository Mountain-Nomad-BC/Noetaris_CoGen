# Evaluation design — measured accuracy, provenance and performance

## Unit of measurement and baseline

The supplied `evaluations/run_fixture_baseline.py` runs the existing **narrow deterministic regex extractor** on fully fictional TXT documents. It is a regression sanity check, **not** an AMD LLM benchmark or proof of system learning. Extend fixtures and add a true baseline comparator before any claims of superiority.

| Metric | Exact definition | Evidence required |
|---|---|---|
| Contradiction precision | TP flagged contradictions / (TP+FP flags), with 0-denominator reported N/A | Labeled document pairs |
| Contradiction recall | TP flagged contradictions / (TP+FN actual contradictions) | Labeled pair set independent from tuning |
| Citation match rate | Responses with exact retrievable source span supporting asserted claim / responses with assessed claims | Annotated source spans and cases |
| Unsupported assertion rate | Unsupported factual assertions / all evaluated factual assertions | Independent annotated labels |
| Retrieval recall@k | Expected gold source(s) in first k authorized results / cases | Frozen candidate index+query set |
| Answer abstention accuracy | Cases needing abstention where answer abstains / all such cases | Labeled missing/ambiguous cases |
| Model p50/p95 latency | 50th/95th percentile of measured elapsed milliseconds for inference requests | Raw timings, host/version/batch size |
| Job throughput | Completed ingest jobs / elapsed min, report source bytes and size | Raw job receipts and compute resources |
| Cost per doc | Actual inference+GPU/billed platform spend / complete docs processed | Provider invoice/credits + timing logs |

Separate `manual` review, `deterministic` extractor, and `AMD model` results. For credible comparison, use same unseen dataset, same test machine/load or measured explicit hardware differences and pre-registered acceptance thresholds. Reporting "0 hallucinations" on 3 fixtures is not a meaningful general claim.

## Failure classes to include

Unknown values; source conflict; stale revision; missing scanned PDF text; prompt injection; deliberate near-duplicate and unit mismatch (`85°F` vs `85°C`); source text mutation after hashing; cross-project retrieval; model timeout/500; authorization replay; poisoned index; long-file truncation.

## Release thresholds (proposed, not proven)

- 100% of returned factual claims in the demo's gold set resolve to source references or explicit `unsupported`.
- 100% unauthorized promotion/execution attempts blocked in deterministic security tests.
- All intentionally contradictory pairs in golden set are surfaced as unresolved candidates.
- No failing regressions at demo release.
- Actual AMD request and host GPU proof for all claims of AMD model involvement.

Thresholds are acceptance criteria, not observed metrics. Store raw results under `docs/validation/results/` (exclude any secrets/personally identifying content) and tag git revision.
