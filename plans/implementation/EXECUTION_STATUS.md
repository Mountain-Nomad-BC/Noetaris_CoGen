Current implementation evidence is tracked in [workspace progress](../../docs/implementation/RESEARCH_WORKSPACE_PROGRESS.md) and plan M. The system is not certified; the candidate counts and outcomes below are historical snapshots, not acceptance of the latest source.

# Execution status of all 89 punch cards

The full plan remains partially complete. Zero cards are ACCEPTED; independent criterion/dependency/release gates remain open. Original [backlog](backlog.json) and PLANNED tracker remain unchanged. [Criterion JSON](execution-status.json) retains301originalcriteria and explicit replacement engineering scope; [CSV](execution-status.csv) supports filtering.

## Current scoped outcome

Current 0df candidate:487 unit tests PASS (2knownwarnings),399 functions/180 observed entries/source-stable;31 owned fullstack PASS with immutable identity admission,50 owned PG/parser checks with MOCKmodel,57/57 unmounted src/assets byte matches. Recovery21 casesPASS includes actual previous 2ffe package-only compatibility plus current/pre-upgrade restores and cleanup. Historical100 starts/7194 proof does not qualify newer0df repeats. LIVE remains privacy-only2ffe at 4096. Exact0dfScout retains28 findings(1 HIGH,1 MEDIUM,26 LOW), SARIFexit2. CPU experiment remainsPARTIAL: strictcitation0/60 and6K8K180 second timeout. Zero cards accepted.

## Testing and evidence separate from deployment

[Upgrade/recovery21 cases](../../evidence/implementation/upgrade-recovery/README.md), [CPU experiment](../../evidence/implementation/cpu-context-benchmark/README.md), [database mechanism comparison](../../evidence/implementation/database-performance/README.md) and private indexed receipts preserve scopes, failures and source/artifact matches. [Privacy-only LIVE repair](../../evidence/live-evidence-privacy/7cdfd9d55ca4/result.json) changes no full-feature deployment. Passing source bytes/entries/testcases or immutable receipt admission is not release/security certification. Current 0dfsource and historical 7194 proof are kept distinct.

## Current fixes and withheld quality

Provider compression is refused before decode iteration, unsafe legacy generation is retired, duplicate/malformed role credentials fail closed, governed review avoids nested pool acquisition and retrieval reports conservative omissions. These are tested fixes; the former three static followups are no longer marked UNVALIDATED. Memory10 actual PG/API and retrieval8 actual PG/API cases pass narrow source/limit fixtures. OCR geometry4 pages/48 clean Aileron words passes minIoU0.94595 with0FP/FN; this does not broaden the200page synthetic calibration into general OCR quality. Critical negation/degraded tables/formulas remain withheld; other fonts/domain layouts/unsupported transforms/strict peak bounds remain open.

## Scope and disabled boundaries

Engineering issue translation supersedes actual transcript product work in069/070/071/076; original criteria remain archived with explicit replacement criteria. Graphs are review order, not verified causality or diagnosis. Central security/generated execution/AMD/Evolus/semantic indexing/external signing remain disabled;083-089 are DESIGN_ONLY. LIVE remains4096; candidate8192admission is not long-context quality/SLO qualification and16K/32K remain deferred. Model/source/dependency rights, exact archive/privacy and managed-profile dedicated Deep Scan remain independent gates. No canonical scan/report exists; do not weaken global permissions.

## Every card

### NSAI-001 - Bind verification to immutable run identities

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: none.

Implemented/tested: Shared immutable identity admission now binds current31-case0df stack to run/source/image/effective-config/producer/content/time with PASS_SCOPED and no release certification. Reviewed public summary stays separate; not every legacy producer is wired.

Next action: Complete all-producer/consumer identity coverage and independent final release acceptance; scoped sidecar admission is not certification.

- **PARTIAL** - Missing, failed, stale or mismatched source/image/config receipts cannot yield PASS Observed: Shared immutable identity admission now binds current31-case0df stack to run/source/image/effective-config/producer/content/time with PASS_SCOPED and no release certification. Reviewed public summary stays separate; not every legacy producer is wired. Remaining: Complete all-producer/consumer identity coverage and independent final release acceptance; scoped sidecar admission is not certification.
- **PARTIAL** - distinct static/runtime/quality/recovery verdicts remain visible Observed: Shared immutable identity admission now binds current31-case0df stack to run/source/image/effective-config/producer/content/time with PASS_SCOPED and no release certification. Reviewed public summary stays separate; not every legacy producer is wired. Remaining: Complete all-producer/consumer identity coverage and independent final release acceptance; scoped sidecar admission is not certification.

### NSAI-002 - Verify the complete effective deployment

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-001.

Implemented/tested: Current 0df candidate31-case owned stackPASS and57/57 unmounted image src/assets bytes match. Four actual LIVE containers pass selected runtime policy; LIVE remains privacy-only2ffe at 4096.

Next action: Qualify exact final intended deployment/runtime and review all image/policy/source gates; do not transfer current candidate proof to LIVE or old100-start proof to0df.

- **CONFIRMED** - Empty/missing services fail Observed: Current 0df candidate31-case owned stackPASS and57/57 unmounted image src/assets bytes match. Four actual LIVE containers pass selected runtime policy; LIVE remains privacy-only2ffe at 4096. Remaining: Qualify exact final intended deployment/runtime and review all image/policy/source gates; do not transfer current candidate proof to LIVE or old100-start proof to0df.
- **PARTIAL** - exact CPU service set, health, UID, capabilities, read-only mounts, secrets, resource limits and network policy verified Observed: Current 0df candidate31-case owned stackPASS and57/57 unmounted image src/assets bytes match. Four actual LIVE containers pass selected runtime policy; LIVE remains privacy-only2ffe at 4096. Remaining: Qualify exact final intended deployment/runtime and review all image/policy/source gates; do not transfer current candidate proof to LIVE or old100-start proof to0df.

### NSAI-003 - Isolate stateful acceptance and restore on every exit

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-001.

Implemented/tested: Owned stack/integration/recovery fixtures retain cleanup and no production DB selection. Recovery21 casesPASS includes three sequential tmpfs databases and both current/pre-upgrade restores.

Next action: Complete independent all-exit lifecycle audit and final-artifact acceptance; no concurrent application snapshot/PITR or live recovery qualification.

- **PARTIAL** - Failure at each mutation point restores owned test state in finally Observed: Owned stack/integration/recovery fixtures retain cleanup and no production DB selection. Recovery21 casesPASS includes three sequential tmpfs databases and both current/pre-upgrade restores. Remaining: Complete independent all-exit lifecycle audit and final-artifact acceptance; no concurrent application snapshot/PITR or live recovery qualification.
- **PARTIAL** - unrecovered state fails explicitly Observed: Owned stack/integration/recovery fixtures retain cleanup and no production DB selection. Recovery21 casesPASS includes three sequential tmpfs databases and both current/pre-upgrade restores. Remaining: Complete independent all-exit lifecycle audit and final-artifact acceptance; no concurrent application snapshot/PITR or live recovery qualification.
- **CONFIRMED** - live user corpus is never a fixture Observed: Owned stack/integration/recovery fixtures retain cleanup and no production DB selection. Recovery21 casesPASS includes three sequential tmpfs databases and both current/pre-upgrade restores. Remaining: Complete independent all-exit lifecycle audit and final-artifact acceptance; no concurrent application snapshot/PITR or live recovery qualification.

### NSAI-004 - Make startup and readiness observational

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-003, NSAI-002.

Implemented/tested: 100/100 owned starts passed with unchanged database and cleanup on historical 7194 fixture. That image became unavailable after retag;0df is a newer artifact and has31-case stack proof, not100 repeat proof.

Next action: Repeat100 starts/readiness on the exact intended final artifact or obtain independent explicit bounded proof-reuse acceptance; historical proof alone does not accept0df.

- **PARTIAL** - 100 repeated starts/readiness checks add no documents, claims, sessions or policy changes Observed: 100/100 owned starts passed with unchanged database and cleanup on historical 7194 fixture. That image became unavailable after retag;0df is a newer artifact and has31-case stack proof, not100 repeat proof. Remaining: Repeat100 starts/readiness on the exact intended final artifact or obtain independent explicit bounded proof-reuse acceptance; historical proof alone does not accept0df.
- **CONFIRMED** - acceptance data uses a disposable database Observed: 100/100 owned starts passed with unchanged database and cleanup on historical 7194 fixture. That image became unavailable after retag;0df is a newer artifact and has31-case stack proof, not100 repeat proof. Remaining: Repeat100 starts/readiness on the exact intended final artifact or obtain independent explicit bounded proof-reuse acceptance; historical proof alone does not accept0df.

### NSAI-005 - Consolidate supported local entrypoints

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-004.

Implemented/tested: Legacy Windows launchers redirect to CPU; obsolete shell launchers reject with retirement instructions.

Next action: Exercise each retained root/Windows launcher on clean owned volumes, then reconcile guides and selected OCR profile.

- **PARTIAL** - Every retained Windows/shell launcher performs parser, roles, migration and CPU readiness on clean volumes Observed: Legacy Windows launchers redirect to CPU; obsolete shell launchers reject with retirement instructions. Remaining: Exercise each retained root/Windows launcher on clean owned volumes, then reconcile guides and selected OCR profile.
- **CONFIRMED** - obsolete paths redirect or reject clearly Observed: Legacy Windows launchers redirect to CPU; obsolete shell launchers reject with retirement instructions. Remaining: Exercise each retained root/Windows launcher on clean owned volumes, then reconcile guides and selected OCR profile.

### NSAI-006 - Stage checks before journaled compatible migrations

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-003.

Implemented/tested: Owned21-case recovery upgrades populated original init/0002/0003 to current SQL preserving row hashes; exact current journal/idempotence, dirty/unknown refusal and failedDDL/data/journal rollback pass. Current and pre-upgrade backups restore exactly.

Next action: Qualify archived real deployed schema/data upgrade and complete previous HTTP/auth/UI/inference API behavior; actual previous 2ffe package read/ingest/original probe is narrower. No arbitrary legacy backfill/PITR/concurrent-write snapshot claim.

- **PARTIAL** - Build/check failure performs no schema mutation Observed: Owned21-case recovery upgrades populated original init/0002/0003 to current SQL preserving row hashes; exact current journal/idempotence, dirty/unknown refusal and failedDDL/data/journal rollback pass. Current and pre-upgrade backups restore exactly. Remaining: Qualify archived real deployed schema/data upgrade and complete previous HTTP/auth/UI/inference API behavior; actual previous 2ffe package read/ingest/original probe is narrower. No arbitrary legacy backfill/PITR/concurrent-write snapshot claim.
- **UNVERIFIED** - upgrade and compatible prior-image recovery pass on cloned data Observed: Owned21-case recovery upgrades populated original init/0002/0003 to current SQL preserving row hashes; exact current journal/idempotence, dirty/unknown refusal and failedDDL/data/journal rollback pass. Current and pre-upgrade backups restore exactly. Remaining: Qualify archived real deployed schema/data upgrade and complete previous HTTP/auth/UI/inference API behavior; actual previous 2ffe package read/ingest/original probe is narrower. No arbitrary legacy backfill/PITR/concurrent-write snapshot claim.
- **UNVERIFIED** - incompatible downgrade is denied with restore instructions Observed: Owned21-case recovery upgrades populated original init/0002/0003 to current SQL preserving row hashes; exact current journal/idempotence, dirty/unknown refusal and failedDDL/data/journal rollback pass. Current and pre-upgrade backups restore exactly. Remaining: Qualify archived real deployed schema/data upgrade and complete previous HTTP/auth/UI/inference API behavior; actual previous 2ffe package read/ingest/original probe is narrower. No arbitrary legacy backfill/PITR/concurrent-write snapshot claim.

### NSAI-007 - Converge database privileges and rotate credentials

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-006.

Implemented/tested: Convergent role SQL removes seeded excess memberships/attributes and historic grants; owned stack verifies convergence.

Next action: Test every immutable table UPDATE/DELETE and explicit owner/app credential rotation during concurrent calls without secret logs.

- **CONFIRMED** - Seed excess grants/memberships/attributes and prove removal Observed: Convergent role SQL removes seeded excess memberships/attributes and historic grants; owned stack verifies convergence. Remaining: Test every immutable table UPDATE/DELETE and explicit owner/app credential rotation during concurrent calls without secret logs.
- **PARTIAL** - immutable tables cannot be updated/deleted Observed: Convergent role SQL removes seeded excess memberships/attributes and historic grants; owned stack verifies convergence. Remaining: Test every immutable table UPDATE/DELETE and explicit owner/app credential rotation during concurrent calls without secret logs.
- **PARTIAL** - explicit rotation preserves availability without logging secrets Observed: Convergent role SQL removes seeded excess memberships/attributes and historic grants; owned stack verifies convergence. Remaining: Test every immutable table UPDATE/DELETE and explicit owner/app credential rotation during concurrent calls without secret logs.

### NSAI-008 - Protect private state with Windows ACLs

Status: **PARTIALLY_IMPLEMENTED**; accepted:false. Unaccepted dependencies: NSAI-005.

Implemented/tested: Startup applies and reads back owner, protected-DACL, exact principal and FullControl policy for each existing private target and child. An owned Windows fixture verifies removal of explicit Everyone ACEs, child inheritance and restricted-token read denial. Receipt: `evidence/implementation/windows-acl-owned-fixture-20261017-rt36.json`.

Next action: Obtain independent reproduction and a separately provisioned low-privilege account check; qualify effective access on authorized application paths without exposing real secrets.

- **CONFIRMED** - Intended account and SYSTEM access only Observed: Owned Windows fixture verified only current account and SYSTEM allowed on the synthetic private root, existing child directory and file, plus new descendants. Remaining: Independent reproduction and authorized application-path review before card acceptance.
- **CONFIRMED** - existing/inherited grants and children checked Observed: Fixture began with explicit Everyone access; protection removed it, verified protected DACLs on existing objects, and new descendants inherited only the expected principals. Remaining: Independent reproduction and authorized application-path review before card acceptance.
- **UNVERIFIED** - hostile account read fails Observed: Restricted Windows token was denied reading the synthetic protected file; a separately provisioned real account was not tested. Remaining: Test using an independently provisioned low-privilege account and obtain independent reproduction.
- **CONFIRMED** - startup checks actual DACL rather than chmod Observed: Startup protection helper reads back owner, DACL protection, principals, access type and FullControl after `Set-Acl`; the owned probe passed against the exact helper hash. Remaining: Independent review and separate-account negative test before card acceptance.

### NSAI-009 - Write bounded exclusive recoverable backups

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-008, NSAI-006.

Implemented/tested: Final487-test snapshot includes exclusive/fsynced atomic backup-manifest failure/concurrency cases. Actual21-case recovery validates size/SHA manifests and restores current plus pre-upgrade backups with rows/sequences/indexes/triggers/ACL/role comparison.

Next action: Qualify maximum-size/time and actual disk/power interruption plus concurrent application snapshot consistency on final release; owned small quiescent fixtures do not accept all backup criteria.

- **CONFIRMED** - Same-second/concurrent dumps never overwrite Observed: Final487-test snapshot includes exclusive/fsynced atomic backup-manifest failure/concurrency cases. Actual21-case recovery validates size/SHA manifests and restores current plus pre-upgrade backups with rows/sequences/indexes/triggers/ACL/role comparison. Remaining: Qualify maximum-size/time and actual disk/power interruption plus concurrent application snapshot consistency on final release; owned small quiescent fixtures do not accept all backup criteria.
- **CONFIRMED** - streaming size/time/disk bounds enforced Observed: Final487-test snapshot includes exclusive/fsynced atomic backup-manifest failure/concurrency cases. Actual21-case recovery validates size/SHA manifests and restores current plus pre-upgrade backups with rows/sequences/indexes/triggers/ACL/role comparison. Remaining: Qualify maximum-size/time and actual disk/power interruption plus concurrent application snapshot consistency on final release; owned small quiescent fixtures do not accept all backup criteria.
- **PARTIAL** - protected temporary output atomically finalized with SHA256 manifest Observed: Final487-test snapshot includes exclusive/fsynced atomic backup-manifest failure/concurrency cases. Actual21-case recovery validates size/SHA manifests and restores current plus pre-upgrade backups with rows/sequences/indexes/triggers/ACL/role comparison. Remaining: Qualify maximum-size/time and actual disk/power interruption plus concurrent application snapshot consistency on final release; owned small quiescent fixtures do not accept all backup criteria.
- **CONFIRMED** - failed dumps never marked successful Observed: Final487-test snapshot includes exclusive/fsynced atomic backup-manifest failure/concurrency cases. Actual21-case recovery validates size/SHA manifests and restores current plus pre-upgrade backups with rows/sequences/indexes/triggers/ACL/role comparison. Remaining: Qualify maximum-size/time and actual disk/power interruption plus concurrent application snapshot consistency on final release; owned small quiescent fixtures do not accept all backup criteria.

### NSAI-010 - Validate credentials and secure every error response

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-003.

Implemented/tested: Current principal validates the entire configured role credential set before matching, rejects duplicate values and malformed later files with503. Current31-case real HTTP roles/denials and487-unit snapshot pass.

Next action: Finish production identity/TLS/expiry/step-up commissioning only under separate scope; independent local-auth acceptance remains open.

- **CONFIRMED** - Non-ASCII, oversized, malformed and absent bearer credentials return controlled 401/403 with required security headers Observed: Current principal validates the entire configured role credential set before matching, rejects duplicate values and malformed later files with503. Current31-case real HTTP roles/denials and487-unit snapshot pass. Remaining: Finish production identity/TLS/expiry/step-up commissioning only under separate scope; independent local-auth acceptance remains open.
- **CONFIRMED** - constant-time comparison retained Observed: Current principal validates the entire configured role credential set before matching, rejects duplicate values and malformed later files with503. Current31-case real HTTP roles/denials and487-unit snapshot pass. Remaining: Finish production identity/TLS/expiry/step-up commissioning only under separate scope; independent local-auth acceptance remains open.

