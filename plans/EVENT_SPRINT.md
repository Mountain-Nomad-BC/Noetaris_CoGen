# Six-day delivery lanes — event build 12–18 Oct 2026

**Deadline caution:** official public page confirms Oct 12–18 event but does not clearly publish an exact submission hour in the retrieved page text. Verify time inside your lablab.ai submission dashboard and submit early. Allocate margin for video upload and GitHub checks.

| Day | Must finish | Optional if ahead | Proof to save |
|---|---|---|---|
| Oct 12 | G0 local boot, secure Compose checks; Git branch, clean release boundary, sample conflicting text. | UI polish | Docker `ps`, health response, claims JSON, pytest output |
| Oct 13 | G1 strict contracts, migration for immutable source revisions, parsers/chunking and source locators. | PDF viewer | Schema tests, source round-trip, 3 source hashes |
| Oct 14 | G2 conflict lifecycle; lexical retrieval; evaluation dataset; candidate-only memory. | Vector index | Golden cases, no auto-promotion test |
| Oct 15 | AMD cloud instance, GPU probes, vLLM model inference and NSAI endpoint; do this earlier if credits allow. | Vector retrieval, Evolus workspace | Actual AMD model trace, GPU metrics, latency |
| Oct 16 | G4 complete demo with citations and no false promotion; bounded bench; choose primary business track. | Evolus two blocks | Video rehearsal, per-case evidence table |
| Oct 17 | UI polish, security scans, README, release verification, record demo/video/screenshots. | Evolus proof, partner extras | CI green, clean release zip, demo artifact |
| Oct 18 | Early submission, validate public links and playable video, shut down unused GPU afterward. | Nothing high risk | Submission confirmation and cost record |

## Time-box rules

- If AMD is not up by end of Oct 15, allocate the next engineering slot to GPU connectivity, not more architecture.
- If TurnBurn-inspired general ingestion is delayed, constrain demo to TXT/Markdown/PDF with explicit known-source locators; do not fake knowledge extraction.
- If the public production identity is not ready, run a private controlled demo behind authenticated access; never put the local bearer-token app directly onto the internet.
- If an Evolus workspace key or model public ingress consumes the remaining schedule, prioritize the AMD main challenge. Google remains separate/optional.

## Engineering parallelism

- Lane A: data/knowledge (DATA, ING, RET, EVD, MEM).
- Lane B: deployment/runtime (BASE, SEC, AMD).
- Lane C: UI/demonstration (CHAT, OPS).
- Lane D: partners (EVO, GGL), starts only after AMD connectivity proof.

For solo work, advance one blocked gate at a time; avoid parallel writes to `src/nsai/api.py` or `compose.yaml` from multiple coding agents.
