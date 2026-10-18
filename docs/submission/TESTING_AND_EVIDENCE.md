# Current testing and evidence scope

Testing evidence remains separate from deployment. The private `evidence/release-validation/current.json` index identifies exact current receipts and hashes. New checks include native source/graph/formula/memory/vector lineage, supplemental author/OCR namespaces, corpus-map centroid and nearest-neighbour derivation, and real isolated PostgreSQL supplement-to-review descriptor bindings. Refer to [execution progress](../../plans/implementation/RELEASE_VALIDATION_EXECUTION.md) for exact completed runs and limitations.

The older results below are historical scopes. Their unit counts, browser outputs, source inventories, image/package scans and model results do not automatically qualify newer builds. The private static verification JSON endpoint is blocked, and public exports require a separately reviewed redacted projection. A successful job or citation ID is not evidence of scientific truth, OCR accuracy or claim entailment.

---

# Automated testing and raw evidence

This section is independent of deployment instructions. The application's Testing & evidence view
renders the fresh summary in `assets/verification.json`. Exact commands, exit statuses and output
digests live in `evidence/raw/verification-receipts.json`; source digests in `source-inventory.json`.

| Evidence | What it establishes | Where to inspect |
|---|---|---|
| Unit and contract tests | Parsing/hashes/chunks, unsafe input denial, imported PX plan validation, Remy manifest integration, role denials, citation rejection, model timeouts and disabled execution | `unit-tests-final.txt` |
| Live HTTP acceptance | Actual DB/parser collaboration, source original-byte round-trip, page citations, conflict review, stale review, session memory, reflections, central activation denial, local policy kill switch and audit verification | `live-system-current.json` |
| CPU model acceptance | Actual provider/model response, real latency and resolving source references; optional model run must be present to count as tested | Same report, `model_required` and real model result |
| Browser workflow | Authentication, synthetic sources, cited chat, source inspection, dedicated evidence view, cleared logout state and mobile layout | `browser.json`, `browser-*.png` |
| Persistence | DB/API service restart without volume deletion preserves document IDs/hashes and authentication | `persistence.json` |
| Backup recovery | Private custom-format backup restored into a network-isolated disposable database; all 11 table fingerprints match; live DB untouched | `recovery.json` |
| Browser identity isolation | Late authenticated response is discarded after disconnect; viewer controls remain denied after role switch | `session-isolation.json` |
| Effective runtime controls | Actual UID, seccomp, capabilities, readonly root, DB role and immutable table privileges | `runtime-controls.json` |
| Parser containment probes | Actual denied external egress/database DNS, dedicated secret and noexec scratch | `parser-runtime-controls.json` |
| Docker runtime inspection | Redacted actual networks/mounts/ports/resources and health, no tokens or environment dump | `docker-runtime-inspection.json` |
| Runtime dependency audit | Current known package advisories against locked dependency versions | `runtime-dependency-audit.json` |
| Image CVE/SBOM evidence | Retained base/runtime package findings; not a zero-vulnerability claim | `api-image-cves-final.sarif`, `api-sbom-final.json`, image scan logs |
| Secret hygiene | Exact generated local secret values absent from source/evidence; narrow key-pattern check | `secret-hygiene.json` |
| AMD / Evolus | Deferred by user until local foundation and subsequent refinement are complete | Historical preflight is not GPU validation |
| PX tooling observation | Metadata startup and honest broader Doctor blockers, separate from imported component tests | `px-startup.json`, `px-doctor.json` |

The starter baseline passed 24 tests. During implementation, evidence retained a Windows pytest
parameter-ID environment-limit error and an obsolete UI label assertion; these were corrected.
The static security checker initially replaced an inherited Compose service instead of merging overlays;
its merge handling was corrected. Browser checks initially lacked an FFmpeg build, then used a CSP-
disallowed string-eval wait and a premature asynchronous assertion; the verification harness was corrected
without relaxing application CSP. Earlier failures remain retained and are not presented as current passes.

Live inference subsequently exposed non-JSON-safe timestamps in continued conversation memory.
They are now serialized explicitly and covered by a real continuation acceptance check. Model key
authentication exposed a Windows CRLF incompatibility in the upstream C++ key-file reader; LF
normalization preserves the key value and is covered by a cross-platform regression test. Actual model
auth checks prove missing-key denial and admitted-key acceptance. Structured output constrains citation
IDs to retrieved sources; the citation guard still rejects invalid plain/structured responses.

The inherited Python stack/multipart parser produced known advisories. Patched FastAPI/Starlette/
multipart versions pass compatibility tests and the current runtime audit reports no known advisories.
Runtime package hashes are checked during Docker installation. Packaging utilities are removed from the
final runtime image. Image scanning still reports base-OS advisories; exact counts/severity are in the
retained SARIF and final scan summary. A filtered “no fixable high/critical” result does not mean no CVEs.
Scanner cleanup warnings on Windows are retained separately from the generated scan report.

The inherited database image's Go helper produced fixable critical/high advisories. A derived image
replaces it with su-exec, refreshes available Alpine libraries and ships only the merged patched filesystem.
The original scan (72 advisories) is retained as `db-image-cves-inherited.sarif`; the corrected image
reports 11 remaining libxml2 advisories, one high and no scanner-reported fixes. No critical findings
remain in the demonstrated database artifact. See `image-scan-summary.json` and `db-image-cves.sarif`.
These are retained limitations, not public production clearance.

Limitations: no actual ROCm GPU execution; no arbitrary-code escape certification; no full PX control-
plane certification; no semantic truth proof from citation IDs; no complete secret scanner guarantee;
no production identity/TLS assurance. The draft video is a silent local recording and not a final narrated
submission. Any model run using citation fallback is labeled accordingly; inference is real, its rejected
answer is not silently described as a successful grounded model answer.