### NSAI-011 - Clear all private browser state on identity changes

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-010.

Implemented/tested: Identity changes clear six drafts/files/private renders/PDF resources; epochs suppress stale replies; Chromium logout passes.

Next action: Stress actual-server delayed model/source replies during repeated identity changes and verify no buffer/worker residue.

- **CONFIRMED** - All six observed draft fields, file selections, rendered private content and object URLs clear Observed: Identity changes clear six drafts/files/private renders/PDF resources; epochs suppress stale replies; Chromium logout passes. Remaining: Stress actual-server delayed model/source replies during repeated identity changes and verify no buffer/worker residue.
- **CONFIRMED** - pending old-epoch responses cannot repopulate state Observed: Identity changes clear six drafts/files/private renders/PDF resources; epochs suppress stale replies; Chromium logout passes. Remaining: Stress actual-server delayed model/source replies during repeated identity changes and verify no buffer/worker residue.

### NSAI-012 - Handle malformed provider and secret failures

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-010.

Implemented/tested: Current bounded provider transport requests identity encoding and rejects nonidentity Content-Encoding before body iteration; length/deadline/JSON guards are tested. Model-status regressions cover invalid inventories and missing credentials. Completion regressions cover array/null/empty/null-member envelopes and confirm API translation returns generic HTTP 503. Token admission rejects malformed properties, templates, and token IDs as typed ValueErrors before generation.

Next action: Extend I/O/deadline/cancellation coverage across all provider adapters; obtain independent final artifact review.

- **PARTIAL** - JSON list/null/invalid envelopes, missing secret, I/O error, timeout and cancellation return bounded typed failures without accidental 500 or secret disclosure Observed: Bounded transport tests encoded/oversized responses, deadlines, I/O stream closure, cancellation, and strict JSON; invalid model inventory/completion envelopes return generic errors and missing credentials do not expose paths. Malformed tokenizer properties/templates/token IDs are rejected before generation. API timeout tests confirm generic 502 responses and durable failed invocation/inference records at both admission and completion stages, without provider-message disclosure. Remaining: Qualify I/O/deadline/cancellation across every adapter; obtain independent final artifact review.

### NSAI-013 - Bound PDF decoding before allocation

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-003.

Implemented/tested: Parser tests reject a 9 MiB Flate expansion, repeated content-array expansion, and a compressed object stream expanding to 9 MiB from under 10 KiB input; a Python-traced peak-allocation assertion stays below 24 MiB. Unsupported filters/predictors, malformed Boolean/name/array DecodeParms, malformed page Resources/XObjects, and Boolean `/Contents` reject as controlled errors. Parser-service tests verify malformed content/resource requests return 422 and the next valid PDF returns 200.

Next action: Expand remaining malformed-object cases and measure process RSS/allocation in the isolated final image; qualify parser-service/process recovery on the final image.

- **PARTIAL** - False-valued ContentStream, compressed arrays/object streams, huge expansion and malformed objects reject before excessive allocation Observed: Tests reject 9 MiB Flate/object-stream expansion, repeated content-array expansion, malformed DecodeParms and page resources, unsupported filters/predictors, and Boolean `/Contents`; traced peak remains below 24 MiB. Remaining: Expand malformed-object corpus; measure process RSS in and qualify the final image.
- **CONFIRMED** - parser recovers for next valid job Observed: Malformed `/Contents` and Resources requests return 422 and a following valid compressed-PDF request returns 200 through the parser service; decoder restoration is tested after direct decode/resource rejection. Remaining: Qualify final-image parser service/process recovery; this local test is not deployment evidence.

### NSAI-014 - Record every PDF page and its completeness

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-013, NSAI-006.

Implemented/tested: Every page has status/completeness; mixed raster omissions remain visible and incomplete model reasoning is withheld.

Next action: Qualify native/blank/form/mixed/failed/unsupported classes and final answer/citation completeness under partial OCR failure.

- **CONFIRMED** - Mixed native/raster fixture accounts for all pages as native/blank/OCR-required/failed/unsupported Observed: Every page has status/completeness; mixed raster omissions remain visible and incomplete model reasoning is withheld. Remaining: Qualify native/blank/form/mixed/failed/unsupported classes and final answer/citation completeness under partial OCR failure.
- **CONFIRMED** - omitted pages never imply complete evidence Observed: Every page has status/completeness; mixed raster omissions remain visible and incomplete model reasoning is withheld. Remaining: Qualify native/blank/form/mixed/failed/unsupported classes and final answer/citation completeness under partial OCR failure.

### NSAI-015 - Make inference terminal transitions idempotent

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-006, NSAI-003.

Implemented/tested: Clean owned PostgreSQL qualification verified concurrent finish idempotency, stale-owner denial, failed/expired attempt charging, and durable expiry audit. Migration 0040 prevents >300-second abandoned rows from consuming global inference slots.

Next action: Qualify cancellation/process-death behavior on the final image; document owner-scoped reconciliation and the 300-second global-slot lease.

- **CONFIRMED** - Concurrent finish/retry yields one terminal transition and one settlement event Observed: Two simultaneous finishes returned the same terminal receipt and wrote exactly one `inference.completed` audit event in owned PostgreSQL. Remaining: Qualify final image and process-death/cancellation paths.
- **CONFIRMED** - stale actors denied Observed: A second principal could not finish the first user's run; RLS returned not-found. Remaining: Qualify against the final packaged image.
- **CONFIRMED** - failed attempts charged Observed: Failed and expired rows remained in the per-user daily attempt count. Remaining: Confirm final-image budget behavior.
- **CONFIRMED** - abandoned reservations reconciled durably Observed: An expired run became failed with one `inference.abandoned` audit event; repeat reconciliation was idempotent. A foreign expired row did not block a new user after migration 0040. Remaining: Qualify actual process death/final image.

### NSAI-016 - Admit the complete prompt using the actual tokenizer

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-012, NSAI-015.

Implemented/tested: Actual CPU8K admission receipts pass6/7guardcases, including a complete prompt above4096 and within8192 withoutgeneration and oversizedrefusal; two shortgeneration smokes remainunverifieddrafts. CandidateCompose nowtargets8192; liveapp remains4096 untildeployment.

Next action: Qualify matched long-context answer/support/refusal/latency/RSS and policy/omission races, then freshlyintegrate the8192candidateimage beforedeployment. No longpromptgeneration/qualitySLO claim;16K/32K requirelaterhardware/model proofs.

- **CONFIRMED** - System/schema/question/history/evidence plus reserved output fit model context Observed: Actual CPU8K admission receipts pass6/7guardcases, including a complete prompt above4096 and within8192 withoutgeneration and oversizedrefusal; two shortgeneration smokes remainunverifieddrafts. CandidateCompose nowtargets8192; liveapp remains4096 untildeployment. Remaining: Qualify matched long-context answer/support/refusal/latency/RSS and policy/omission races, then freshlyintegrate the8192candidateimage beforedeployment. No longpromptgeneration/qualitySLO claim;16K/32K requirelaterhardware/model proofs.
- **CONFIRMED** - 4,632-token adversarial fixture is refused or explicitly reduced before reservation Observed: Actual CPU8K admission receipts pass6/7guardcases, including a complete prompt above4096 and within8192 withoutgeneration and oversizedrefusal; two shortgeneration smokes remainunverifieddrafts. CandidateCompose nowtargets8192; liveapp remains4096 untildeployment. Remaining: Qualify matched long-context answer/support/refusal/latency/RSS and policy/omission races, then freshlyintegrate the8192candidateimage beforedeployment. No longpromptgeneration/qualitySLO claim;16K/32K requirelaterhardware/model proofs.
- **PARTIAL** - omissions observable Observed: Actual CPU8K admission receipts pass6/7guardcases, including a complete prompt above4096 and within8192 withoutgeneration and oversizedrefusal; two shortgeneration smokes remainunverifieddrafts. CandidateCompose nowtargets8192; liveapp remains4096 untildeployment. Remaining: Qualify matched long-context answer/support/refusal/latency/RSS and policy/omission races, then freshlyintegrate the8192candidateimage beforedeployment. No longpromptgeneration/qualitySLO claim;16K/32K requirelaterhardware/model proofs.

### NSAI-017 - Discover conflicts beyond retrieved top-k

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-006.

Implemented/tested: Active conflicts expand beyond top-k inside selected documents; disputed canon is quarantined and history retained.

Next action: Test legacy oversized-corpus admission, all page/revision scopes, equivalent values and concurrent review/reparse invalidation.

- **PARTIAL** - Authorized active alternatives outside rank limits still conflict Observed: Active conflicts expand beyond top-k inside selected documents; disputed canon is quarantined and history retained. Remaining: Test legacy oversized-corpus admission, all page/revision scopes, equivalent values and concurrent review/reparse invalidation.
- **PARTIAL** - quarantined/disputed values cannot become answer facts Observed: Active conflicts expand beyond top-k inside selected documents; disputed canon is quarantined and history retained. Remaining: Test legacy oversized-corpus admission, all page/revision scopes, equivalent values and concurrent review/reparse invalidation.
- **PARTIAL** - revision/history retained Observed: Active conflicts expand beyond top-k inside selected documents; disputed canon is quarantined and history retained. Remaining: Test legacy oversized-corpus admission, all page/revision scopes, equivalent values and concurrent review/reparse invalidation.

### NSAI-018 - Align Unicode and serialized transport budgets

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-013.

Implemented/tested: UTF-8 parser output and explicit transport budgets replace ASCII escaping mismatch; Unicode custody unit fixtures exist.

Next action: Exercise150000 supplementary codepoints through actual upload/parser/API and measure buffering at accepted/rejected boundaries.

- **PARTIAL** - 150,000 supplementary-codepoint fixture has a deliberate supported/rejected result consistent with UTF-8 transport and child/API limits Observed: UTF-8 parser output and explicit transport budgets replace ASCII escaping mismatch; Unicode custody unit fixtures exist. Remaining: Exercise150000 supplementary codepoints through actual upload/parser/API and measure buffering at accepted/rejected boundaries.
- **PARTIAL** - no oversized buffered response Observed: UTF-8 parser output and explicit transport budgets replace ASCII escaping mismatch; Unicode custody unit fixtures exist. Remaining: Exercise150000 supplementary codepoints through actual upload/parser/API and measure buffering at accepted/rejected boundaries.

### NSAI-019 - Replace UI presence checks with observed outcomes

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-011, NSAI-001.

Implemented/tested: Chromium tests observe completed flows; owned stack verifies real upload/PDF/scopedQA/review/engineering/logout.

Next action: Retain full failed attempts and qualify complete real workflow evidence identity plus accessibility independently.

- **PARTIAL** - Wait on state/results rather than fixed sleeps Observed: Chromium tests observe completed flows; owned stack verifies real upload/PDF/scopedQA/review/engineering/logout. Remaining: Retain full failed attempts and qualify complete real workflow evidence identity plus accessibility independently.
- **PARTIAL** - role ingestion/review/answer/logout flows prove source binding and completed actions Observed: Chromium tests observe completed flows; owned stack verifies real upload/PDF/scopedQA/review/engineering/logout. Remaining: Retain full failed attempts and qualify complete real workflow evidence identity plus accessibility independently.
- **PARTIAL** - receipts include run/time/source/image identities Observed: Chromium tests observe completed flows; owned stack verifies real upload/PDF/scopedQA/review/engineering/logout. Remaining: Retain full failed attempts and qualify complete real workflow evidence identity plus accessibility independently.

### NSAI-020 - Verify model identity, licensing and endpoint configuration

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-012.

Implemented/tested: Model inspection mandates exact SHA256, pre-resolve symlink checks and actual GGUF metadata; current license is unreviewed qwen-research.

Next action: Review artifact-specific license and alternate-port behavior; digest PASS authorizes neither redistribution nor source publication.

- **PARTIAL** - Mandatory digest and explicit metadata/license match actual GGUF Observed: Model inspection mandates exact SHA256, pre-resolve symlink checks and actual GGUF metadata; current license is unreviewed qwen-research. Remaining: Review artifact-specific license and alternate-port behavior; digest PASS authorizes neither redistribution nor source publication.
- **PARTIAL** - symlink policy checked before resolve Observed: Model inspection mandates exact SHA256, pre-resolve symlink checks and actual GGUF metadata; current license is unreviewed qwen-research. Remaining: Review artifact-specific license and alternate-port behavior; digest PASS authorizes neither redistribution nor source publication.
- **PARTIAL** - alternate configured port works throughout Observed: Model inspection mandates exact SHA256, pre-resolve symlink checks and actual GGUF metadata; current license is unreviewed qwen-research. Remaining: Review artifact-specific license and alternate-port behavior; digest PASS authorizes neither redistribution nor source publication.
- **PARTIAL** - arbitrary GGUF not mislabeled Qwen Observed: Model inspection mandates exact SHA256, pre-resolve symlink checks and actual GGUF metadata; current license is unreviewed qwen-research. Remaining: Review artifact-specific license and alternate-port behavior; digest PASS authorizes neither redistribution nor source publication.

### NSAI-021 - Make container package resolution reproducible

Status: **PARTIALLY_IMPLEMENTED**; accepted:false. Unaccepted dependencies: NSAI-002.

Implemented/tested: Exact0df OCI candidate has fresh Scout SPDXexit0 and SARIFexit2:28 findings(1 HIGH,1 MEDIUM,26 LOW), all retained. DB exact package closure and toolchain hash closures/install proof remain separate.

Next action: Disposition exact0df HIGH CVE-2026-85091 zlib/MEDIUM CVE-2025-45582 tar and other findings; no suppression or exploitability inference. Complete independent reproducibility/license review.

- **PARTIAL** - Base digest and installed OS package closure recorded/pinned or snapshot-controlled Observed: Exact0df OCI candidate has fresh Scout SPDXexit0 and SARIFexit2:28 findings(1 HIGH,1 MEDIUM,26 LOW), all retained. DB exact package closure and toolchain hash closures/install proof remain separate. Remaining: Disposition exact0df HIGH CVE-2026-85091 zlib/MEDIUM CVE-2025-45582 tar and other findings; no suppression or exploitability inference. Complete independent reproducibility/license review.
- **PARTIAL** - two matched builds explain any drift Observed: Exact0df OCI candidate has fresh Scout SPDXexit0 and SARIFexit2:28 findings(1 HIGH,1 MEDIUM,26 LOW), all retained. DB exact package closure and toolchain hash closures/install proof remain separate. Remaining: Disposition exact0df HIGH CVE-2026-85091 zlib/MEDIUM CVE-2025-45582 tar and other findings; no suppression or exploitability inference. Complete independent reproducibility/license review.
- **PARTIAL** - SBOM and current CVE dispositions retained Observed: Exact0df OCI candidate has fresh Scout SPDXexit0 and SARIFexit2:28 findings(1 HIGH,1 MEDIUM,26 LOW), all retained. DB exact package closure and toolchain hash closures/install proof remain separate. Remaining: Disposition exact0df HIGH CVE-2026-85091 zlib/MEDIUM CVE-2025-45582 tar and other findings; no suppression or exploitability inference. Complete independent reproducibility/license review.

### NSAI-022 - Lock runtime, build, test and CI dependencies

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-021.

Implemented/tested: Exact build/dev transitive hash locks, pinned backends and official action SHAs passed isolated Windows install/build/pipcheck.

Next action: Run commissioned Linux3.12/host CI matrix, disposition test-client deprecations and document OS/interpreter/build determinism limits.

- **PARTIAL** - Runtime Python 3.12 checks plus declared host compatibility pass Observed: Exact build/dev transitive hash locks, pinned backends and official action SHAs passed isolated Windows install/build/pipcheck. Remaining: Run commissioned Linux3.12/host CI matrix, disposition test-client deprecations and document OS/interpreter/build determinism limits.
- **CONFIRMED** - build/test hashes locked Observed: Exact build/dev transitive hash locks, pinned backends and official action SHAs passed isolated Windows install/build/pipcheck. Remaining: Run commissioned Linux3.12/host CI matrix, disposition test-client deprecations and document OS/interpreter/build determinism limits.
- **PARTIAL** - commissioned CI uses lock and pinned action SHAs Observed: Exact build/dev transitive hash locks, pinned backends and official action SHAs passed isolated Windows install/build/pipcheck. Remaining: Run commissioned Linux3.12/host CI matrix, disposition test-client deprecations and document OS/interpreter/build determinism limits.
- **PARTIAL** - deprecations have explicit disposition Observed: Exact build/dev transitive hash locks, pinned backends and official action SHAs passed isolated Windows install/build/pipcheck. Remaining: Run commissioned Linux3.12/host CI matrix, disposition test-client deprecations and document OS/interpreter/build determinism limits.

### NSAI-023 - Validate Docker's effective profile-aware configuration

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-002.

Implemented/tested: CPU effective Docker JSON rejects missing/unknown active services and tests private confinement.

Next action: Expand adversarial mounts/ports/egress and OCR-selected profile checks; deferred providers must remain outside supported startup.

- **PARTIAL** - Effective CPU JSON rejects unknown services, added mounts/ports/egress or missing limits Observed: CPU effective Docker JSON rejects missing/unknown active services and tests private confinement. Remaining: Expand adversarial mounts/ports/egress and OCR-selected profile checks; deferred providers must remain outside supported startup.
- **PARTIAL** - deferred profiles not mistaken for commissioned CPU services Observed: CPU effective Docker JSON rejects missing/unknown active services and tests private confinement. Remaining: Expand adversarial mounts/ports/egress and OCR-selected profile checks; deferred providers must remain outside supported startup.

### NSAI-024 - Remove import-time script mutations and bound subprocesses

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-005.

Implemented/tested: Operational helpers use explicit main entrypoints, bounded backup reader and command deadlines/failure receipts.

Next action: Inventory every remaining script/subprocess for import purity, cancellation, cleanup and strict fingerprint/dump disk limits.

