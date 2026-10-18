# Current capability states — 2026-10-14

This matrix supersedes the supplied kit baseline. Fresh evidence is in `evidence/raw` and the
submission Testing & evidence section. Labels do not imply production or full PX certification.

| Capability | State | Evidence / limit |
|---|---|---|
| Docker API / DB / isolated parser / CPU model | IMPLEMENTED, LOCAL RUNTIME TESTED | Healthy real containers; loopback API only |
| TXT/Markdown/text-PDF ingestion | IMPLEMENTED, TESTED | Actual PDF upload, exact original bytes/hash, normalization/spans/chunks; no OCR |
| Source-grounded retrieval | IMPLEMENTED, TESTED | PostgreSQL lexical full-text index and resolving citations; no embeddings |
| Local AI inference/chat | IMPLEMENTED, TESTED | Real CPU llama.cpp model, structured citation IDs, provider/timing receipts; answers unverified |
| Conflict review/resolution | IMPLEMENTED, TESTED | Independent local reviewer, rationale, integrity/revision checks; alternatives preserved |
| Structured memory | IMPLEMENTED, TESTED | Scoped conversation continuation, hypotheses, reviewed canon and reflections; bounded PX plan contract |
| Full PX memory fabric / broker | PARTIAL REUSE ONLY | Pure query-plan class/build/validator imported; NSAI-specific bounded adapter |
| Remy capabilities | SELECTIVE REUSE TESTED | Actual typed TurnBurn manifest import; original UI; not full Remy app |
| Bounded learning | IMPLEMENTED, TESTED | Deterministic conflict reflections and source-backed proposals; independent review, no weight training |
| Local auth/RBAC / policy limits | IMPLEMENTED, TESTED | Role-negative tests, kill switch, rate/body/context/output/daily attempt bounds |
| Central security integration | STAGED, DISABLED | Config/admin interface only; activation is denied |
| Audit and source integrity | IMPLEMENTED, TESTED | DB immutability and app privileges, verifiable append-only hash chain; no external anchor |
| Fixed parser containment | LOCAL RUNTIME TESTED | UID/caps/seccomp, noexec scratch, denied internet and DB networking |
| Arbitrary generated-code executor / Linux Gremlin | DISABLED / NOT IMPLEMENTED | No Docker socket or admitted hostile-code backend; all roles denied execution |
| Browser UI | IMPLEMENTED, TESTED | Real Chromium workflow and mobile check; source/model text escaped |
| Restart persistence | TESTED | Actual DB/API restart retains document IDs/hashes and authentication |
| Backup restoration | TESTED | All 11 table fingerprints match in network-isolated disposable restore; live DB untouched |
| Browser identity isolation | TESTED | Late response after logout discarded; role switch clears private views |
| Runtime dependency audit | TESTED, NO KNOWN ADVISORIES | Locked patched packages; scanned at build time; not a guarantee against undiscovered flaws |
| Container image CVEs | FINDINGS RETAINED | Base-OS advisories visible in SARIF/SBOM; no public production clearance |
| Submission materials | PREPARED, PRIVATE | Separate evidence/provenance/demo/security/AMD/blocker docs, screenshots and draft silent video |
| AMD ROCm/vLLM / Evolus | DEFERRED BY USER | Existing preparation retained; no activation; local stability and refinement come first |
| Ollama profile | SOURCE/CONTRACT TESTED; RUNTIME PENDING | Optional retained profile; large download stopped in favor of validated existing GGUF |
| Production OIDC/TLS / cloud partners / publication | NOT ENABLED | Requires separate authorization, identity, security and license gates |
