# Local foundation completion ledger

This ledger supersedes the inherited kit task statuses for the current authorized scope.
The original TASK_LEDGER files remain baseline planning records, not current acceptance evidence.
User priority: stabilize the local system first; refine next; Evolus and AMD later.

| Work | Current state | Evidence |
|---|---|---|
| Four-service local CPU stack | Running and tested | live-system-current.json; docker-runtime-inspection.json |
| Ingestion, original bytes, citations, independent conflict review | Tested | 30 live acceptance checks |
| Reviewed memory conflict quarantine and bounded context | Implemented and unit tested | test_memory_projection.py; unit-tests-final.txt |
| Unsupported inference retains conversation | Implemented | api.py; workflow unit checks |
| Disconnect and role switch discard late responses | Browser tested | session-isolation.json |
| Restart persistence | Tested | persistence.json |
| Private backup restoration into isolated disposable DB | Tested; all 11 table fingerprints matched | recovery.json |
| Local repeatable check command | Updated for project venv and private local secrets | scripts/run-checks.ps1 |
| Testing separated from deployment | Available in UI and submission docs | assets/verification.json; docs/submission/TESTING_AND_EVIDENCE.md |
| Pacify-X and Remy selective integrations | Imported and tested; broader PX control plane uncommissioned | component-provenance.json; PX startup/Doctor evidence |
| Central security | Staged and disabled; activation denied | live acceptance; admin policy |
| Container OS advisories | Retained known findings; not production cleared | docs/CONTAINER_REVIEW.md |
| Hosted CI / public release | Deferred; inherited workflow is not hardened release approval | no hosted CI execution or publication |
| AMD / Evolus | Deferred by user | no activation or new implementation in this foundation pass |

Evidence describes specific tests, not a guarantee of defect-free behavior. This is a single-project
local demo with role tokens; production OIDC, TLS, tenant isolation, external audit anchoring,
OCR, embeddings, and arbitrary code execution are outside the accepted foundation scope.