- **PARTIAL** - Importing helpers has no host/service mutation Observed: Operational helpers use explicit main entrypoints, bounded backup reader and command deadlines/failure receipts. Remaining: Inventory every remaining script/subprocess for import purity, cancellation, cleanup and strict fingerprint/dump disk limits.
- **PARTIAL** - explicit main entrypoints Observed: Operational helpers use explicit main entrypoints, bounded backup reader and command deadlines/failure receipts. Remaining: Inventory every remaining script/subprocess for import purity, cancellation, cleanup and strict fingerprint/dump disk limits.
- **PARTIAL** - deadlines/cancellation/cleanup and typed receipts for every subprocess Observed: Operational helpers use explicit main entrypoints, bounded backup reader and command deadlines/failure receipts. Remaining: Inventory every remaining script/subprocess for import purity, cancellation, cleanup and strict fingerprint/dump disk limits.

### NSAI-025 - Qualify recovery from independently verified backups

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-009, NSAI-007, NSAI-024.

Implemented/tested: Recovery21 casesPASS verifies actual current-schema restore to a second DB and pre-upgrade backup restore to a third DB, exact logical rows/sequences/indexes/triggers/canonical ACL/role policy and historical journal.

Next action: Qualify real archived deployment recovery, concurrent-write consistency/PITR and complete old HTTP API behavior; small synthetic quiescent proof and package-only2ffe compatibility are limited.

- **CONFIRMED** - Restore schema, roles, grants, indexes, triggers and data with bounded SHA256 verification Observed: Recovery21 casesPASS verifies actual current-schema restore to a second DB and pre-upgrade backup restore to a third DB, exact logical rows/sequences/indexes/triggers/canonical ACL/role policy and historical journal. Remaining: Qualify real archived deployment recovery, concurrent-write consistency/PITR and complete old HTTP API behavior; small synthetic quiescent proof and package-only2ffe compatibility are limited.
- **UNVERIFIED** - concurrent-write snapshot semantics documented Observed: Recovery21 casesPASS verifies actual current-schema restore to a second DB and pre-upgrade backup restore to a third DB, exact logical rows/sequences/indexes/triggers/canonical ACL/role policy and historical journal. Remaining: Qualify real archived deployment recovery, concurrent-write consistency/PITR and complete old HTTP API behavior; small synthetic quiescent proof and package-only2ffe compatibility are limited.
- **UNVERIFIED** - interrupted restore recovers Observed: Recovery21 casesPASS verifies actual current-schema restore to a second DB and pre-upgrade backup restore to a third DB, exact logical rows/sequences/indexes/triggers/canonical ACL/role policy and historical journal. Remaining: Qualify real archived deployment recovery, concurrent-write consistency/PITR and complete old HTTP API behavior; small synthetic quiescent proof and package-only2ffe compatibility are limited.
- **CONFIRMED** - PITR remains explicitly unqualified unless separately implemented Observed: Recovery21 casesPASS verifies actual current-schema restore to a second DB and pre-upgrade backup restore to a third DB, exact logical rows/sequences/indexes/triggers/canonical ACL/role policy and historical journal. Remaining: Qualify real archived deployment recovery, concurrent-write consistency/PITR and complete old HTTP API behavior; small synthetic quiescent proof and package-only2ffe compatibility are limited.

### NSAI-026 - Enforce database structural invariants

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-006, NSAI-007.

Implemented/tested: Typed central-false/hash/uniqueness/span-chunk/reviewer constraints reject bad owned rows.

Next action: Run exhaustive app-role constraint/table negatives and publish the trusted-application semantic-forgery boundary.

- **PARTIAL** - Central-disabled invariant, hash lengths/uniqueness, span-chunk relationships and nonempty reviewer constrained Observed: Typed central-false/hash/uniqueness/span-chunk/reviewer constraints reject bad owned rows. Remaining: Run exhaustive app-role constraint/table negatives and publish the trusted-application semantic-forgery boundary.
- **PARTIAL** - seeded bad rows fail Observed: Typed central-false/hash/uniqueness/span-chunk/reviewer constraints reject bad owned rows. Remaining: Run exhaustive app-role constraint/table negatives and publish the trusted-application semantic-forgery boundary.
- **PARTIAL** - trusted application semantic-forgery boundary documented Observed: Typed central-false/hash/uniqueness/span-chunk/reviewer constraints reject bad owned rows. Remaining: Run exhaustive app-role constraint/table negatives and publish the trusted-application semantic-forgery boundary.

### NSAI-027 - Bound pre-auth traffic and enforce fair admission

Status: **PARTIALLY_IMPLEMENTED**; accepted:false. Unaccepted dependencies: NSAI-010, NSAI-015.

Implemented/tested: Bounded ASCII secrets, pre-buffer authentication/body deadlines and per-role principal fairness120requests/minute each with global480 are implemented.

Next action: Qualify hostile slow bodies, each-role fairness/global capacity and sustained concurrent actualHTTP on final image; single-process/shared-role scope remains explicit.

- **PARTIAL** - Unauthenticated streaming body bounded before buffering Observed: Bounded ASCII secrets, pre-buffer authentication/body deadlines and per-role principal fairness120requests/minute each with global480 are implemented. Remaining: Qualify hostile slow bodies, each-role fairness/global capacity and sustained concurrent actualHTTP on final image; single-process/shared-role scope remains explicit.
- **PARTIAL** - total deadline and principal fairness tested Observed: Bounded ASCII secrets, pre-buffer authentication/body deadlines and per-role principal fairness120requests/minute each with global480 are implemented. Remaining: Qualify hostile slow bodies, each-role fairness/global capacity and sustained concurrent actualHTTP on final image; single-process/shared-role scope remains explicit.
- **PARTIAL** - one-process scope honest Observed: Bounded ASCII secrets, pre-buffer authentication/body deadlines and per-role principal fairness120requests/minute each with global480 are implemented. Remaining: Qualify hostile slow bodies, each-role fairness/global capacity and sustained concurrent actualHTTP on final image; single-process/shared-role scope remains explicit.
- **PARTIAL** - no unauthenticated request exhausts all authenticated capacity Observed: Bounded ASCII secrets, pre-buffer authentication/body deadlines and per-role principal fairness120requests/minute each with global480 are implemented. Remaining: Qualify hostile slow bodies, each-role fairness/global capacity and sustained concurrent actualHTTP on final image; single-process/shared-role scope remains explicit.

### NSAI-028 - Unify approved model/parser HTTP transport

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-012, NSAI-018.

Implemented/tested: Compression refused before decoded-body iteration; retired legacy generator cannot call buffered transport. Current31-case HTTP/browser stack and487-unit snapshot cover selected transport/error boundaries.

Next action: Qualify full network/provider/TLS/large-body/cancellation matrix on intended release; no broad network security clearance.

- **PARTIAL** - Approved hosts, TLS policy, no redirects, explicit proxy policy, bounded response and deadlines enforced consistently Observed: Compression refused before decoded-body iteration; retired legacy generator cannot call buffered transport. Current31-case HTTP/browser stack and487-unit snapshot cover selected transport/error boundaries. Remaining: Qualify full network/provider/TLS/large-body/cancellation matrix on intended release; no broad network security clearance.
- **PARTIAL** - environment proxy cannot reroute private traffic Observed: Compression refused before decoded-body iteration; retired legacy generator cannot call buffered transport. Current31-case HTTP/browser stack and487-unit snapshot cover selected transport/error boundaries. Remaining: Qualify full network/provider/TLS/large-body/cancellation matrix on intended release; no broad network security clearance.

### NSAI-029 - Verify parser output independently

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-014, NSAI-018.

Implemented/tested: Parser verifies hashes/statuses/TXT original lines and complete span/map/chunk coverage; forged span regressions pass.

Next action: Test real malicious-worker envelopes, finite/depth bounds and stage identity; confined PDF extraction is a trust boundary, not SHA proof.

- **PARTIAL** - API checks original digest, response schema, finite bounds and stage receipt before acceptance Observed: Parser verifies hashes/statuses/TXT original lines and complete span/map/chunk coverage; forged span regressions pass. Remaining: Test real malicious-worker envelopes, finite/depth bounds and stage identity; confined PDF extraction is a trust boundary, not SHA proof.
- **CONFIRMED** - forged worker metadata and inconsistent spans rejected Observed: Parser verifies hashes/statuses/TXT original lines and complete span/map/chunk coverage; forged span regressions pass. Remaining: Test real malicious-worker envelopes, finite/depth bounds and stage identity; confined PDF extraction is a trust boundary, not SHA proof.

### NSAI-030 - Redact logs and verification metadata

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-010, NSAI-001.

Implemented/tested: Privacy-only live repairPASS deployed APIimage2ffe38c418aa; all tested static GET/HEAD aliases404 and authenticated sanitizedsummary200. Documents20/audit126head/policy/roles/nonAPIidentities preserved, livecontext4096 unchanged. Candidate PublicAssets whitelist and OCR metadata guards independently tested40PASS.

Next action: Qualify final full-feature artifact separately and complete source/query/secret log canary matrix; rollback prepared but not exercised.

- **PARTIAL** - Synthetic secret/source/query payloads absent from normal access/error logs and public verification Observed: Privacy-only live repairPASS deployed APIimage2ffe38c418aa; all tested static GET/HEAD aliases404 and authenticated sanitizedsummary200. Documents20/audit126head/policy/roles/nonAPIidentities preserved, livecontext4096 unchanged. Candidate PublicAssets whitelist and OCR metadata guards independently tested40PASS. Remaining: Qualify final full-feature artifact separately and complete source/query/secret log canary matrix; rollback prepared but not exercised.
- **PARTIAL** - allowlisted metadata only Observed: Privacy-only live repairPASS deployed APIimage2ffe38c418aa; all tested static GET/HEAD aliases404 and authenticated sanitizedsummary200. Documents20/audit126head/policy/roles/nonAPIidentities preserved, livecontext4096 unchanged. Candidate PublicAssets whitelist and OCR metadata guards independently tested40PASS. Remaining: Qualify final full-feature artifact separately and complete source/query/secret log canary matrix; rollback prepared but not exercised.
- **PARTIAL** - private diagnostic export explicitly distinguished Observed: Privacy-only live repairPASS deployed APIimage2ffe38c418aa; all tested static GET/HEAD aliases404 and authenticated sanitizedsummary200. Documents20/audit126head/policy/roles/nonAPIidentities preserved, livecontext4096 unchanged. Candidate PublicAssets whitelist and OCR metadata guards independently tested40PASS. Remaining: Qualify final full-feature artifact separately and complete source/query/secret log canary matrix; rollback prepared but not exercised.

### NSAI-031 - Resolve existing imported source and compatibility

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-029.

Implemented/tested: Original runtime contracts replace imports; import tools are retired; provenance denies comprehensive IP/publication clearance.

Next action: Review exact source/license manifest and historical hash/span compatibility on cloned records before explicit source-origin disposition or archive.

- **PARTIAL** - Independent replacement specification and implementation Observed: Original runtime contracts replace imports; import tools are retired; provenance denies comprehensive IP/publication clearance. Remaining: Review exact source/license manifest and historical hash/span compatibility on cloned records before explicit source-origin disposition or archive.
- **PARTIAL** - old hash/span records remain readable Observed: Original runtime contracts replace imports; import tools are retired; provenance denies comprehensive IP/publication clearance. Remaining: Review exact source/license manifest and historical hash/span compatibility on cloned records before explicit source-origin disposition or archive.
- **PARTIAL** - unused filesystem loaders and brittle replacement imports retired Observed: Original runtime contracts replace imports; import tools are retired; provenance denies comprehensive IP/publication clearance. Remaining: Review exact source/license manifest and historical hash/span compatibility on cloned records before explicit source-origin disposition or archive.
- **PARTIAL** - licensing/provenance accurate Observed: Original runtime contracts replace imports; import tools are retired; provenance denies comprehensive IP/publication clearance. Remaining: Review exact source/license manifest and historical hash/span compatibility on cloned records before explicit source-origin disposition or archive.
- **PARTIAL** - no public release implied Observed: Original runtime contracts replace imports; import tools are retired; provenance denies comprehensive IP/publication clearance. Remaining: Review exact source/license manifest and historical hash/span compatibility on cloned records before explicit source-origin disposition or archive.

### NSAI-032 - Commission the repaired CPU foundation

Status: **QUALIFICATION_PENDING**; accepted:false. Unaccepted dependencies: NSAI-004, NSAI-005, NSAI-006, NSAI-007, NSAI-008, NSAI-009, NSAI-010, NSAI-011, NSAI-012, NSAI-013, NSAI-014, NSAI-015, NSAI-016, NSAI-017, NSAI-018, NSAI-019, NSAI-020, NSAI-021, NSAI-022, NSAI-023, NSAI-024, NSAI-025, NSAI-026, NSAI-027, NSAI-028, NSAI-029, NSAI-030, NSAI-031.

Implemented/tested: Foundation has unit,45 owned realDB checks,26 real-stack checks and real tokenizer/model smoke; user volumes untouched.

Next action: Close every required foundation criterion including ACL/image/backup/compatibility/security acceptance before this gate.

- **PARTIAL** - All stage-1 repair cards accepted with fresh receipts Observed: Foundation has unit,45 owned realDB checks,26 real-stack checks and real tokenizer/model smoke; user volumes untouched. Remaining: Close every required foundation criterion including ACL/image/backup/compatibility/security acceptance before this gate.
- **PARTIAL** - clean boot, upgrade, restart, restore, negative RBAC and real CPU model work pass Observed: Foundation has unit,45 owned realDB checks,26 real-stack checks and real tokenizer/model smoke; user volumes untouched. Remaining: Close every required foundation criterion including ACL/image/backup/compatibility/security acceptance before this gate.
- **PARTIAL** - original user volumes preserved Observed: Foundation has unit,45 owned realDB checks,26 real-stack checks and real tokenizer/model smoke; user volumes untouched. Remaining: Close every required foundation criterion including ACL/image/backup/compatibility/security acceptance before this gate.
- **PARTIAL** - security qualification shown separately Observed: Foundation has unit,45 owned realDB checks,26 real-stack checks and real tokenizer/model smoke; user volumes untouched. Remaining: Close every required foundation criterion including ACL/image/backup/compatibility/security acceptance before this gate.

### NSAI-033 - Compare finite quantities with dimensions and intervals

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-032.

Implemented/tested: Original typed quantity/formula contracts remain proposals; source-bound engineering pipeline uses conservative candidate/unknown states. Clean OCR geometry is separately scoped, not formula recognition.

Next action: Implement/qualify dimensions, temporal intervals, uncertain units and source-family engineering holdouts; formulas remain unsupported for OCR admission.

- **PARTIAL** - 85 C and 185 F, 85 C and 85.0 C are equivalent Observed: Original typed quantity/formula contracts remain proposals; source-bound engineering pipeline uses conservative candidate/unknown states. Clean OCR geometry is separately scoped, not formula recognition. Remaining: Implement/qualify dimensions, temporal intervals, uncertain units and source-family engineering holdouts; formulas remain unsupported for OCR admission.
- **PARTIAL** - incompatible dimensions/conditions do not falsely compare Observed: Original typed quantity/formula contracts remain proposals; source-bound engineering pipeline uses conservative candidate/unknown states. Clean OCR geometry is separately scoped, not formula recognition. Remaining: Implement/qualify dimensions, temporal intervals, uncertain units and source-family engineering holdouts; formulas remain unsupported for OCR admission.
- **PARTIAL** - signs, intervals and rounding have independent oracle tests Observed: Original typed quantity/formula contracts remain proposals; source-bound engineering pipeline uses conservative candidate/unknown states. Clean OCR geometry is separately scoped, not formula recognition. Remaining: Implement/qualify dimensions, temporal intervals, uncertain units and source-family engineering holdouts; formulas remain unsupported for OCR admission.
- **PARTIAL** - raw spans retained Observed: Original typed quantity/formula contracts remain proposals; source-bound engineering pipeline uses conservative candidate/unknown states. Clean OCR geometry is separately scoped, not formula recognition. Remaining: Implement/qualify dimensions, temporal intervals, uncertain units and source-family engineering holdouts; formulas remain unsupported for OCR admission.

### NSAI-034 - Represent negation, conditions, time and uncertainty

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-033.

Implemented/tested: Negation/condition/history/question/proposed observations abstain from unsupported facts; engineering categories stay candidates.

Next action: Add original temporal/table/entity/uncertainty holdouts with extraction/refusal metrics and no corporate dictionaries.

- **PARTIAL** - Negative/historical/conditional/question/table observations remain typed Observed: Negation/condition/history/question/proposed observations abstain from unsupported facts; engineering categories stay candidates. Remaining: Add original temporal/table/entity/uncertainty holdouts with extraction/refusal metrics and no corporate dictionaries.
- **PARTIAL** - unsupported forms abstain Observed: Negation/condition/history/question/proposed observations abstain from unsupported facts; engineering categories stay candidates. Remaining: Add original temporal/table/entity/uncertainty holdouts with extraction/refusal metrics and no corporate dictionaries.
- **PARTIAL** - generic entity handling uses original fixtures without corporate dictionaries Observed: Negation/condition/history/question/proposed observations abstain from unsupported facts; engineering categories stay candidates. Remaining: Add original temporal/table/entity/uncertainty holdouts with extraction/refusal metrics and no corporate dictionaries.

### NSAI-035 - Apply one conflict policy to reflection and learning

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-034, NSAI-017.

Implemented/tested: Reflection includes verified-plus-new active contradictions and bounds/deduplicates proposals.

Next action: Qualify concurrent review/reflection/reparse races and a single current conflict policy in retrieval/canon/reflection on real DB.

- **PARTIAL** - Verified 85 plus new 75 generates bounded deduplicated conflict proposal Observed: Reflection includes verified-plus-new active contradictions and bounds/deduplicates proposals. Remaining: Qualify concurrent review/reflection/reparse races and a single current conflict policy in retrieval/canon/reflection on real DB.
- **PARTIAL** - same active conflict rule applies across retrieval/memory/reflection Observed: Reflection includes verified-plus-new active contradictions and bounds/deduplicates proposals. Remaining: Qualify concurrent review/reflection/reparse races and a single current conflict policy in retrieval/canon/reflection on real DB.

### NSAI-036 - Rank eligible memory and invalidate stale dependencies

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-035.

