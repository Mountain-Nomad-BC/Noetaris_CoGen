# Release gate checklist, stop/go

| Gate | Verification artifacts | Status in this package |
|---|---|---|
| G0 local | actual Docker compose `ps`, token negative test, claim conflict, restart persistence | UNVERIFIED ON HOST |
| G1 ingest | file/page/line provenance, immutable hash, bounded parser, schema/migration | NOT COMPLETE |
| G2 trust | candidate conflicts, reviewed canon, immutable event receipts, negative authorization | PURE HELPERS ONLY |
| G3 AMD | ROCm GPU device, vLLM actual response, model+container version, latency | NOT VERIFIED |
| G4 demo | E2E video, raw metrics, click-through citations, workflow if optional | NOT COMPLETE |
| G5 public | legal clearance, OIDC+TLS, no secrets, rate limits, secure file handling, backup/rollback | NOT READY |

## Current guaranteed scope

An independently written deterministic evidence starter and planning scaffolds; local unit-level verification can be reproduced in this environment. Real deployment and product-level capability claims require executing the gates above. A verified failure is a useful finding, never something to hide by editing logs.
