# NOETARIS source analysis and staged owner sharing

The live source inspector now connects the existing deterministic analysis API. It supports explicit value/group columns, count/sum/mean/min/max, header-row skips, declared units, exact worksheet selection including hidden sheets, source-bound coverage and decimal result strings. The table retains exact values; the bar chart explicitly uses approximate positions. Evidence includes source ID/revision/original hash, analysis hash, request and included/excluded locators. Calculations do not execute formulas, infer units or promote factual authority.

Changing inputs clears previous results and aborts the pending request. Component epochs also reject delayed responses after request-scope changes. Results must match the selected source, original hash, revision, full typed request, units, worksheet and internally consistent coverage/group denominators before rendering. Literal group labels never become HTML.

Owner sharing controls are implemented against the existing GET/POST /v1/sources/{id}/access API, but are available only to an admitted individual owner. The existing individual HTTP-content gate remains closed. Shared-role readers cannot load owner grants, infer a directory or mutate policy. No UI/SQL admission bypass was added to qualify the owner interface. Therefore the positive private-owner browser workflow remains UNQUALIFIED pending independent private-access admission; SQL-owner tests and request contracts do not substitute for that workflow.

The staged owner controls require a fresh owner snapshot and policy epoch, exact known user/group identifiers, and optional future expiry with explicit timezone. Expiry retains supplied microsecond precision. Revoke is bound to the displayed exact grant subject and current epoch. Uncertain or conflicting mutations clear the cached policy and require reload; the interface never optimistically declares access changed.

Current exact frontend image: sha256:91c527eec149f804f197b29744c5d49812751a146635b1682ee15782835c5285. Existing API remains sha256:2cb14915a827ee050fe7a2dd04d2d1c79a211891154501ed2e72c57a97299ec0. Both retained with hold tags. Existing backend packaged files remain byte-identical to the prior 1,327-passing-test baseline.

Fresh evidence:

- 16 frontend transport/source-control contract tests in the Docker build, evidence/noetaris-integration/docker-source-controls-build.log.
- 49 actual library/parser/API/PostgreSQL/Chromium checks, evidence/noetaris-integration/dca6d768cbb041ed81539f3e0941beac/receipt.json. Added exact CSV decimal/coverage/table/chart, literal labels, nonnumeric refusal, stale chart removal, XLSX formula-cache refusal, explicit hidden-sheet count and owner-control denials. A real analysis response was held across a unit edit; it could not repopulate old results, and a fresh request used the new explicit unit. The prior original-byte corruption fault injection remains separately declared; positive calculations use real backend responses.
- 41 focused backend sharing/calculation tests, evidence/implementation/noetaris-source-controls-backend.xml. Includes actual PostgreSQL owner binding, reader/admin delegation denial, CAS races, revocation, group-membership removal, expiry and audit-failure rollback. These are scoped backend checks, not positive private-owner HTTP/UI acceptance.
- 23 current Docker/auth checks, evidence/noetaris-integration/7271dd24ae7f4d6ba0b467468d62ccc9/receipt.json.
- 21 current HTTPS OAuth/resilience checks, evidence/oauth-browser-tls/ff657ae9ef834d5f99038878d4ac6de1/receipt.json. External provider boundaries remain simulated; no real provider activation is claimed.

Changed-file map: new components/SourceAnalysis.jsx, components/SourceSharing.jsx and services/sourceControls.js; LiveLibrary.jsx inspector integration and scripts/live-transport.test.js. Exact original/imported hash differences, all receipt hashes and current source fingerprints are retained in evidence/noetaris-integration/current-evidence.json and changed-imported-files.json. The original 44 supplied download files remain unchanged.

Rollback selects the retained prior frontend image. No database migration, source rewrite or deletion is required; analysis is read-only and sharing remains server-audited when legitimately admitted. Owned qualification resources were removed. Existing live services, protected data and original source bytes were untouched.

Remaining: positive owner-browser qualification after admission; filters/joins/multiple-source comparisons, line/scatter plots and exports; PDF.js and citation geometry, grounded chat, Atlas/memory, 14 placeholder routes, local-first voice and remaining full operational expansion. Build dependency risks, real provider/hardware/capacity checks and independent acceptance remain open. No whole-system certification is inferred.