Implemented/tested: Current memory-scope10 actual PG/API cases pass, with page1reviewed75C excluding page2value95C and2001unrelated legacy rows; current 0df embeds matching source.

Next action: Extend reviewed-memory relevance/omission/source-family holdouts and performance beyond this narrow deterministic fixture.

- **PARTIAL** - 13+ approved facts select by query relevance rather than hash ordering Observed: Current memory-scope10 actual PG/API cases pass, with page1reviewed75C excluding page2value95C and2001unrelated legacy rows; current 0df embeds matching source. Remaining: Extend reviewed-memory relevance/omission/source-family holdouts and performance beyond this narrow deterministic fixture.
- **PARTIAL** - eligible canon/hypothesis/reflection included deliberately Observed: Current memory-scope10 actual PG/API cases pass, with page1reviewed75C excluding page2value95C and2001unrelated legacy rows; current 0df embeds matching source. Remaining: Extend reviewed-memory relevance/omission/source-family holdouts and performance beyond this narrow deterministic fixture.
- **PARTIAL** - changed review/source/rules invalidate projection Observed: Current memory-scope10 actual PG/API cases pass, with page1reviewed75C excluding page2value95C and2001unrelated legacy rows; current 0df embeds matching source. Remaining: Extend reviewed-memory relevance/omission/source-family holdouts and performance beyond this narrow deterministic fixture.

### NSAI-037 - Measure complete memory envelopes and omissions

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-036, NSAI-016.

Implemented/tested: Current memory byte/scope guards and10 actual PG/API cases pass; retrieval8 actual cases report limit+1 conservative omissions without claiming exact truncated totals.

Next action: Qualify larger canon/session/project budgets, complete omission accounting and sustained performance under declared corpora.

- **PARTIAL** - Full JSON/envelope and tokenizer budgets include IDs/status/schema overhead Observed: Current memory byte/scope guards and10 actual PG/API cases pass; retrieval8 actual cases report limit+1 conservative omissions without claiming exact truncated totals. Remaining: Qualify larger canon/session/project budgets, complete omission accounting and sustained performance under declared corpora.
- **PARTIAL** - 1,300-byte envelope cannot claim compliance with 1,024-byte budget Observed: Current memory byte/scope guards and10 actual PG/API cases pass; retrieval8 actual cases report limit+1 conservative omissions without claiming exact truncated totals. Remaining: Qualify larger canon/session/project budgets, complete omission accounting and sustained performance under declared corpora.
- **PARTIAL** - every omitted initial slice listed Observed: Current memory byte/scope guards and10 actual PG/API cases pass; retrieval8 actual cases report limit+1 conservative omissions without claiming exact truncated totals. Remaining: Qualify larger canon/session/project budgets, complete omission accounting and sustained performance under declared corpora.

### NSAI-038 - Persist reversible normalization and chunk geometry

Status: **PARTIALLY_IMPLEMENTED**; accepted:false. Unaccepted dependencies: NSAI-032.

Implemented/tested: All source parsers persist compact raw-to-normalized code-point offset maps, share bounded word-aware chunk boundaries where whitespace permits, preserve exact chunk offsets/hashes and validate map/end-offset custody; no page geometry is inferred.

Next action: Add queryable chunk geometry for supplied PDF/OCR boxes and correction round-trip oracles; retain conservative behavior where geometry is unavailable.

- **PARTIAL** - NFC, whitespace, aliases and chunk offsets round-trip to immutable raw spans Observed: Text/PDF and OCR normalization maps bind every normalized code-point range to immutable raw code-point offsets, including NFC composition, collapsed whitespace and Hangul composition; identity maps cover JSON/CSV/TSV/XLSX records. Validation recomputes maps and rejects tampering. Remaining: Add correction edit/round-trip oracles and exercise downstream selection against all normalization forms.
- **PARTIAL** - overlap remains word-safe Observed: Chunk boundaries prefer whitespace before the size limit for all source parsers; overlong unbroken tokens use bounded code-point-safe splits. Custody tests cover offsets, hashes and end offsets; an owned PostgreSQL manifest test confirms structured-source maps persist. Remaining: Qualify any overlap policy and additional source-family cases; unbroken tokens may split at the hard size bound.
- **CONFIRMED** - page geometry never inferred from line numbers Observed: A source-level synthetic native-PDF regression confirms page:1:line:1 is retained while spans and chunks omit bbox/geometry/rect/quad_points fields; see the current source-bound scoped receipt and cases under evidence/implementation/NSAI-038/. Remaining: No-inference invariant is addressed; actual PDF.js/OCR visual alignment and supplied geometry remain outside this confirmation. Card acceptance remains pending.

### NSAI-039 - Version extraction, indexes and projections independently

Status: **PARTIALLY_IMPLEMENTED**; accepted:false. Unaccepted dependencies: NSAI-038.

Implemented/tested: Reparse stores an inactive immutable extraction-generation proposal without replacing original evidence.

Next action: Implement active index/generation selection, shadow rebuild, stale projection rejection and replay/rollback qualification.

- **PARTIAL** - Same original bytes can be reparsed without replacing originals Observed: Reparse stores an inactive immutable extraction-generation proposal without replacing original evidence. Remaining: Implement active index/generation selection, shadow rebuild, stale projection rejection and replay/rollback qualification.
- **PARTIAL** - generation IDs bind parser/rules/source Observed: Reparse stores an inactive immutable extraction-generation proposal without replacing original evidence. Remaining: Implement active index/generation selection, shadow rebuild, stale projection rejection and replay/rollback qualification.
- **PARTIAL** - stale index/projection excluded Observed: Reparse stores an inactive immutable extraction-generation proposal without replacing original evidence. Remaining: Implement active index/generation selection, shadow rebuild, stale projection rejection and replay/rollback qualification.
- **PARTIAL** - replay and rollback verified Observed: Reparse stores an inactive immutable extraction-generation proposal without replacing original evidence. Remaining: Implement active index/generation selection, shadow rebuild, stale projection rejection and replay/rollback qualification.

### NSAI-040 - Improve measured scoped lexical recall

Status: **PARTIALLY_IMPLEMENTED**; accepted:false. Unaccepted dependencies: NSAI-038, NSAI-039, NSAI-034.

Implemented/tested: Current retrieval8 actual PG/public-API cases preserve ranking and expose13matching lower-bound chunks with12returned; total truncated count unknown. Earlier lexical17unit/11PGquery cases retained.

Next action: Collect source-family heldout recall/ranking/ambiguity/support metrics and actual application sustained performance; lexical coverage is not semantic evidence completeness.

- **UNVERIFIED** - Paraphrase/revision-qualified held-out queries measured with Recall@k/MRR/citation precision Observed: Current retrieval8 actual PG/public-API cases preserve ranking and expose13matching lower-bound chunks with12returned; total truncated count unknown. Earlier lexical17unit/11PGquery cases retained. Remaining: Collect source-family heldout recall/ranking/ambiguity/support metrics and actual application sustained performance; lexical coverage is not semantic evidence completeness.
- **PARTIAL** - scope filtered before ranking Observed: Current retrieval8 actual PG/public-API cases preserve ranking and expose13matching lower-bound chunks with12returned; total truncated count unknown. Earlier lexical17unit/11PGquery cases retained. Remaining: Collect source-family heldout recall/ranking/ambiguity/support metrics and actual application sustained performance; lexical coverage is not semantic evidence completeness.
- **PARTIAL** - lexical alternates/overlap and optional RRF accepted only on paired quality evidence Observed: Current retrieval8 actual PG/public-API cases preserve ranking and expose13matching lower-bound chunks with12returned; total truncated count unknown. Earlier lexical17unit/11PGquery cases retained. Remaining: Collect source-family heldout recall/ranking/ambiguity/support metrics and actual application sustained performance; lexical coverage is not semantic evidence completeness.

### NSAI-041 - Check factual support beyond citation identity

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-033, NSAI-040, NSAI-037.

Implemented/tested: Citation/numeric/entity checks now reject invented or transferred values; all drafts remain unverified.

Next action: Measure heldout support/refusal/quote/conversion and negation/condition/relation fidelity; no second model as truth authority.

- **PARTIAL** - Valid citation with invented quantity/entity is withheld Observed: Citation/numeric/entity checks now reject invented or transferred values; all drafts remain unverified. Remaining: Measure heldout support/refusal/quote/conversion and negation/condition/relation fidelity; no second model as truth authority.
- **PARTIAL** - supported quotes/conversions retain exact provenance Observed: Citation/numeric/entity checks now reject invented or transferred values; all drafts remain unverified. Remaining: Measure heldout support/refusal/quote/conversion and negation/condition/relation fidelity; no second model as truth authority.
- **PARTIAL** - held-out refusal/support metrics Observed: Citation/numeric/entity checks now reject invented or transferred values; all drafts remain unverified. Remaining: Measure heldout support/refusal/quote/conversion and negation/condition/relation fidelity; no second model as truth authority.
- **PARTIAL** - model drafts always unverified Observed: Citation/numeric/entity checks now reject invented or transferred values; all drafts remain unverified. Remaining: Measure heldout support/refusal/quote/conversion and negation/condition/relation fidelity; no second model as truth authority.
- **CONFIRMED** - no second model as truth authority Observed: Citation/numeric/entity checks now reject invented or transferred values; all drafts remain unverified. Remaining: Measure heldout support/refusal/quote/conversion and negation/condition/relation fidelity; no second model as truth authority.

### NSAI-042 - Bound database work and unblock async handlers

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-032, NSAI-040.

Implemented/tested: Four-connection pool reuses connections and async DB work is offloaded; bounded concurrent real reads pass.

Next action: Qualify full application event-loop/read-write contention and sustained tail behavior; current direct-versus-pool mechanism benchmark is complete, not historical baseline.

- **PARTIAL** - Bounded pool/coherent snapshot/offload or async chosen from matched measurements Observed: Four-connection pool reuses connections and async DB work is offloaded; bounded concurrent real reads pass. Remaining: Record matched lag/connections/SQL plans/snapshot consistency/max-workload quality and RBAC instead of inferring production tails.
- **PARTIAL** - event-loop lag/connection count/SQL plans recorded Observed: Four-connection pool reuses connections and async DB work is offloaded; bounded concurrent real reads pass. Remaining: Record matched lag/connections/SQL plans/snapshot consistency/max-workload quality and RBAC instead of inferring production tails.
- **PARTIAL** - permission/conflict/transaction behavior unchanged Observed: Four-connection pool reuses connections and async DB work is offloaded; bounded concurrent real reads pass. Remaining: Record matched lag/connections/SQL plans/snapshot consistency/max-workload quality and RBAC instead of inferring production tails.

### NSAI-043 - Return safe original filename and media type

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-038, NSAI-010.

Implemented/tested: Safe Unicode Content-Disposition and media preserve exact originals; private PDF viewer is separate.

Next action: Exercise HEAD/range/cache/error/MIME/control behavior on real endpoints and preserve denial of active embedding.

- **PARTIAL** - Viewer and download paths separated Observed: Safe Unicode Content-Disposition and media preserve exact originals; private PDF viewer is separate. Remaining: Exercise HEAD/range/cache/error/MIME/control behavior on real endpoints and preserve denial of active embedding.
- **PARTIAL** - safe Content-Disposition handles Unicode/control characters Observed: Safe Unicode Content-Disposition and media preserve exact originals; private PDF viewer is separate. Remaining: Exercise HEAD/range/cache/error/MIME/control behavior on real endpoints and preserve denial of active embedding.
- **PARTIAL** - original bytes/hash preserved Observed: Safe Unicode Content-Disposition and media preserve exact originals; private PDF viewer is separate. Remaining: Exercise HEAD/range/cache/error/MIME/control behavior on real endpoints and preserve denial of active embedding.
- **CONFIRMED** - no automatic active-content embedding Observed: Safe Unicode Content-Disposition and media preserve exact originals; private PDF viewer is separate. Remaining: Exercise HEAD/range/cache/error/MIME/control behavior on real endpoints and preserve denial of active embedding.

### NSAI-044 - Make conversation failures and retries ordered

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-011, NSAI-015, NSAI-039.

Implemented/tested: Durable actor/request invocation settlement and expired pending terminal failure guards pass focused/actual owned tests. Current31-case browser stack exercises state clearing and independent review.

Next action: Qualify complete crash/retry/cancel/concurrency and reconciliation histories with exact final source bindings.

- **PARTIAL** - Failed asks exit pending state Observed: Durable actor/request invocation settlement and expired pending terminal failure guards pass focused/actual owned tests. Current31-case browser stack exercises state clearing and independent review. Remaining: Qualify complete crash/retry/cancel/concurrency and reconciliation histories with exact final source bindings.
- **PARTIAL** - delayed/out-of-order evidence/model calls cannot append to wrong session Observed: Durable actor/request invocation settlement and expired pending terminal failure guards pass focused/actual owned tests. Current31-case browser stack exercises state clearing and independent review. Remaining: Qualify complete crash/retry/cancel/concurrency and reconciliation histories with exact final source bindings.
- **PARTIAL** - retry idempotent Observed: Durable actor/request invocation settlement and expired pending terminal failure guards pass focused/actual owned tests. Current31-case browser stack exercises state clearing and independent review. Remaining: Qualify complete crash/retry/cancel/concurrency and reconciliation histories with exact final source bindings.
- **PARTIAL** - active/pending/closed object switches explicit Observed: Durable actor/request invocation settlement and expired pending terminal failure guards pass focused/actual owned tests. Current31-case browser stack exercises state clearing and independent review. Remaining: Qualify complete crash/retry/cancel/concurrency and reconciliation histories with exact final source bindings.

### NSAI-045 - Paginate and lazily render large views accessibly

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-042, NSAI-044.

Implemented/tested: UI renders25-card pages for100documents/2000claims, limits inspector size, filters governed pages and fits mobile.

Next action: Complete actual maximum-corpus paging/RBAC/performance and keyboard/focus/status/contrast accessibility cases.

- **PARTIAL** - Declared 2,000-claim/100-document workload stays bounded Observed: UI renders25-card pages for100documents/2000claims, limits inspector size, filters governed pages and fits mobile. Remaining: Complete actual maximum-corpus paging/RBAC/performance and keyboard/focus/status/contrast accessibility cases.
- **PARTIAL** - inspector size limited Observed: UI renders25-card pages for100documents/2000claims, limits inspector size, filters governed pages and fits mobile. Remaining: Complete actual maximum-corpus paging/RBAC/performance and keyboard/focus/status/contrast accessibility cases.
- **PARTIAL** - keyboard focus/status/contrast/mobile behaviors tested Observed: UI renders25-card pages for100documents/2000claims, limits inspector size, filters governed pages and fits mobile. Remaining: Complete actual maximum-corpus paging/RBAC/performance and keyboard/focus/status/contrast accessibility cases.
- **PARTIAL** - API pagination preserves authorization Observed: UI renders25-card pages for100documents/2000claims, limits inspector size, filters governed pages and fits mobile. Remaining: Complete actual maximum-corpus paging/RBAC/performance and keyboard/focus/status/contrast accessibility cases.

### NSAI-046 - Plan capacity, holds and non-destructive retention

Status: **PARTIALLY_IMPLEMENTED**; accepted:false. Unaccepted dependencies: NSAI-032, NSAI-030.

Implemented/tested: Document/claim/governed count/byte caps exist; retention inspects growth and holds originals/audit without deletion.

Next action: Bound sessions/messages/invocations/audit growth and add owner/eligible-ID/hold-aware export with separately reviewed archive/expiry policy.

- **PARTIAL** - Capacity growth and limits measurable Observed: Document/claim/governed count/byte caps exist; retention inspects growth and holds originals/audit without deletion. Remaining: Bound sessions/messages/invocations/audit growth and add owner/eligible-ID/hold-aware export with separately reviewed archive/expiry policy.
- **PARTIAL** - dry-run reports eligible IDs/holds/owners Observed: Document/claim/governed count/byte caps exist; retention inspects growth and holds originals/audit without deletion. Remaining: Bound sessions/messages/invocations/audit growth and add owner/eligible-ID/hold-aware export with separately reviewed archive/expiry policy.
- **PARTIAL** - no automatic destructive cleanup Observed: Document/claim/governed count/byte caps exist; retention inspects growth and holds originals/audit without deletion. Remaining: Bound sessions/messages/invocations/audit growth and add owner/eligible-ID/hold-aware export with separately reviewed archive/expiry policy.
- **PARTIAL** - future expiry/archive actions require separately reviewed policy Observed: Document/claim/governed count/byte caps exist; retention inspects growth and holds originals/audit without deletion. Remaining: Bound sessions/messages/invocations/audit growth and add owner/eligible-ID/hold-aware export with separately reviewed archive/expiry policy.

### NSAI-047 - Publish honest contracts and capability maturity

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-032.

Implemented/tested: Current capabilities expose data-only staged boundaries;0df exact57src/assets match and current31-case stack pass. Unsafe legacy generator is retired.

Next action: Complete capability-to-owner-to-qualification mapping and independent gate acceptance; existence/metadata is not feature qualification.

- **PARTIAL** - Active/staged/unsupported/disabled states mapped to requirements, functions, routes, permissions and evidence Observed: Current capabilities expose data-only staged boundaries;0df exact57src/assets match and current31-case stack pass. Unsafe legacy generator is retired. Remaining: Complete capability-to-owner-to-qualification mapping and independent gate acceptance; existence/metadata is not feature qualification.
- **PARTIAL** - finite strict schemas Observed: Current capabilities expose data-only staged boundaries;0df exact57src/assets match and current31-case stack pass. Unsafe legacy generator is retired. Remaining: Complete capability-to-owner-to-qualification mapping and independent gate acceptance; existence/metadata is not feature qualification.
- **PARTIAL** - dormant helper presence never claims live capability Observed: Current capabilities expose data-only staged boundaries;0df exact57src/assets match and current31-case stack pass. Unsafe legacy generator is retired. Remaining: Complete capability-to-owner-to-qualification mapping and independent gate acceptance; existence/metadata is not feature qualification.

### NSAI-048 - Use source-bound deterministic answers where qualified

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-041, NSAI-047.

Implemented/tested: Deterministic source excerpts and conflict/missing-coverage abstention avoid unnecessary model use.

Next action: Prove exact ID/hash/review/scope against empty/prefix/stale references and compare deterministic versus CPU quality/cost on matched holdout.

- **PARTIAL** - Actual source ID/hash/review/scope validated Observed: Deterministic source excerpts and conflict/missing-coverage abstention avoid unnecessary model use. Remaining: Prove exact ID/hash/review/scope against empty/prefix/stale references and compare deterministic versus CPU quality/cost on matched holdout.
- **PARTIAL** - empty or prefix-only reference rejected Observed: Deterministic source excerpts and conflict/missing-coverage abstention avoid unnecessary model use. Remaining: Prove exact ID/hash/review/scope against empty/prefix/stale references and compare deterministic versus CPU quality/cost on matched holdout.
- **PARTIAL** - stale/unknown source denied Observed: Deterministic source excerpts and conflict/missing-coverage abstention avoid unnecessary model use. Remaining: Prove exact ID/hash/review/scope against empty/prefix/stale references and compare deterministic versus CPU quality/cost on matched holdout.
- **PARTIAL** - exact-answer lane benchmarked against model use without upgrading authority Observed: Deterministic source excerpts and conflict/missing-coverage abstention avoid unnecessary model use. Remaining: Prove exact ID/hash/review/scope against empty/prefix/stale references and compare deterministic versus CPU quality/cost on matched holdout.

### NSAI-049 - Accept quality and performance refinement

Status: **EXPERIMENT_PARTIAL_QUALITY_FAILED**; accepted:false. Unaccepted dependencies: NSAI-033, NSAI-034, NSAI-035, NSAI-036, NSAI-037, NSAI-038, NSAI-039, NSAI-040, NSAI-041, NSAI-042, NSAI-043, NSAI-044, NSAI-045, NSAI-046, NSAI-047, NSAI-048.

Implemented/tested: Bounded actual CPU4K/8K experiment PARTIAL: each30warm short and30real tokenizer checks complete. 6119prompt+114reserve refused4K/admitted8K. Warm p95~2384.896/2453.644ms under repeated56/57token cache. All60numeric75C correct; strict citation0/60. One6K8K generation timeout180s. No long-quality or SLO qualification.

Next action: Repair/qualify grounded response contract and long-prompt completion on declared resources, then full application cold/warm sustained load with quality/support/queue/event-loop metrics. Keep live4K and optional16K/32K deferred.

- **UNVERIFIED** - Matched CPU corpus and configuration, cold/warm labels, adequate predeclared samples, concurrency/queue/lag/memory data and failure cases Observed: Bounded actual CPU4K/8K experiment PARTIAL: each30warm short and30real tokenizer checks complete. 6119prompt+114reserve refused4K/admitted8K. Warm p95~2384.896/2453.644ms under repeated56/57token cache. All60numeric75C correct; strict citation0/60. One6K8K generation timeout180s. No long-quality or SLO qualification. Remaining: Repair/qualify grounded response contract and long-prompt completion on declared resources, then full application cold/warm sustained load with quality/support/queue/event-loop metrics. Keep live4K and optional16K/32K deferred.
- **PARTIAL** - no tail/scalability claim from n=5 Observed: Bounded actual CPU4K/8K experiment PARTIAL: each30warm short and30real tokenizer checks complete. 6119prompt+114reserve refused4K/admitted8K. Warm p95~2384.896/2453.644ms under repeated56/57token cache. All60numeric75C correct; strict citation0/60. One6K8K generation timeout180s. No long-quality or SLO qualification. Remaining: Repair/qualify grounded response contract and long-prompt completion on declared resources, then full application cold/warm sustained load with quality/support/queue/event-loop metrics. Keep live4K and optional16K/32K deferred.
- **PARTIAL** - no quality/RBAC/recovery regression Observed: Bounded actual CPU4K/8K experiment PARTIAL: each30warm short and30real tokenizer checks complete. 6119prompt+114reserve refused4K/admitted8K. Warm p95~2384.896/2453.644ms under repeated56/57token cache. All60numeric75C correct; strict citation0/60. One6K8K generation timeout180s. No long-quality or SLO qualification. Remaining: Repair/qualify grounded response contract and long-prompt completion on declared resources, then full application cold/warm sustained load with quality/support/queue/event-loop metrics. Keep live4K and optional16K/32K deferred.

### NSAI-050 - Add server-validated document/revision/page questions

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-049.

Implemented/tested: Server validates document/revision/page scope; stale scope fails and incomplete coverage is declared/withheld.

Next action: Qualify cross-source/unknown/unauthorized/page-failure scopes on final HTTP; single project does not imply tenant isolation.

- **PARTIAL** - Selected source/revision/page is the retrieval universe Observed: Server validates document/revision/page scope; stale scope fails and incomplete coverage is declared/withheld. Remaining: Qualify cross-source/unknown/unauthorized/page-failure scopes on final HTTP; single project does not imply tenant isolation.
- **PARTIAL** - cross-document comparison explicit Observed: Server validates document/revision/page scope; stale scope fails and incomplete coverage is declared/withheld. Remaining: Qualify cross-source/unknown/unauthorized/page-failure scopes on final HTTP; single project does not imply tenant isolation.
- **PARTIAL** - wrong/stale/unauthorized scopes rejected Observed: Server validates document/revision/page scope; stale scope fails and incomplete coverage is declared/withheld. Remaining: Qualify cross-source/unknown/unauthorized/page-failure scopes on final HTTP; single project does not imply tenant isolation.
- **PARTIAL** - completeness shown with answers Observed: Server validates document/revision/page scope; stale scope fails and incomplete coverage is declared/withheld. Remaining: Qualify cross-source/unknown/unauthorized/page-failure scopes on final HTTP; single project does not imply tenant isolation.

### NSAI-051 - Build a private PDF workspace and exact citation navigation

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-050, NSAI-043, NSAI-031.

Implemented/tested: Bundled pinned PDF.js/worker retains license/provenance; actual Chromium renders exact private PDF bytes/canvas and clears resources.

Next action: Test hostile actions/forms/attachments/external links, navigation/zoom/text pane and authenticated HEAD/range/cache/thumb/error paths.

- **CONFIRMED** - Pinned locally bundled renderer/worker Observed: Bundled pinned PDF.js/worker retains license/provenance; actual Chromium renders exact private PDF bytes/canvas and clears resources. Remaining: Test hostile actions/forms/attachments/external links, navigation/zoom/text pane and authenticated HEAD/range/cache/thumb/error paths.
- **PARTIAL** - navigation/zoom/text pane opens exact revision/page Observed: Bundled pinned PDF.js/worker retains license/provenance; actual Chromium renders exact private PDF bytes/canvas and clears resources. Remaining: Test hostile actions/forms/attachments/external links, navigation/zoom/text pane and authenticated HEAD/range/cache/thumb/error paths.
- **PARTIAL** - no PDF JavaScript/actions/forms/attachments/external fetch Observed: Bundled pinned PDF.js/worker retains license/provenance; actual Chromium renders exact private PDF bytes/canvas and clears resources. Remaining: Test hostile actions/forms/attachments/external links, navigation/zoom/text pane and authenticated HEAD/range/cache/thumb/error paths.
- **PARTIAL** - CSP preserved Observed: Bundled pinned PDF.js/worker retains license/provenance; actual Chromium renders exact private PDF bytes/canvas and clears resources. Remaining: Test hostile actions/forms/attachments/external links, navigation/zoom/text pane and authenticated HEAD/range/cache/thumb/error paths.
- **PARTIAL** - auth on HEAD/range/cache/thumb/error paths Observed: Bundled pinned PDF.js/worker retains license/provenance; actual Chromium renders exact private PDF bytes/canvas and clears resources. Remaining: Test hostile actions/forms/attachments/external links, navigation/zoom/text pane and authenticated HEAD/range/cache/thumb/error paths.
- **PARTIAL** - logout clears buffers Observed: Bundled pinned PDF.js/worker retains license/provenance; actual Chromium renders exact private PDF bytes/canvas and clears resources. Remaining: Test hostile actions/forms/attachments/external links, navigation/zoom/text pane and authenticated HEAD/range/cache/thumb/error paths.

### NSAI-052 - Build bounded owned OCR jobs and leases

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-051, NSAI-029, NSAI-023.

Implemented/tested: Nonroot/read-only OCR has dedicated credentials and pixel/time/render bounds with no DB/model secrets; real confined jobs pass.

Next action: Implement durable bounded queue/lease/expiry/idempotency/cancel/restart and prove containment/reusability after crashes.

- **PARTIAL** - Bounded queue/lease/expiry/cancel/restart/idempotency Observed: Nonroot/read-only OCR has dedicated credentials and pixel/time/render bounds with no DB/model secrets; real confined jobs pass. Remaining: Implement durable bounded queue/lease/expiry/idempotency/cancel/restart and prove containment/reusability after crashes.
- **PARTIAL** - no DB/model secrets or external network Observed: Nonroot/read-only OCR has dedicated credentials and pixel/time/render bounds with no DB/model secrets; real confined jobs pass. Remaining: Implement durable bounded queue/lease/expiry/idempotency/cancel/restart and prove containment/reusability after crashes.
- **PARTIAL** - CPU/RAM/time/pixel limits before allocation Observed: Nonroot/read-only OCR has dedicated credentials and pixel/time/render bounds with no DB/model secrets; real confined jobs pass. Remaining: Implement durable bounded queue/lease/expiry/idempotency/cancel/restart and prove containment/reusability after crashes.
- **PARTIAL** - cancellation and child crash leave worker reusable Observed: Nonroot/read-only OCR has dedicated credentials and pixel/time/render bounds with no DB/model secrets; real confined jobs pass. Remaining: Implement durable bounded queue/lease/expiry/idempotency/cancel/restart and prove containment/reusability after crashes.

### NSAI-053 - Choose native extraction or OCR for each page

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-052, NSAI-014.

Implemented/tested: Pages choose native/blank/OCR-required; printed English candidates are source-bound and unsupported transforms are withheld.

Next action: Qualify mixed/forms/blank routing and implement/test orientation/deskew before support; strengthen handwriting/language/formula refusals.

- **PARTIAL** - Native/blank/scanned/mixed classification per page Observed: Pages choose native/blank/OCR-required; printed English candidates are source-bound and unsupported transforms are withheld. Remaining: Qualify mixed/forms/blank routing and implement/test orientation/deskew before support; strengthen handwriting/language/formula refusals.
- **PARTIAL** - orientation/deskew actual transforms recorded Observed: Pages choose native/blank/OCR-required; printed English candidates are source-bound and unsupported transforms are withheld. Remaining: Qualify mixed/forms/blank routing and implement/test orientation/deskew before support; strengthen handwriting/language/formula refusals.
- **CONFIRMED** - English printed baseline explicit Observed: Pages choose native/blank/OCR-required; printed English candidates are source-bound and unsupported transforms are withheld. Remaining: Qualify mixed/forms/blank routing and implement/test orientation/deskew before support; strengthen handwriting/language/formula refusals.
- **PARTIAL** - unsupported languages/handwriting flagged Observed: Pages choose native/blank/OCR-required; printed English candidates are source-bound and unsupported transforms are withheld. Remaining: Qualify mixed/forms/blank routing and implement/test orientation/deskew before support; strengthen handwriting/language/formula refusals.
- **CONFIRMED** - OCR observations never approved automatically Observed: Pages choose native/blank/OCR-required; printed English candidates are source-bound and unsupported transforms are withheld. Remaining: Qualify mixed/forms/blank routing and implement/test orientation/deskew before support; strengthen handwriting/language/formula refusals.

### NSAI-054 - Preserve raw OCR, boxes and coordinate transforms

Status: **IMPLEMENTED_NARROW_GEOMETRY_QUALIFIED**; accepted:false. Unaccepted dependencies: NSAI-053, NSAI-038.

Implemented/tested: Actual OCR geometry4original clean Aileron raster pages/48 labeled words passes48joint text+IoU cases, minIoU0.94595, no textFP/FN. Bulk200-page calibration had roundtrip-only geometry; general transforms remain unqualified.

Next action: Label additional fonts/degraded/domain layouts and qualify crop/rotation/UserUnit/deskew/geometry bounds; narrow clean identity300DPI word IoU is not general glyph accuracy.

- **UNVERIFIED** - UserUnit/crop/rotation/deskew/DPI transforms and inverse all corners tested Observed: Actual OCR geometry4original clean Aileron raster pages/48 labeled words passes48joint text+IoU cases, minIoU0.94595, no textFP/FN. Bulk200-page calibration had roundtrip-only geometry; general transforms remain unqualified. Remaining: Label additional fonts/degraded/domain layouts and qualify crop/rotation/UserUnit/deskew/geometry bounds; narrow clean identity300DPI word IoU is not general glyph accuracy.
- **PARTIAL** - raw/normalized text and engine score meaning retained Observed: Actual OCR geometry4original clean Aileron raster pages/48 labeled words passes48joint text+IoU cases, minIoU0.94595, no textFP/FN. Bulk200-page calibration had roundtrip-only geometry; general transforms remain unqualified. Remaining: Label additional fonts/degraded/domain layouts and qualify crop/rotation/UserUnit/deskew/geometry bounds; narrow clean identity300DPI word IoU is not general glyph accuracy.
- **UNVERIFIED** - corrections append with lineage rather than rewriting originals Observed: Actual OCR geometry4original clean Aileron raster pages/48 labeled words passes48joint text+IoU cases, minIoU0.94595, no textFP/FN. Bulk200-page calibration had roundtrip-only geometry; general transforms remain unqualified. Remaining: Label additional fonts/degraded/domain layouts and qualify crop/rotation/UserUnit/deskew/geometry bounds; narrow clean identity300DPI word IoU is not general glyph accuracy.

### NSAI-055 - Implement independently checked OCR metrics and holdouts

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-054.

Implemented/tested: Bulk200pages/50original synthetic documents retains source-family split and failed cohorts. New4page/48word clean geometry truth passes only its declared cohort.

Next action: Add real-domain/source-family accuracy and critical semantic/geometry truth; retain critical negation/degraded/formula withholding.

- **CONFIRMED** - CER/WER edit counts include insertions and may exceed 1 Observed: Bulk200pages/50original synthetic documents retains source-family split and failed cohorts. New4page/48word clean geometry truth passes only its declared cohort. Remaining: Add real-domain/source-family accuracy and critical semantic/geometry truth; retain critical negation/degraded/formula withholding.
- **CONFIRMED** - blank reference scored separately Observed: Bulk200pages/50original synthetic documents retains source-family split and failed cohorts. New4page/48word clean geometry truth passes only its declared cohort. Remaining: Add real-domain/source-family accuracy and critical semantic/geometry truth; retain critical negation/degraded/formula withholding.
- **PARTIAL** - critical digits/signs/units/negation/exponents and layout/table metrics reported Observed: Bulk200pages/50original synthetic documents retains source-family split and failed cohorts. New4page/48word clean geometry truth passes only its declared cohort. Remaining: Add real-domain/source-family accuracy and critical semantic/geometry truth; retain critical negation/degraded/formula withholding.
- **PARTIAL** - source-family split prevents leakage Observed: Bulk200pages/50original synthetic documents retains source-family split and failed cohorts. New4page/48word clean geometry truth passes only its declared cohort. Remaining: Add real-domain/source-family accuracy and critical semantic/geometry truth; retain critical negation/degraded/formula withholding.

### NSAI-056 - Calibrate OCR admission and resource targets

Status: **QUALIFICATION_FAILED_QUALITY**; accepted:false. Unaccepted dependencies: NSAI-055, NSAI-052.

Implemented/tested: Synthetic clean proposal subset passes; critical negation missed, degraded tables fail and formula cohort unsupported. Separate4page/48word geometry passes minIoU0.94595 without broadening OCR admission.

Next action: Improve and independently requalify failed critical/degraded/formula cohorts and unsupported transforms; no general OCR quality gate PASS.

- **PARTIAL** - Proposed 200 pages/50 documents, clean CER<=1% WER<=3%, degraded CER<=3% WER<=8%, critical exact>=99.5%, geometry roundtrip<=0.5pt/IoU median>=0.9/p95 boundary<=2pt are evaluated as uncalibrated targets Observed: Synthetic clean proposal subset passes; critical negation missed, degraded tables fail and formula cohort unsupported. Separate4page/48word geometry passes minIoU0.94595 without broadening OCR admission. Remaining: Improve and independently requalify failed critical/degraded/formula cohorts and unsupported transforms; no general OCR quality gate PASS.
- **PARTIAL** - confidence not presumed probability Observed: Synthetic clean proposal subset passes; critical negation missed, degraded tables fail and formula cohort unsupported. Separate4page/48word geometry passes minIoU0.94595 without broadening OCR admission. Remaining: Improve and independently requalify failed critical/degraded/formula cohorts and unsupported transforms; no general OCR quality gate PASS.
- **PARTIAL** - 10s/page at 300DPI/512MiB calibrated with total-job limits Observed: Synthetic clean proposal subset passes; critical negation missed, degraded tables fail and formula cohort unsupported. Separate4page/48word geometry passes minIoU0.94595 without broadening OCR admission. Remaining: Improve and independently requalify failed critical/degraded/formula cohorts and unsupported transforms; no general OCR quality gate PASS.

### NSAI-057 - Represent recognized formula candidates safely

Status: **PARTIALLY_IMPLEMENTED**; accepted:false. Unaccepted dependencies: NSAI-054, NSAI-033.

Implemented/tested: Explicit dimensionless formula proposals retain expression/source hash/locator; general formula OCR is withheld.

Next action: Add source boxes/variables/dimensions/assumptions/superscript/fraction/table-link recognition oracles or preserve unsupported states.

- **UNVERIFIED** - Verbatim symbols, normalized notation, variables/dimensions/assumptions/source boxes stored Observed: Explicit dimensionless formula proposals retain expression/source hash/locator; general formula OCR is withheld. Remaining: Add source boxes/variables/dimensions/assumptions/superscript/fraction/table-link recognition oracles or preserve unsupported states.
- **UNVERIFIED** - superscripts/fractions/table links tested Observed: Explicit dimensionless formula proposals retain expression/source hash/locator; general formula OCR is withheld. Remaining: Add source boxes/variables/dimensions/assumptions/superscript/fraction/table-link recognition oracles or preserve unsupported states.
- **CONFIRMED** - ambiguous/unsupported formula recognition explicitly withheld Observed: Explicit dimensionless formula proposals retain expression/source hash/locator; general formula OCR is withheld. Remaining: Add source boxes/variables/dimensions/assumptions/superscript/fraction/table-link recognition oracles or preserve unsupported states.

### NSAI-058 - Validate finite allowlisted calculations without execution

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-057, NSAI-041.

Implemented/tested: Finite Decimal AST allowlist rejects eval/calls/attributes and retains expression provenance without execution.

Next action: Add dimensional/sign/rounding/version/input-span contracts and independently reviewed finite fixture catalog; no generic math recognition.

- **CONFIRMED** - Small grammar rejects Python/eval/functions outside allowlist Observed: Finite Decimal AST allowlist rejects eval/calls/attributes and retains expression provenance without execution. Remaining: Add dimensional/sign/rounding/version/input-span contracts and independently reviewed finite fixture catalog; no generic math recognition.
- **PARTIAL** - finite Decimal/dimensions/sign/rounding independently verified Observed: Finite Decimal AST allowlist rejects eval/calls/attributes and retains expression provenance without execution. Remaining: Add dimensional/sign/rounding/version/input-span contracts and independently reviewed finite fixture catalog; no generic math recognition.
- **PARTIAL** - formula/version/input spans recorded Observed: Finite Decimal AST allowlist rejects eval/calls/attributes and retains expression provenance without execution. Remaining: Add dimensional/sign/rounding/version/input-span contracts and independently reviewed finite fixture catalog; no generic math recognition.
- **PARTIAL** - 100% exact only for declared finite fixture set, no generic math recognition claim Observed: Finite Decimal AST allowlist rejects eval/calls/attributes and retains expression provenance without execution. Remaining: Add dimensional/sign/rounding/version/input-span contracts and independently reviewed finite fixture catalog; no generic math recognition.

### NSAI-059 - Qualify the complete PDF/OCR/formula workflow

Status: **QUALIFICATION_PENDING**; accepted:false. Unaccepted dependencies: NSAI-051, NSAI-056, NSAI-058.

Implemented/tested: Private native/raster scopedPDF, EnglishOCR, refusals and formula-unit smoke exist; real browser subcases pass.

Next action: Finish rotated/multicolumn/table/formula/encrypted/malformed and correction/source-auth subgroup qualification with failures visible.

- **PARTIAL** - Native/scanned/mixed/rotated/multicolumn/table/formula/encrypted/malformed fixtures Observed: Private native/raster scopedPDF, EnglishOCR, refusals and formula-unit smoke exist; real browser subcases pass. Remaining: Finish rotated/multicolumn/table/formula/encrypted/malformed and correction/source-auth subgroup qualification with failures visible.
- **PARTIAL** - source auth, private renderer, correction review, scoped QA and containment pass with per-subgroup failures and unsupported states visible Observed: Private native/raster scopedPDF, EnglishOCR, refusals and formula-unit smoke exist; real browser subcases pass. Remaining: Finish rotated/multicolumn/table/formula/encrypted/malformed and correction/source-auth subgroup qualification with failures visible.

### NSAI-060 - Assemble a small deterministic evidence stage graph

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-059, NSAI-039.

Implemented/tested: Original bounded allowlisted DAG rejects cycles/missing dependencies and binds source/config/operator/output; persisted assembly stays candidate.

Next action: Persist parser/rules/model generation selection and prove replay invalidation/rollback; generation1 receipts are not active orchestration.

- **CONFIRMED** - Owned bounded DAG rejects cycles/unknown dependencies Observed: Original bounded allowlisted DAG rejects cycles/missing dependencies and binds source/config/operator/output; persisted assembly stays candidate. Remaining: Persist parser/rules/model generation selection and prove replay invalidation/rollback; generation1 receipts are not active orchestration.
- **PARTIAL** - semantic fingerprints distinct from paths/timestamps Observed: Original bounded allowlisted DAG rejects cycles/missing dependencies and binds source/config/operator/output; persisted assembly stays candidate. Remaining: Persist parser/rules/model generation selection and prove replay invalidation/rollback; generation1 receipts are not active orchestration.
- **PARTIAL** - replay invalidation binds source/parser/rules/model generations Observed: Original bounded allowlisted DAG rejects cycles/missing dependencies and binds source/config/operator/output; persisted assembly stays candidate. Remaining: Persist parser/rules/model generation selection and prove replay invalidation/rollback; generation1 receipts are not active orchestration.
- **CONFIRMED** - no full PX runtime transplant Observed: Original bounded allowlisted DAG rejects cycles/missing dependencies and binds source/config/operator/output; persisted assembly stays candidate. Remaining: Persist parser/rules/model generation selection and prove replay invalidation/rollback; generation1 receipts are not active orchestration.

### NSAI-061 - Govern proposals through holdout, review and rollback

Status: **PARTIALLY_IMPLEMENTED**; accepted:false. Unaccepted dependencies: NSAI-060, NSAI-047.

Implemented/tested: Learning/governed proposals require independent review; paired holdout validator exists; training/execution stay off.

Next action: Persist observation/shadow/review/revision transitions, frozen paired trials, stale evidence refusal and reversible promotion.

- **UNVERIFIED** - Observation/candidate/shadow-evaluation/independent-review/revision transitions explicit Observed: Learning/governed proposals require independent review; paired holdout validator exists; training/execution stay off. Remaining: Persist observation/shadow/review/revision transitions, frozen paired trials, stale evidence refusal and reversible promotion.
- **UNVERIFIED** - paired frozen baseline/challenger and holdout isolation Observed: Learning/governed proposals require independent review; paired holdout validator exists; training/execution stay off. Remaining: Persist observation/shadow/review/revision transitions, frozen paired trials, stale evidence refusal and reversible promotion.
- **PARTIAL** - stale evidence denied Observed: Learning/governed proposals require independent review; paired holdout validator exists; training/execution stay off. Remaining: Persist observation/shadow/review/revision transitions, frozen paired trials, stale evidence refusal and reversible promotion.
- **UNVERIFIED** - promotion reversible Observed: Learning/governed proposals require independent review; paired holdout validator exists; training/execution stay off. Remaining: Persist observation/shadow/review/revision transitions, frozen paired trials, stale evidence refusal and reversible promotion.
- **CONFIRMED** - no training or generated execution enabled Observed: Learning/governed proposals require independent review; paired holdout validator exists; training/execution stay off. Remaining: Persist observation/shadow/review/revision transitions, frozen paired trials, stale evidence refusal and reversible promotion.

### NSAI-062 - Use strict data-only manifests and procedure proposals

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-061, NSAI-031.

Implemented/tested: Strict JSON rejects duplicate/deep/oversize/nonfinite input and executable/authority/credential proposals; no procedure dispatch.

Next action: Define finite per-procedure I/O/effects/tests/hashes, reject unknown/missing fields and prove no unsafe deserializer/executable interpretation.

- **PARTIAL** - Unknown fields, duplicate JSON keys, depth/size excess, nonfinite values, missing hashes and forged authority denied Observed: Strict JSON rejects duplicate/deep/oversize/nonfinite input and executable/authority/credential proposals; no procedure dispatch. Remaining: Define finite per-procedure I/O/effects/tests/hashes, reject unknown/missing fields and prove no unsafe deserializer/executable interpretation.
- **CONFIRMED** - no pickle/untrusted code Observed: Strict JSON rejects duplicate/deep/oversize/nonfinite input and executable/authority/credential proposals; no procedure dispatch. Remaining: Define finite per-procedure I/O/effects/tests/hashes, reject unknown/missing fields and prove no unsafe deserializer/executable interpretation.
- **PARTIAL** - procedures declare I/O/effects/tests but remain nonexecutable Observed: Strict JSON rejects duplicate/deep/oversize/nonfinite input and executable/authority/credential proposals; no procedure dispatch. Remaining: Define finite per-procedure I/O/effects/tests/hashes, reject unknown/missing fields and prove no unsafe deserializer/executable interpretation.

### NSAI-063 - Track scoped correction and outcome uncertainty

Status: **PARTIALLY_IMPLEMENTED**; accepted:false. Unaccepted dependencies: NSAI-061, NSAI-044.

Implemented/tested: Extraction-correction proposals and immutable independent reviews form candidates, not causal resolution.

Next action: Add response/source/claim linkage, reason taxonomy, dedupe, before/after generations and reviewed correction replay with unknown causes.

- **UNVERIFIED** - Response/source/claim IDs and bounded reason taxonomy Observed: Extraction-correction proposals and immutable independent reviews form candidates, not causal resolution. Remaining: Add response/source/claim linkage, reason taxonomy, dedupe, before/after generations and reviewed correction replay with unknown causes.
- **UNVERIFIED** - dedupe and before/after lineage Observed: Extraction-correction proposals and immutable independent reviews form candidates, not causal resolution. Remaining: Add response/source/claim linkage, reason taxonomy, dedupe, before/after generations and reviewed correction replay with unknown causes.
- **UNVERIFIED** - reviewer outcomes do not imply verified causal resolution Observed: Extraction-correction proposals and immutable independent reviews form candidates, not causal resolution. Remaining: Add response/source/claim linkage, reason taxonomy, dedupe, before/after generations and reviewed correction replay with unknown causes.
- **PARTIAL** - unknown causes remain unknown Observed: Extraction-correction proposals and immutable independent reviews form candidates, not causal resolution. Remaining: Add response/source/claim linkage, reason taxonomy, dedupe, before/after generations and reviewed correction replay with unknown causes.

### NSAI-064 - Complete local governance management controls

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-061, NSAI-046, NSAI-010.

Implemented/tested: Governed policy review now uses one transaction connection for source checks, decision and update, avoiding nested pool acquisition. Focused authority/integrity cases plus current31-case admin-stage/reviewer-apply pass.

Next action: Qualify broader concurrent approval/expiry/replay and production step-up/OIDC commissioning separately; local shared-role approvals are not enterprise identity.

- **PARTIAL** - Risk-tiered local role/action matrix Observed: Governed policy review now uses one transaction connection for source checks, decision and update, avoiding nested pool acquisition. Focused authority/integrity cases plus current31-case admin-stage/reviewer-apply pass. Remaining: Qualify broader concurrent approval/expiry/replay and production step-up/OIDC commissioning separately; local shared-role approvals are not enterprise identity.
- **PARTIAL** - actual actor/old-new policy revision/expiry/idempotency and independent approval for sensitive changes Observed: Governed policy review now uses one transaction connection for source checks, decision and update, avoiding nested pool acquisition. Focused authority/integrity cases plus current31-case admin-stage/reviewer-apply pass. Remaining: Qualify broader concurrent approval/expiry/replay and production step-up/OIDC commissioning separately; local shared-role approvals are not enterprise identity.
- **PARTIAL** - stale/forged/self approval rejected Observed: Governed policy review now uses one transaction connection for source checks, decision and update, avoiding nested pool acquisition. Focused authority/integrity cases plus current31-case admin-stage/reviewer-apply pass. Remaining: Qualify broader concurrent approval/expiry/replay and production step-up/OIDC commissioning separately; local shared-role approvals are not enterprise identity.
- **CONFIRMED** - natural language grants no authority Observed: Governed policy review now uses one transaction connection for source checks, decision and update, avoiding nested pool acquisition. Focused authority/integrity cases plus current31-case admin-stage/reviewer-apply pass. Remaining: Qualify broader concurrent approval/expiry/replay and production step-up/OIDC commissioning separately; local shared-role approvals are not enterprise identity.
- **CONFIRMED** - central remains disabled Observed: Governed policy review now uses one transaction connection for source checks, decision and update, avoiding nested pool acquisition. Focused authority/integrity cases plus current31-case admin-stage/reviewer-apply pass. Remaining: Qualify broader concurrent approval/expiry/replay and production step-up/OIDC commissioning separately; local shared-role approvals are not enterprise identity.

### NSAI-065 - Stage central authorization interfaces without activation

Status: **PARTIALLY_IMPLEMENTED**; accepted:false. Unaccepted dependencies: NSAI-064.

Implemented/tested: Data-only central config imports and live enabling are denied in app/typedDB; provider helper fails closed.

Next action: Specify actor/resource/policy/reason/expiry/revocation adapter schemas and stale/unavailable/malformed provider tests without activation.

- **PARTIAL** - Validated actor/resource/policy/reason/expiry/revocation contracts Observed: Data-only central config imports and live enabling are denied in app/typedDB; provider helper fails closed. Remaining: Specify actor/resource/policy/reason/expiry/revocation adapter schemas and stale/unavailable/malformed provider tests without activation.
- **PARTIAL** - malformed/unavailable/stale provider fails closed in isolated tests Observed: Data-only central config imports and live enabling are denied in app/typedDB; provider helper fails closed. Remaining: Specify actor/resource/policy/reason/expiry/revocation adapter schemas and stale/unavailable/malformed provider tests without activation.
- **CONFIRMED** - configuration imports data only Observed: Data-only central config imports and live enabling are denied in app/typedDB; provider helper fails closed. Remaining: Specify actor/resource/policy/reason/expiry/revocation adapter schemas and stale/unavailable/malformed provider tests without activation.
- **CONFIRMED** - all live central enable attempts denied Observed: Data-only central config imports and live enabling are denied in app/typedDB; provider helper fails closed. Remaining: Specify actor/resource/policy/reason/expiry/revocation adapter schemas and stale/unavailable/malformed provider tests without activation.

### NSAI-066 - Specify scoped integration secret lifecycle

Status: **PARTIALLY_IMPLEMENTED**; accepted:false. Unaccepted dependencies: NSAI-065, NSAI-008.

Implemented/tested: Parser/OCR/model secrets are scoped files and no external product connector is activated.

Next action: Specify integration expiry/revocation/rotation receipts, prove no global/plaintext fallback and test owned availability through rotation.

- **UNVERIFIED** - Dedicated scoped credentials, expiry/revocation/rotation receipt Observed: Parser/OCR/model secrets are scoped files and no external product connector is activated. Remaining: Specify integration expiry/revocation/rotation receipts, prove no global/plaintext fallback and test owned availability through rotation.
- **UNVERIFIED** - no global key or plaintext fallback Observed: Parser/OCR/model secrets are scoped files and no external product connector is activated. Remaining: Specify integration expiry/revocation/rotation receipts, prove no global/plaintext fallback and test owned availability through rotation.
- **CONFIRMED** - no new external connector activated Observed: Parser/OCR/model secrets are scoped files and no external product connector is activated. Remaining: Specify integration expiry/revocation/rotation receipts, prove no global/plaintext fallback and test owned availability through rotation.

### NSAI-067 - Render bounded accepted and withheld evidence traces

Status: **IMPLEMENTED_ACCEPTANCE_PENDING**; accepted:false. Unaccepted dependencies: NSAI-060, NSAI-030, NSAI-063.

Implemented/tested: Bounded inspectors show candidate/withheld/completeness/source identity and reviewer retrieves payload first; renderer cannot grant authority.

Next action: Bind final run/version/source/claim traces, reject mixed generations and only commission reviewed redacted formula-safe CSV if selected.

- **PARTIAL** - Stable run/version/source/claim identity Observed: Bounded inspectors show candidate/withheld/completeness/source identity and reviewer retrieves payload first; renderer cannot grant authority. Remaining: Bind final run/version/source/claim traces, reject mixed generations and only commission reviewed redacted formula-safe CSV if selected.
- **PARTIAL** - mismatched receipts never merged Observed: Bounded inspectors show candidate/withheld/completeness/source identity and reviewer retrieves payload first; renderer cannot grant authority. Remaining: Bind final run/version/source/claim traces, reject mixed generations and only commission reviewed redacted formula-safe CSV if selected.
- **PARTIAL** - approved/disputed/withheld/unsupported shown Observed: Bounded inspectors show candidate/withheld/completeness/source identity and reviewer retrieves payload first; renderer cannot grant authority. Remaining: Bind final run/version/source/claim traces, reject mixed generations and only commission reviewed redacted formula-safe CSV if selected.
- **PARTIAL** - optional CSV export formula-injection neutralized and redacted Observed: Bounded inspectors show candidate/withheld/completeness/source identity and reviewer retrieves payload first; renderer cannot grant authority. Remaining: Bind final run/version/source/claim traces, reject mixed generations and only commission reviewed redacted formula-safe CSV if selected.
- **CONFIRMED** - renderer cannot grant truth/authority Observed: Bounded inspectors show candidate/withheld/completeness/source identity and reviewer retrieves payload first; renderer cannot grant authority. Remaining: Bind final run/version/source/claim traces, reject mixed generations and only commission reviewed redacted formula-safe CSV if selected.

### NSAI-068 - Accept governed assembly and disabled central contracts

Status: **QUALIFICATION_PENDING**; accepted:false. Unaccepted dependencies: NSAI-062, NSAI-063, NSAI-064, NSAI-065, NSAI-066, NSAI-067.

Implemented/tested: Governed assembly, independent review and forbidden activation have owned DB/browser evidence.

Next action: Complete replay/promotion/rollback, scoped-secret lifecycle and every062-067 criterion before accepting this assembly gate.

- **PARTIAL** - Replay, promotion denial, rollback, action ownership, scoped key contracts and forbidden activation verified Observed: Governed assembly, independent review and forbidden activation have owned DB/browser evidence. Remaining: Complete replay/promotion/rollback, scoped-secret lifecycle and every062-067 criterion before accepting this assembly gate.
- **PARTIAL** - registry/graph/proposal existence never implies execution permission Observed: Governed assembly, independent review and forbidden activation have owned DB/browser evidence. Remaining: Complete replay/promotion/rollback, scoped-secret lifecycle and every062-067 criterion before accepting this assembly gate.

### NSAI-069 - Build independent source-bound transcript observations

Status: **SUPERSEDED_ISSUE_FLOW**; accepted:false. Unaccepted dependencies: NSAI-068.

Implemented/tested: Transcript product scope superseded: issue descriptions become exact source/revision/hash/locator engineering category and quantity candidates.

Next action: Qualify original engineering offset/category/unknown/spoof/provenance cases; actual speaker/time/transcript handling is not a current requirement.

- **UNVERIFIED** - Original synthetic turns with speaker/time/offset/session manifest Observed: Transcript product scope superseded: issue descriptions become exact source/revision/hash/locator engineering category and quantity candidates. Remaining: Qualify original engineering offset/category/unknown/spoof/provenance cases; actual speaker/time/transcript handling is not a current requirement.
- **UNVERIFIED** - duplicate/reordered/unknown-speaker/spoof cases Observed: Transcript product scope superseded: issue descriptions become exact source/revision/hash/locator engineering category and quantity candidates. Remaining: Qualify original engineering offset/category/unknown/spoof/provenance cases; actual speaker/time/transcript handling is not a current requirement.
- **UNVERIFIED** - reversible aliases are proposals Observed: Transcript product scope superseded: issue descriptions become exact source/revision/hash/locator engineering category and quantity candidates. Remaining: Qualify original engineering offset/category/unknown/spoof/provenance cases; actual speaker/time/transcript handling is not a current requirement.
- **UNVERIFIED** - no upstream source, dictionary or corporate transcript copied Observed: Transcript product scope superseded: issue descriptions become exact source/revision/hash/locator engineering category and quantity candidates. Remaining: Qualify original engineering offset/category/unknown/spoof/provenance cases; actual speaker/time/transcript handling is not a current requirement.

Replacement engineering criteria (user steering):

- **PARTIAL** - Exact document/revision/hash/locator binds authorized original engineering observations/quantities. Remaining: Qualify original engineering offset/category/unknown/spoof/provenance cases; actual speaker/time/transcript handling is not a current requirement.
- **PARTIAL** - Symptom/condition/measurement/hypothesis/check/action/outcome/negation remain candidate/unknown; graph edges are bounded review order, not causal diagnosis. Remaining: Qualify original engineering offset/category/unknown/spoof/provenance cases; actual speaker/time/transcript handling is not a current requirement.
- **PARTIAL** - Original engineering holdout/replay/uncertainty/false-link cases are qualified without corporate dictionaries or actual speaker transcripts. Remaining: Qualify original engineering offset/category/unknown/spoof/provenance cases; actual speaker/time/transcript handling is not a current requirement.

### NSAI-070 - Link questions, measurements, actions and outcomes conservatively

Status: **SUPERSEDED_ISSUE_FLOW**; accepted:false. Unaccepted dependencies: NSAI-069, NSAI-034.

Implemented/tested: Engineering separates symptoms/conditions/observations/hypotheses/checks/actions/outcomes/negation; instrument/location stay unknown and edges mean review order.

Next action: Measure original engineering category/quantity associations and false links; specifications are not measurements and edges are not causal diagnosis.

- **UNVERIFIED** - Assertion/question/negated/historical/conditional/action/outcome states separated Observed: Engineering separates symptoms/conditions/observations/hypotheses/checks/actions/outcomes/negation; instrument/location stay unknown and edges mean review order. Remaining: Measure original engineering category/quantity associations and false links; specifications are not measurements and edges are not causal diagnosis.
- **UNVERIFIED** - quantities include instrument/location/conditions Observed: Engineering separates symptoms/conditions/observations/hypotheses/checks/actions/outcomes/negation; instrument/location stay unknown and edges mean review order. Remaining: Measure original engineering category/quantity associations and false links; specifications are not measurements and edges are not causal diagnosis.
- **UNVERIFIED** - request-answer links measured Observed: Engineering separates symptoms/conditions/observations/hypotheses/checks/actions/outcomes/negation; instrument/location stay unknown and edges mean review order. Remaining: Measure original engineering category/quantity associations and false links; specifications are not measurements and edges are not causal diagnosis.
- **UNVERIFIED** - manual specification not treated as observed measurement Observed: Engineering separates symptoms/conditions/observations/hypotheses/checks/actions/outcomes/negation; instrument/location stay unknown and edges mean review order. Remaining: Measure original engineering category/quantity associations and false links; specifications are not measurements and edges are not causal diagnosis.

Replacement engineering criteria (user steering):

- **PARTIAL** - Exact document/revision/hash/locator binds authorized original engineering observations/quantities. Remaining: Measure original engineering category/quantity associations and false links; specifications are not measurements and edges are not causal diagnosis.
- **PARTIAL** - Symptom/condition/measurement/hypothesis/check/action/outcome/negation remain candidate/unknown; graph edges are bounded review order, not causal diagnosis. Remaining: Measure original engineering category/quantity associations and false links; specifications are not measurements and edges are not causal diagnosis.
- **PARTIAL** - Original engineering holdout/replay/uncertainty/false-link cases are qualified without corporate dictionaries or actual speaker transcripts. Remaining: Measure original engineering category/quantity associations and false links; specifications are not measurements and edges are not causal diagnosis.

### NSAI-071 - Qualify transcript replay and withheld reports

Status: **SUPERSEDED_ISSUE_FLOW**; accepted:false. Unaccepted dependencies: NSAI-070, NSAI-067.

Implemented/tested: Issue-flow reports preserve candidate/withheld/source identities and bounded acyclic edges; actual transcript API removed.

Next action: Build engineering source-family/revision replay, corrected-issue generation invalidation and uncertainty/refusal holdouts without transcript sessions.

- **UNVERIFIED** - Source-family/revision/session split, deterministic semantic corpus signatures, accepted/withheld/unsupported ledger, corrected-turn replay and uncertainty metrics Observed: Issue-flow reports preserve candidate/withheld/source identities and bounded acyclic edges; actual transcript API removed. Remaining: Build engineering source-family/revision replay, corrected-issue generation invalidation and uncertainty/refusal holdouts without transcript sessions.
- **UNVERIFIED** - report existence alone fails certification Observed: Issue-flow reports preserve candidate/withheld/source identities and bounded acyclic edges; actual transcript API removed. Remaining: Build engineering source-family/revision replay, corrected-issue generation invalidation and uncertainty/refusal holdouts without transcript sessions.

Replacement engineering criteria (user steering):

- **PARTIAL** - Exact document/revision/hash/locator binds authorized original engineering observations/quantities. Remaining: Build engineering source-family/revision replay, corrected-issue generation invalidation and uncertainty/refusal holdouts without transcript sessions.
- **PARTIAL** - Symptom/condition/measurement/hypothesis/check/action/outcome/negation remain candidate/unknown; graph edges are bounded review order, not causal diagnosis. Remaining: Build engineering source-family/revision replay, corrected-issue generation invalidation and uncertainty/refusal holdouts without transcript sessions.
- **PARTIAL** - Original engineering holdout/replay/uncertainty/false-link cases are qualified without corporate dictionaries or actual speaker transcripts. Remaining: Build engineering source-family/revision replay, corrected-issue generation invalidation and uncertainty/refusal holdouts without transcript sessions.

### NSAI-072 - Define operational metrics before business conclusions

Status: **PARTIALLY_IMPLEMENTED**; accepted:false. Unaccepted dependencies: NSAI-068, NSAI-046.

Implemented/tested: Finite source/cohort/grain/version/freshness ratios return unknown for zero/stale/incompatible inputs and deny causality.

Next action: Persist owner/window/exclusion/duplicate/missingness definitions and qualify real eligible task denominators before reporting.

- **UNVERIFIED** - Metric owner/version/grain/numerator/denominator/window/freshness/exclusions explicit Observed: Finite source/cohort/grain/version/freshness ratios return unknown for zero/stale/incompatible inputs and deny causality. Remaining: Persist owner/window/exclusion/duplicate/missingness definitions and qualify real eligible task denominators before reporting.
- **PARTIAL** - duplicates/missing/stale/zero denominator produce unknown or failure Observed: Finite source/cohort/grain/version/freshness ratios return unknown for zero/stale/incompatible inputs and deny causality. Remaining: Persist owner/window/exclusion/duplicate/missingness definitions and qualify real eligible task denominators before reporting.
- **UNVERIFIED** - utilization and throughput use actual task cohorts Observed: Finite source/cohort/grain/version/freshness ratios return unknown for zero/stale/incompatible inputs and deny causality. Remaining: Persist owner/window/exclusion/duplicate/missingness definitions and qualify real eligible task denominators before reporting.

### NSAI-073 - Distinguish continuation, recurrence and new tasks

Status: **PARTIALLY_IMPLEMENTED**; accepted:false. Unaccepted dependencies: NSAI-069, NSAI-044.

Implemented/tested: Actor-owned conversation continuation and request identity exist without inferred corporate identities.

Next action: Implement source-bound continuation/recurrence/new-task ambiguity confirmation and measured false-association precision/recall.

- **UNVERIFIED** - Actor-owned source-bound linkage with ambiguity/unknown states and explicit confirmation Observed: Actor-owned conversation continuation and request identity exist without inferred corporate identities. Remaining: Implement source-bound continuation/recurrence/new-task ambiguity confirmation and measured false-association precision/recall.
- **UNVERIFIED** - false-association precision/recall measured Observed: Actor-owned conversation continuation and request identity exist without inferred corporate identities. Remaining: Implement source-bound continuation/recurrence/new-task ambiguity confirmation and measured false-association precision/recall.
- **PARTIAL** - no inferred corporate/customer identity Observed: Actor-owned conversation continuation and request identity exist without inferred corporate identities. Remaining: Implement source-bound continuation/recurrence/new-task ambiguity confirmation and measured false-association precision/recall.

### NSAI-074 - Account for local resource budgets and usage

Status: **PARTIALLY_IMPLEMENTED**; accepted:false. Unaccepted dependencies: NSAI-015, NSAI-072.

Implemented/tested: Durable UTC attempt/settlement/invocation retries and pure immutable token/time-budget contracts exist.

Next action: Persist ledger CAS, crash/day rollover/expiry reconciliation and actual tokens/time; versioned Decimal currency pricing stays staged.

- **PARTIAL** - Durable UTC reservation/settlement/expiry, retries/day rollover/crash reconciled Observed: Durable UTC attempt/settlement/invocation retries and pure immutable token/time-budget contracts exist. Remaining: Persist ledger CAS, crash/day rollover/expiry reconciliation and actual tokens/time; versioned Decimal currency pricing stays staged.
- **PARTIAL** - actual attempts/tokens/time recorded Observed: Durable UTC attempt/settlement/invocation retries and pure immutable token/time-budget contracts exist. Remaining: Persist ledger CAS, crash/day rollover/expiry reconciliation and actual tokens/time; versioned Decimal currency pricing stays staged.
- **PARTIAL** - no guessed currency cost Observed: Durable UTC attempt/settlement/invocation retries and pure immutable token/time-budget contracts exist. Remaining: Persist ledger CAS, crash/day rollover/expiry reconciliation and actual tokens/time; versioned Decimal currency pricing stays staged.
- **PARTIAL** - pricing contract finite Decimal/version/currency staged Observed: Durable UTC attempt/settlement/invocation retries and pure immutable token/time-budget contracts exist. Remaining: Persist ledger CAS, crash/day rollover/expiry reconciliation and actual tokens/time; versioned Decimal currency pricing stays staged.

### NSAI-075 - Report reviewed outcomes and hypothetical scenarios honestly

Status: **PARTIALLY_IMPLEMENTED**; accepted:false. Unaccepted dependencies: NSAI-074, NSAI-072, NSAI-063.

Implemented/tested: Unknown denominators and causal-attribution denial are explicit; engineering outcomes stay reported-unverified.

Next action: Build real reviewed outcome cohorts with attribution and labeled fixed-variable assumptions; no fabricated zero/success/ROI.

- **UNVERIFIED** - Real eligible outcome denominator and attribution needed Observed: Unknown denominators and causal-attribution denial are explicit; engineering outcomes stay reported-unverified. Remaining: Build real reviewed outcome cohorts with attribution and labeled fixed-variable assumptions; no fabricated zero/success/ROI.
- **PARTIAL** - unknown/zero denominator never manufactured as zero Observed: Unknown denominators and causal-attribution denial are explicit; engineering outcomes stay reported-unverified. Remaining: Build real reviewed outcome cohorts with attribution and labeled fixed-variable assumptions; no fabricated zero/success/ROI.
- **PARTIAL** - no model success equated to verified resolution/ROI/causality Observed: Unknown denominators and causal-attribution denial are explicit; engineering outcomes stay reported-unverified. Remaining: Build real reviewed outcome cohorts with attribution and labeled fixed-variable assumptions; no fabricated zero/success/ROI.
- **UNVERIFIED** - fixed-variable scenarios labeled assumptions Observed: Unknown denominators and causal-attribution denial are explicit; engineering outcomes stay reported-unverified. Remaining: Build real reviewed outcome cohorts with attribution and labeled fixed-variable assumptions; no fabricated zero/success/ROI.

### NSAI-076 - Qualify optional transcript and operational reporting

Status: **SUPERSEDED_ISSUE_FLOW**; accepted:false. Unaccepted dependencies: NSAI-071, NSAI-073, NSAI-075.

Implemented/tested: Engineering issue structure is the selected workflow; transcript helper is dormant and its product route is removed.

Next action: Qualify selected engineering lineage/replay/holdout utility and needed metrics; defer unselected transcript/enterprise reporting.

- **UNVERIFIED** - Optional modules off until a selected workflow Observed: Engineering issue structure is the selected workflow; transcript helper is dormant and its product route is removed. Remaining: Qualify selected engineering lineage/replay/holdout utility and needed metrics; defer unselected transcript/enterprise reporting.
- **UNVERIFIED** - independently written fixtures and measured lineage Observed: Engineering issue structure is the selected workflow; transcript helper is dormant and its product route is removed. Remaining: Qualify selected engineering lineage/replay/holdout utility and needed metrics; defer unselected transcript/enterprise reporting.
- **UNVERIFIED** - useful original local capabilities accepted without adopting corporate terminology or full enterprise integrations Observed: Engineering issue structure is the selected workflow; transcript helper is dormant and its product route is removed. Remaining: Qualify selected engineering lineage/replay/holdout utility and needed metrics; defer unselected transcript/enterprise reporting.

Replacement engineering criteria (user steering):

- **PARTIAL** - Exact document/revision/hash/locator binds authorized original engineering observations/quantities. Remaining: Qualify selected engineering lineage/replay/holdout utility and needed metrics; defer unselected transcript/enterprise reporting.
- **PARTIAL** - Symptom/condition/measurement/hypothesis/check/action/outcome/negation remain candidate/unknown; graph edges are bounded review order, not causal diagnosis. Remaining: Qualify selected engineering lineage/replay/holdout utility and needed metrics; defer unselected transcript/enterprise reporting.
- **PARTIAL** - Original engineering holdout/replay/uncertainty/false-link cases are qualified without corporate dictionaries or actual speaker transcripts. Remaining: Qualify selected engineering lineage/replay/holdout utility and needed metrics; defer unselected transcript/enterprise reporting.

### NSAI-077 - Resolve dedicated security scan worker prerequisite

Status: **BLOCKED**; accepted:false. Unaccepted dependencies: none.

Implemented/tested: Deep Scan failed before launch with the managed read-only worker profile error; no scanID/report exists.

Next action: Supply an authorized managed profile externally, preserve failure and run the real tool without weakening global permissions.

- **UNVERIFIED** - Managed read-only filesystem permission profile available Observed: Deep Scan failed before launch with the managed read-only worker profile error; no scanID/report exists. Remaining: Supply an authorized managed profile externally, preserve failure and run the real tool without weakening global permissions.
- **CONFIRMED** - actual tool error retained: Deep Scan cannot safely start a read-only worker: the parent must provide a managed filesystem permission profile Observed: Deep Scan failed before launch with the managed read-only worker profile error; no scanID/report exists. Remaining: Supply an authorized managed profile externally, preserve failure and run the real tool without weakening global permissions.
- **CONFIRMED** - no global permission weakening or scan PASS invented Observed: Deep Scan failed before launch with the managed read-only worker profile error; no scanID/report exists. Remaining: Supply an authorized managed profile externally, preserve failure and run the real tool without weakening global permissions.

### NSAI-078 - Run independent security qualification and revalidate fixes

Status: **BLOCKED**; accepted:false. Unaccepted dependencies: NSAI-077, NSAI-068.

Implemented/tested: Adversarial engineering review is separate; dedicated multi-pass security qualification has not run.

Next action: After077 run a real frozen-source deep scan, validate/fix every finding and link runtime tests; no security-ready claim while blocked.

- **UNVERIFIED** - Actual successful multi-pass scan artifacts bound to final immutable source Observed: Adversarial engineering review is separate; dedicated multi-pass security qualification has not run. Remaining: After077 run a real frozen-source deep scan, validate/fix every finding and link runtime tests; no security-ready claim while blocked.
- **UNVERIFIED** - findings independently validated, tracked in local backlog and addressed Observed: Adversarial engineering review is separate; dedicated multi-pass security qualification has not run. Remaining: After077 run a real frozen-source deep scan, validate/fix every finding and link runtime tests; no security-ready claim while blocked.
- **UNVERIFIED** - required runtime adversarial tests separately linked Observed: Adversarial engineering review is separate; dedicated multi-pass security qualification has not run. Remaining: After077 run a real frozen-source deep scan, validate/fix every finding and link runtime tests; no security-ready claim while blocked.
- **CONFIRMED** - blocked/missing scan prohibits security-ready claim Observed: Adversarial engineering review is separate; dedicated multi-pass security qualification has not run. Remaining: After077 run a real frozen-source deep scan, validate/fix every finding and link runtime tests; no security-ready claim while blocked.

### NSAI-079 - Close remaining adversarial, branch and load coverage gaps

Status: **QUALIFICATION_PENDING**; accepted:false. Unaccepted dependencies: NSAI-032.

Implemented/tested: Final487 unit testsPASS2knownwarnings;399 functions180 observed entries/source-stable. Current 0df31stack,50mock-model integration,57image bytes and21recovery cases provide separate runtime proof.

Next action: Qualify unobserved functions plus branch/property/fuzz/sustained/max-corpus/a11y coverage; entry observations are not correctness/branch/full-function certification.

- **PARTIAL** - All active functions/routes/actions have positive/negative contracts Observed: Final487 unit testsPASS2knownwarnings;399 functions180 observed entries/source-stable. Current 0df31stack,50mock-model integration,57image bytes and21recovery cases provide separate runtime proof. Remaining: Qualify unobserved functions plus branch/property/fuzz/sustained/max-corpus/a11y coverage; entry observations are not correctness/branch/full-function certification.
- **PARTIAL** - property/fuzz parser/protocol/quantity tests, sustained load, full browser/a11y and growing corpus checked Observed: Final487 unit testsPASS2knownwarnings;399 functions180 observed entries/source-stable. Current 0df31stack,50mock-model integration,57image bytes and21recovery cases provide separate runtime proof. Remaining: Qualify unobserved functions plus branch/property/fuzz/sustained/max-corpus/a11y coverage; entry observations are not correctness/branch/full-function certification.
- **CONFIRMED** - disabled Evolus not invoked Observed: Final487 unit testsPASS2knownwarnings;399 functions180 observed entries/source-stable. Current 0df31stack,50mock-model integration,57image bytes and21recovery cases provide separate runtime proof. Remaining: Qualify unobserved functions plus branch/property/fuzz/sustained/max-corpus/a11y coverage; entry observations are not correctness/branch/full-function certification.
- **CONFIRMED** - coverage limitations retained Observed: Final487 unit testsPASS2knownwarnings;399 functions180 observed entries/source-stable. Current 0df31stack,50mock-model integration,57image bytes and21recovery cases provide separate runtime proof. Remaining: Qualify unobserved functions plus branch/property/fuzz/sustained/max-corpus/a11y coverage; entry observations are not correctness/branch/full-function certification.

### NSAI-080 - Validate the actual submission archive

Status: **QUALIFICATION_PENDING**; accepted:false. Unaccepted dependencies: NSAI-031, NSAI-030, NSAI-047.

Implemented/tested: Exact allowlist/member-hash archives and exclusive finalization have disposable tests; real source archive/publication not performed.

Next action: After exact source/model/dependency/privacy/license disposition, build/reopen/review intended bytes and align all claims with receipts.

- **PARTIAL** - Exact allowlisted members with digest manifest, secret/privacy/license scans and member review Observed: Exact allowlist/member-hash archives and exclusive finalization have disposable tests; real source archive/publication not performed. Remaining: After exact source/model/dependency/privacy/license disposition, build/reopen/review intended bytes and align all claims with receipts.
- **PARTIAL** - excluded private corpus/backups/keys/models Observed: Exact allowlist/member-hash archives and exclusive finalization have disposable tests; real source archive/publication not performed. Remaining: After exact source/model/dependency/privacy/license disposition, build/reopen/review intended bytes and align all claims with receipts.
- **PARTIAL** - claims match evidence Observed: Exact allowlist/member-hash archives and exclusive finalization have disposable tests; real source archive/publication not performed. Remaining: After exact source/model/dependency/privacy/license disposition, build/reopen/review intended bytes and align all claims with receipts.
- **CONFIRMED** - no automatic publication Observed: Exact allowlist/member-hash archives and exclusive finalization have disposable tests; real source archive/publication not performed. Remaining: After exact source/model/dependency/privacy/license disposition, build/reopen/review intended bytes and align all claims with receipts.

### NSAI-081 - Reconcile guides and current capability statements

Status: **QUALIFICATION_PENDING**; accepted:false. Unaccepted dependencies: NSAI-005, NSAI-047, NSAI-080.

Implemented/tested: Provenance/registry separate references, licensed PDF.js, unreviewed model and candidate/disabled features; ledger separates testing/deployment.

Next action: Reconcile every root guide/launcher/example with CPU workflow and current scope; do not turn historicalPASS into release clearance.

- **PARTIAL** - One supported workflow Observed: Provenance/registry separate references, licensed PDF.js, unreviewed model and candidate/disabled features; ledger separates testing/deployment. Remaining: Reconcile every root guide/launcher/example with CPU workflow and current scope; do not turn historicalPASS into release clearance.
- **PARTIAL** - old baseline PASS distinguished from fresh qualification Observed: Provenance/registry separate references, licensed PDF.js, unreviewed model and candidate/disabled features; ledger separates testing/deployment. Remaining: Reconcile every root guide/launcher/example with CPU workflow and current scope; do not turn historicalPASS into release clearance.
- **CONFIRMED** - clean-room/source-origin wording truthful Observed: Provenance/registry separate references, licensed PDF.js, unreviewed model and candidate/disabled features; ledger separates testing/deployment. Remaining: Reconcile every root guide/launcher/example with CPU workflow and current scope; do not turn historicalPASS into release clearance.
- **PARTIAL** - PDF/OCR/central/AMD capability states accurate Observed: Provenance/registry separate references, licensed PDF.js, unreviewed model and candidate/disabled features; ledger separates testing/deployment. Remaining: Reconcile every root guide/launcher/example with CPU workflow and current scope; do not turn historicalPASS into release clearance.
- **CONFIRMED** - testing/evidence has its own section Observed: Provenance/registry separate references, licensed PDF.js, unreviewed model and candidate/disabled features; ledger separates testing/deployment. Remaining: Reconcile every root guide/launcher/example with CPU workflow and current scope; do not turn historicalPASS into release clearance.

### NSAI-082 - Rehearse controlled CPU deployment and submission readiness

Status: **QUALIFICATION_PENDING**; accepted:false. Unaccepted dependencies: NSAI-078, NSAI-079, NSAI-080, NSAI-081, NSAI-025, NSAI-059, NSAI-068.

Implemented/tested: Owned26-case stack, immutable images and distinct testing/restore/model evidence exist; production release is not commissioned.

Next action: Accept required dependencies, compatible rollback/upgrade and fresh security/source-image/archive gates before CPU release; no publication/AMD/central activation.

- **CONFIRMED** - Tests/evidence reviewed separately Observed: Owned26-case stack, immutable images and distinct testing/restore/model evidence exist; production release is not commissioned. Remaining: Accept required dependencies, compatible rollback/upgrade and fresh security/source-image/archive gates before CPU release; no publication/AMD/central activation.
- **PARTIAL** - immutable image/config, backup, migration plan and rollback rehearsed Observed: Owned26-case stack, immutable images and distinct testing/restore/model evidence exist; production release is not commissioned. Remaining: Accept required dependencies, compatible rollback/upgrade and fresh security/source-image/archive gates before CPU release; no publication/AMD/central activation.
- **PARTIAL** - deploy only accepted CPU release Observed: Owned26-case stack, immutable images and distinct testing/restore/model evidence exist; production release is not commissioned. Remaining: Accept required dependencies, compatible rollback/upgrade and fresh security/source-image/archive gates before CPU release; no publication/AMD/central activation.
- **PARTIAL** - post-deploy source/image binding and smoke checks Observed: Owned26-case stack, immutable images and distinct testing/restore/model evidence exist; production release is not commissioned. Remaining: Accept required dependencies, compatible rollback/upgrade and fresh security/source-image/archive gates before CPU release; no publication/AMD/central activation.
- **CONFIRMED** - unresolved required findings block release Observed: Owned26-case stack, immutable images and distinct testing/restore/model evidence exist; production release is not commissioned. Remaining: Accept required dependencies, compatible rollback/upgrade and fresh security/source-image/archive gates before CPU release; no publication/AMD/central activation.

### NSAI-083 - Disposition unqualified providers and accelerator profiles

Status: **DESIGN_ONLY**; accepted:false. Unaccepted dependencies: NSAI-082.

Implemented/tested: Ollama/accelerators stay outside CPU baseline; tokenizer admits qualified localCPU adapters only.

Next action: Future provider requires pinned image/model/license/hostTLSegress and own matched quality/security/cost/rollback plus explicit selection.

- **CONFIRMED** - Keep inactive Observed: Ollama/accelerators stay outside CPU baseline; tokenizer admits qualified localCPU adapters only. Remaining: Future provider requires pinned image/model/license/hostTLSegress and own matched quality/security/cost/rollback plus explicit selection.
- **UNVERIFIED** - future selected provider needs pinned image/model, host/TLS/egress policy, license and own quality/security/cost benchmark Observed: Ollama/accelerators stay outside CPU baseline; tokenizer admits qualified localCPU adapters only. Remaining: Future provider requires pinned image/model/license/hostTLSegress and own matched quality/security/cost/rollback plus explicit selection.
- **CONFIRMED** - latest/outbound profiles never silently join CPU baseline Observed: Ollama/accelerators stay outside CPU baseline; tokenizer admits qualified localCPU adapters only. Remaining: Future provider requires pinned image/model/license/hostTLSegress and own matched quality/security/cost/rollback plus explicit selection.

### NSAI-084 - Record deferred enterprise features and rejected transplantation

Status: **DESIGN_ONLY**; accepted:false. Unaccepted dependencies: NSAI-068.

Implemented/tested: Voice/STT/CRM/cloud/device/training/full runtimes/hostile execution and enterprise transplantation are excluded now.

Next action: Future selected workflow needs independent implementation/data/rights/security and activation review; no corporate source/assets/rules adoption.

- **CONFIRMED** - Voice/STT/CRM/cloud/device/SCORM/quizzes/training/full PX fabric/full enterprise diagnostics/hostile-code execution excluded now Observed: Voice/STT/CRM/cloud/device/training/full runtimes/hostile execution and enterprise transplantation are excluded now. Remaining: Future selected workflow needs independent implementation/data/rights/security and activation review; no corporate source/assets/rules adoption.
- **UNVERIFIED** - future workflow and independent data/licensing/security gates required Observed: Voice/STT/CRM/cloud/device/training/full runtimes/hostile execution and enterprise transplantation are excluded now. Remaining: Future selected workflow needs independent implementation/data/rights/security and activation review; no corporate source/assets/rules adoption.
- **CONFIRMED** - corporate source/assets/rules never adopted Observed: Voice/STT/CRM/cloud/device/training/full runtimes/hostile execution and enterprise transplantation are excluded now. Remaining: Future selected workflow needs independent implementation/data/rights/security and activation review; no corporate source/assets/rules adoption.

### NSAI-085 - Define future central identity commissioning prerequisites

Status: **DESIGN_ONLY**; accepted:false. Unaccepted dependencies: NSAI-065, NSAI-082.

Implemented/tested: OIDC/TLS/individual identity/tenants/revocation/CSRF/external anchor are future requirements; current central enabling denied.

Next action: Commission those isolated identity/control proofs only after stable release and explicit activation; shared role tokens are not production identity.

- **UNVERIFIED** - OIDC/TLS/individual identity/tenant isolation/revocation/CSRF cookie policy/external audit anchor design and isolated evidence required Observed: OIDC/TLS/individual identity/tenants/revocation/CSRF/external anchor are future requirements; current central enabling denied. Remaining: Commission those isolated identity/control proofs only after stable release and explicit activation; shared role tokens are not production identity.
- **CONFIRMED** - current enable remains denied Observed: OIDC/TLS/individual identity/tenants/revocation/CSRF/external anchor are future requirements; current central enabling denied. Remaining: Commission those isolated identity/control proofs only after stable release and explicit activation; shared role tokens are not production identity.
- **CONFIRMED** - later activation needs explicit user instruction Observed: OIDC/TLS/individual identity/tenants/revocation/CSRF/external anchor are future requirements; current central enabling denied. Remaining: Commission those isolated identity/control proofs only after stable release and explicit activation; shared role tokens are not production identity.

### NSAI-086 - Define later AMD and Evolus commissioning boundary

Status: **DESIGN_ONLY**; accepted:false. Unaccepted dependencies: NSAI-083, NSAI-082.

Implemented/tested: AMD/Evolus hardware/external workflow remain deferred; target-directory name grants no activation.

Next action: After local gates and explicit instruction select workload/hardware/protocol/rights, matched benchmark and rollback; no AMD/Evolus work now.

- **CONFIRMED** - No AMD changes or external workflows now Observed: AMD/Evolus hardware/external workflow remain deferred; target-directory name grants no activation. Remaining: After local gates and explicit instruction select workload/hardware/protocol/rights, matched benchmark and rollback; no AMD/Evolus work now.
- **UNVERIFIED** - choose real workload after local gates, validate hardware/protocol/rights, measure matched workload and rollback, obtain explicit activation instruction Observed: AMD/Evolus hardware/external workflow remain deferred; target-directory name grants no activation. Remaining: After local gates and explicit instruction select workload/hardware/protocol/rights, matched benchmark and rollback; no AMD/Evolus work now.
- **UNVERIFIED** - qualify optional local modules only when needed by the selected workload Observed: AMD/Evolus hardware/external workflow remain deferred; target-directory name grants no activation. Remaining: After local gates and explicit instruction select workload/hardware/protocol/rights, matched benchmark and rollback; no AMD/Evolus work now.

### NSAI-087 - Qualify optional local semantic retrieval generations

Status: **DESIGN_ONLY**; accepted:false. Unaccepted dependencies: NSAI-049, NSAI-039, NSAI-061.

Implemented/tested: Semantic retrieval is staged and lexical rollback stays active; no unapproved embedding download/provider activation.

Next action: Future exact model/tokenizer/license/index generation needs lexical-versus-hybrid source-family quality/resource shadow trials and rollback.

- **UNVERIFIED** - Model/tokenizer/license/hash identity bound to index Observed: Semantic retrieval is staged and lexical rollback stays active; no unapproved embedding download/provider activation. Remaining: Future exact model/tokenizer/license/index generation needs lexical-versus-hybrid source-family quality/resource shadow trials and rollback.
- **UNVERIFIED** - scoped source-family holdout compares lexical versus hybrid Recall@k/MRR/support/refusal and resource cost Observed: Semantic retrieval is staged and lexical rollback stays active; no unapproved embedding download/provider activation. Remaining: Future exact model/tokenizer/license/index generation needs lexical-versus-hybrid source-family quality/resource shadow trials and rollback.
- **UNVERIFIED** - shadow validation before explicit activation Observed: Semantic retrieval is staged and lexical rollback stays active; no unapproved embedding download/provider activation. Remaining: Future exact model/tokenizer/license/index generation needs lexical-versus-hybrid source-family quality/resource shadow trials and rollback.
- **UNVERIFIED** - rollback to lexical verified Observed: Semantic retrieval is staged and lexical rollback stays active; no unapproved embedding download/provider activation. Remaining: Future exact model/tokenizer/license/index generation needs lexical-versus-hybrid source-family quality/resource shadow trials and rollback.
- **CONFIRMED** - no unapproved download or provider fallback Observed: Semantic retrieval is staged and lexical rollback stays active; no unapproved embedding download/provider activation. Remaining: Future exact model/tokenizer/license/index generation needs lexical-versus-hybrid source-family quality/resource shadow trials and rollback.

### NSAI-088 - Specify valid-time and observation-time memory queries

Status: **DESIGN_ONLY**; accepted:false. Unaccepted dependencies: NSAI-036, NSAI-039, NSAI-034.

Implemented/tested: Immutable source/review history remains; general bitemporal queries are not commissioned.

Next action: Specify valid versus observed time/conditions and test stale historical oracles against current events; abstain unsupported queries without parallel authority.

- **UNVERIFIED** - Historical validity and observation time separated Observed: Immutable source/review history remains; general bitemporal queries are not commissioned. Remaining: Specify valid versus observed time/conditions and test stale historical oracles against current events; abstain unsupported queries without parallel authority.
- **UNVERIFIED** - revisions/conditions and stale records tested Observed: Immutable source/review history remains; general bitemporal queries are not commissioned. Remaining: Specify valid versus observed time/conditions and test stale historical oracles against current events; abstain unsupported queries without parallel authority.
- **UNVERIFIED** - optional bitemporal projection uses current immutable events rather than parallel authority Observed: Immutable source/review history remains; general bitemporal queries are not commissioned. Remaining: Specify valid versus observed time/conditions and test stale historical oracles against current events; abstain unsupported queries without parallel authority.
- **UNVERIFIED** - unsupported historical query abstains Observed: Immutable source/review history remains; general bitemporal queries are not commissioned. Remaining: Specify valid versus observed time/conditions and test stale historical oracles against current events; abstain unsupported queries without parallel authority.

### NSAI-089 - Define future independent audit anchoring

Status: **DESIGN_ONLY**; accepted:false. Unaccepted dependencies: NSAI-085, NSAI-067.

Implemented/tested: Audit is an unsigned localSHA256 chain; no independent signer/key/anchor is activated.

Next action: Future source-bound export/verifier/trust/rotation/revocation needs explicit key/external-write commissioning; local chain is not signed proof.

- **CONFIRMED** - Local SHA256 chain never called externally signed proof Observed: Audit is an unsigned localSHA256 chain; no independent signer/key/anchor is activated. Remaining: Future source-bound export/verifier/trust/rotation/revocation needs explicit key/external-write commissioning; local chain is not signed proof.
- **UNVERIFIED** - source-bound export and verifier/key-rotation/trust/revocation contract specified Observed: Audit is an unsigned localSHA256 chain; no independent signer/key/anchor is activated. Remaining: Future source-bound export/verifier/trust/rotation/revocation needs explicit key/external-write commissioning; local chain is not signed proof.
- **CONFIRMED** - future signer/anchor commissioning separately authorized Observed: Audit is an unsigned localSHA256 chain; no independent signer/key/anchor is activated. Remaining: Future source-bound export/verifier/trust/rotation/revocation needs explicit key/external-write commissioning; local chain is not signed proof.
- **CONFIRMED** - no key generation, external write or activation now Observed: Audit is an unsigned localSHA256 chain; no independent signer/key/anchor is activated. Remaining: Future source-bound export/verifier/trust/rotation/revocation needs explicit key/external-write commissioning; local chain is not signed proof.
