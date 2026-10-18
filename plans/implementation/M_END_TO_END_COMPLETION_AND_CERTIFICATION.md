# End-to-end completion and certification plan

Planning date: 2026-10-15. Status: **IN PROGRESS; system not certified; rollout not ready**.

Execution evidence and current candidate status are maintained in
[research workspace progress](../../docs/implementation/RESEARCH_WORKSPACE_PROGRESS.md).
The starting-state section below is the historical planning baseline, not the
current implementation inventory. Work continues through the remaining packages;
a scoped passing batch does not close this plan.

User objective: finish and repair the complete UI-to-backend system, demonstrate that
it runs correctly, and obtain scoped independent acceptance **before** preparing an
Evolus or AMD rollout. This document plans that work; it does not execute a deployment.

Data preservation is mandatory throughout implementation and acceptance: see the
[data preservation contract](../../docs/implementation/DATA_PRESERVATION_ACCEPTANCE.md).
Original integrity alone does not establish complete derived content or recoverability.

## Completion contract

The deliverable is one reproducible, running CPU reference release: browser, API,
PostgreSQL, parser/OCR, encoder, retrieval, local inference, knowledge/memory,
governed workflows and operations working together. A reviewer must be able to
install it on a clean supported machine, complete the advertised user journeys,
restart it, restore it and reproduce its evidence without developer intervention.

“Certified” means independent engineering acceptance of the exact source, images,
models, configuration, supported input classes, workload limits and environments
listed in the certificate. No test programme establishes universal zero-defect
correctness or confers third-party, regulatory, AMD or Evolus certification.
Any separately required partner assessment is a later gate.

The existing requirements remain binding: [J completion plan](J_REPAIR_UNBLOCK_COMPLETION_PLAN.md),
[K workspace integration](K_RESEARCH_WORKSPACE_INTEGRATION_PLAN.md),
[L private authorization](L_PRIVATE_DOCUMENT_AUTHORIZATION.md), original 89 cards
and their 301 criteria, 209 release-checklist requirements and nine research cards.
M is their execution overlay, not a replacement or a reduction in scope. The
[current static runtime inventory](current-runtime-inventory.json) refreshes the
historical 507-function denominator. Assign current definitions to requirements,
tests and evidence before claiming coverage; historical execution observations
cannot be reused against the new inventory.
The [criterion evidence ledger](criterion-evidence-ledger.csv) expands the inherited obligations into 537 individually addressable rows (301 original criteria, 209 checklist requirements, nine research cards, ten UI cards and eight authorization cards). Candidate implementation/test/receipt links remain separate from independent review; an empty assignment or mapped receipt does not establish that a criterion passed. Regeneration preserves review state and refuses silently changed obligations.

## Starting state and invariants

- Latest scoped policy-persistence receipt: 798 tests passed, one optional skip,
  including eight real PostgreSQL scenarios. This is evidence of its recorded scope,
  not an accepted full application or deployed candidate.
- Individual identities, private-first pure policy, explicit chat scope and
  source-bound quote anchors exist. Database policy persistence is partial;
  production content enforcement, ingestion integration and sharing UI remain open.
- The intermediate individual-user content denial stays in place until E2E-07.
  Develop and test the adapter in owned fixtures; do not upload private real data
  into an environment whose legacy readers can expose it.
- Preserve existing source IDs, originals, citations, audit history, credentials,
  user data and existing live services. Ambiguous legacy ownership stays quarantined
  until an explicit owner mapping is reviewed. No ownership inferred from shared roles.
- Retain local RBAC, explicit owner grants, no implicit admin/agent content access,
  committed privileged-read audits, complete derived provenance and fail-closed behavior.
- Keep live upload limits at 2 MiB/100 pages and live model/context settings until
  the relevant limit/quality gates pass. Do not raise constants to simulate capacity.
- Central identity/security activation, generated execution, voice and external
  partner/hardware rollout remain deferred. Their exclusions must be truthful and reviewed.
- Preserve failed evidence. A changed artifact reopens its affected acceptance gates.

## Execution order and responsibilities

The critical path is baseline/acceptance contracts → database access and derived
protection → authorized durable ingestion → integrated retrieval/answers/viewer →
real user journeys and capacity → frozen-image qualification → independent release
acceptance → controlled CPU commissioning → partner-preparation handoff.

Each package has an implementation owner and a different acceptance reviewer,
assigned in E2E-01. Reviewer identities are recorded only when actually assigned.
Storage/schema changes have one integration owner and run in order. Independent
preparation for host security, rights, fixtures and operational checks can progress
while dependent implementation proceeds. The machine plan specifies dependencies;
it does not authorize simultaneous writers or tool delegation.

### E2E-01 — Reconcile the real baseline and requirements

Inventory current source, running/candidate images, models, effective configuration,
schema, launchers, APIs, UI controls and disabled features. Record absent Git metadata
honestly and create a complete hashed source manifest. Reconcile stale status pages
without rewriting historical receipts. Expand every existing criterion into a row:
requirement → observable behavior → owner → implementation → test → evidence → reviewer.
Map newly added functions, routes and migrations; find orphan features and unsupported
claims. **Exit:** no unassigned mandatory requirement and a reproducible baseline.

### E2E-02 — Establish qualification environments and test oracles

Create isolated real PostgreSQL/API/parser/encoder/model/browser environments with
owned resource names, pinned images, bounded resources and deterministic cleanup.
Test Python 3.12 container runtime and each declared supported host/launcher; explicitly
exclude untested environments. Establish a managed host session for the canonical
scan early; the current disabled filesystem profile cannot supply that prerequisite.
Prepare rights-cleared native/scanned/mixed/rotated/table/formula/multilingual PDFs,
independent ground truth and untouched subject holdouts. Freeze numeric quality,
latency, queue, resource and recovery thresholds **before** tuning or measurement.
**Exit:** runnable environments, assigned reviewers and approved workload/test contracts.

### E2E-03 — Complete database identity, ownership and access enforcement

Finish ACL-01/02/03. Attach verified actors to every transaction with reliable pool
reset. Implement database policies/least privilege and application authorization
for content reads, writes, originals/HEAD, metadata, pagination, counts and traversal.
Create ownership in the source transaction. Replace global logical hash/revision
deduplication with owner-scoped identity, preserving legacy IDs and artifact custody.
Do not expose cross-user duplicate response/timing signals. Separate application,
migration and bounded job privileges. Review trusted actor arguments in migration
0008; server functions alone do not establish an SQL or content isolation boundary.
**Exit:** real SQL and HTTP A/B same-role tests, admin/agent negatives, duplicate-byte
isolation, ownership rollback, privilege convergence and pooled-connection isolation pass.

### E2E-04 — Protect every derived artifact and revoke access completely

Finish ACL-05/06 across chunks, formulas, graph nodes/edges, supplements, memories,
learning proposals, engineering flows, sessions, invocation receipts, caches, prompts,
exports and logs. Store all contributing sources and generations; unresolved provenance
denies. Require access to every dependency or regenerate using authorized evidence.
Reauthorize on fetch, prompt construction and immediately before response release;
withhold/cancel stale in-flight work. Define the response/revocation transaction
boundary explicitly and test races. Legacy mixed-provenance records remain withheld.
**Exit:** share → query → revoke prevents later answer/receipt/cache/citation/export
fetches; graph bridges, metadata, counts and prompt/log canaries leak no private content.

### E2E-05 — Finish sharing and administrative workflows

Implement owner-only share/revoke API and UI, explicit server-owned groups, expiry,
stale-update feedback and immediate revoked-state UX. Readers cannot reshare. An
admin needs an explicit content grant and a committed access audit; unavailable audit
storage denies bytes. Provision the demo library by named identities and explicit
group shares. **Exit:** owner, shared reader, unrelated user, group member/removed
member, admin and bounded agent workflows pass through the real browser and API.

### E2E-06 — Implement durable authorized ingestion and atomic indexing

Finish ACL-07 and UI-04. Enqueue in the source transaction, claim bounded leases with
`SKIP LOCKED`, checkpoint stages, cap attempts and reject expired/stale publication.
Refactor embedding persistence to accept the owning transaction. Validate and publish
knowledge, embeddings, graph and search visibility as one generation; failed jobs
publish no partial results. Check job authority at claim and publication. Preserve a
previous valid generation during replacement. Add per-actor fairness, admission,
observable progress, cancellation and bounded CPU/RAM/disk/time; parser/encoder receive
no broad database/admin credentials. **Exit:** kill/restart, duplicate submission,
lease takeover, source replacement/revocation and database-loss fixtures recover without
double activation, corruption or unbounded retries; all effective database grants pass.

### E2E-07 — Independently accept the private application adapter

Run ACL-01 through ACL-08 as one source-policy matrix across every route and derived
path, including browser identity switches, audit outages, cached outputs, concurrent
revocation and reused connections. Review implementation and raw adversarial evidence
independently. **Exit:** only after the complete matrix passes may the individual-user
content adapter be enabled in the isolated candidate. This is not live deployment.
Any uncovered content path keeps the intermediate denial enabled.

### E2E-08 — Repair extraction, typed facts and source lineage

Complete native/OCR page classification, reversible normalization/Unicode maps,
revision/generation custody and append-only corrections. Qualify dimensions, units,
uncertainty, temporal conditions, numerical precision and formula lineage. Measure
critical negation, symbols, tables and formulas separately from text custody.
**Exit:** original bytes and exact quotes remain resolvable; incompatible dimensions
never merge; unsupported/partial recognition visibly abstains and is excluded from
accuracy claims. Supported critical classes must pass, or the declared release scope
must undergo explicit independent review rather than silent exclusion.

### E2E-09 — Finish knowledge, memory and governed learning

Integrate source-linked structural navigation, formulas and graph relationships.
Bind candidate memories to actor/scope/dependencies; similarity never grants factual
authority. Finish contradiction quarantine, temporal/version selection, correction,
shadow evaluation, independent promotion, expiry and replay/rollback. Ensure the
submitter cannot approve its own change. **Exit:** stale/concurrent/expired reviews,
withdrawal, supersession and multi-source graphs preserve provenance and invalidate
affected projections without overwriting observations.

### E2E-10 — Integrate full authorized-library retrieval

Connect ordinary natural-language Ask to a server-side query encoder and evaluated
lexical/semantic fusion. Remove the 20-document request and first-100 listing bottlenecks
without silent truncation. Filter authorization before ranking/counts/pagination and
reauthorize hydrated candidates. Pin model/vector generations, paginate completely
and expose honest coverage/omission status. Profile current JSON embedding and graph
reload/copy costs before selecting a larger index. **Exit:** every indexed authorized
source is eligible; source-family holdouts meet predeclared recall/MRR/nDCG criteria;
cross-user sources never reach prompts or results.

### E2E-11 — Repair actual grounded chat and resource accounting

Run the complete application with actual CPU inference. Diagnose prior strict-citation
failures and long-prompt timeouts. Enforce claim-to-source support, quantity/unit fidelity,
comparisons, conflicts, subject switches and insufficient-evidence handling. Validate
citations after generation; withhold unsupported claims rather than attach unrelated
citations. Count the complete prompt and output allowance with the actual tokenizer.
Reconcile durable invocation/task reservations exactly once across cancellation,
disconnect, timeout, crash, retry and day rollover. **Exit:** independent support/refusal
and resource thresholds pass; no fabricated source/quantity in mandatory fixtures;
unknown costs or business outcomes remain unknown.

### E2E-12 — Complete exact PDF citation navigation

Integrate the pinned local PDF.js positioned text layer and licensed local fonts.
Match quote plus context uniquely using reversible normalization; repeated text stays
ambiguous. Bind highlights to source hash/revision/generation and recompute after zoom,
rotation, resize and device-pixel-ratio changes. Qualify OCR quadrilaterals separately.
Author-source math without PDF alignment cannot claim a PDF passage. **Exit:** synthetic
exact-native cases all select the correct passage; independent corner/DOM-range
oracles pass; ambiguous/OCR/page-only/unavailable states are labeled accurately.

### E2E-13 — Finish engineering flows and operational accounting

Complete issue → evidence → applicability → proposed steps → independent review,
with source/uncertainty lineage for each step. Procedures remain data; no generated
executor is activated. Persist task/cohort denominators, continuity, resource use and
outcome status, and bound session/audit/invocation storage with reviewed retention/holds.
**Exit:** unsupported causal/diagnostic claims are withheld; review-order edges do not
masquerade as physical causality; restart/replay does not duplicate outcomes or budgets.

### E2E-14 — Complete the real UI from login to reviewed result

Use real backend services for login, private upload, queue/progress/error/retry,
library paging/search, sharing, ordinary Ask, citations/PDF, knowledge/memory,
reviewer actions, admin auditing, export, logout and restart. Finish keyboard/screen-reader
access, focus, responsive layout, loading/error/empty/partial states and cancellation.
Bind async work to auth/scope/request/source/render generations; clear drafts, workers,
PDF buffers and stale private data on identity change. **Exit:** all advertised journeys
work without scripts, manual database edits or intercepted APIs; real browser privacy,
accessibility and stale-response cases pass.

### E2E-15 — Qualify the required workload and upload envelopes

First independently demonstrate **100 PDFs/5,000 pages**, then the required target
**1,000 PDFs/50,000 pages**. The latter is a release gate; the former alone is insufficient.
Measure a frozen native/OCR/mixed workload with two-document configurable ingestion
concurrency, per-actor fairness, cold/warm retrieval, actual model contention, queue
depth, p50/p95 with adequate samples, peak RAM, CPU, disk/index/WAL/backup growth,
graph integrity, restart recovery and no full-library rebuild on one update.
Qualify 25 MiB/250-page standard uploads end to end before enabling that envelope;
100 MiB/1,000-page large uploads remain separately gated. Keep current live limits
until acceptance. **Exit:** signed workload/resource/SLO results meet the frozen
contract with no silent truncation, quality regression or authorization leak. Optional
10,000 PDFs/500,000 pages is a stretch experiment, never a substitute for P1.

### E2E-16 — Repair and rehearse the complete runtime lifecycle

Finish all supported clean launchers, install/import safety, schema journal/replay,
least privilege, effective Windows/private-state ACLs under a distinct identity,
secret rotation/cache races, transport bounds and runtime sandbox controls. Exercise
populated old-schema upgrades, current/pre-upgrade restores, previous-image full HTTP/UI
compatibility, concurrent-write backups, interrupted/disk-full recovery and rollback.
Verify network/mount/user/capability/PID/resource restrictions in the actual containers.
**Exit:** owned rehearsals meet frozen RTO/RPO and compatibility contracts; every failure
has an explicit recoverable state. A dump or package-only probe is not a restore/UI pass.

### E2E-17 — Freeze a candidate and run integrated adversarial qualification

Build reproducibly from the reconciled source and lockfiles; retain previous images
before promotion. Freeze source/image/model/configuration/fixture manifests and run
all relevant unit, contract, database, API, real-model and real-browser checks on that
candidate, including final-image P1 capacity, supported upload limits and recovery.
Development-image measurements alone cannot accept the frozen release. Add prompt
injection, malformed/oversized/compressed input, hash corruption,
job races, cancellation, model/parser/database outages, missing fonts, saturation and
privacy canaries. Repeat the required 100 startup cycles on the exact intended image.
**Exit:** required cases pass with source stable, no unclassified failures or skipped
mandatory tests, immutable receipts and cleanup. Fixes produce a new candidate and
reopen affected gates; historical successes never qualify changed bytes automatically.

### E2E-18 — Obtain canonical security and package acceptance

Use the managed host prerequisite prepared in E2E-02 to run the installed canonical
deep scan on the frozen source; retain its real scan identity and artifact bytes.
Triage, fix and verify findings. Generate SBOMs and scan exact API/database/parser/
encoder/model images and distributed browser assets; review applicability, licenses,
runtime exposure and exploitability without suppressing failures. **Exit:** independent
security reviewer accepts the exact candidate with no unresolved required findings or
release-blocking applicable risk. A local report, old scan or hand-written PASS cannot
replace canonical evidence. The current unmanaged-session blocker remains external.

### E2E-19 — Clear rights, packaging and documentation

Trace code/model/font/dataset/document/reference origins and distribution rights.
Inspect actual archive bytes for credentials, private content, restricted references,
licenses, notices, integrity and reproducibility. Refresh supported-feature, installation,
limits, operator/recovery and known-limitation docs for the final candidate. Review
deferred-feature exclusions against original criteria. **Exit:** an independent reviewer
accepts the exact distributable and redacted evidence; no publication occurs here.

### E2E-20 — Pass untouched-subject and cold-start acceptance

Use withheld subjects and source families never used to tune implementation. Perform
the existing ten-step challenge and judge demonstrations on the frozen candidate,
including unseen upload, explanation, comparison, contradiction, PDF passage opening,
private-source denial, knowledge/learning review and restart. Have an independent
reviewer reproduce the full journey from clean startup. **Exit:** all required outcomes
meet the predeclared rubric; a tuned-on failure requires a fresh holdout.

### E2E-21 — Accept, commission and certify the CPU reference release

Independently reconcile every original/checklist/research/private/workspace criterion
with final evidence and dependencies. No manual acceptance flags in place of review.
Generate the actual content-bound foundation, extension, canonical-security and
admission artifacts, retaining the real canonical artifact. The existing read-only
guard must return **ADMITTED** for the frozen source. Then execute the controlled CPU
commissioning procedure with verified backup, retained rollback image and explicit
rollback triggers; complete the predeclared observation window and acceptance probes.
Keep release evidence, commissioning records and authorization records distinct.
**Exit:** running image identity matches accepted artifacts, observation checks pass,
rollback/restore is demonstrated and independent final sign-offs are present.

The certificate must list accepted scope, requirement results, source/image/model/config
digests, supported environments/input classes, measured capacity/SLOs, reviewer names
and roles, actual scan references, exact artifact hashes, limitations, recovery results
and recertification triggers. Missing review or mandatory evidence means **NOT CERTIFIED**.

### E2E-22 — Hand off readiness for Evolus and AMD preparation

Only after E2E-21, prepare the accepted CPU artifact, architecture/interface contracts,
dependency/SBOM/rights pack, requirements evidence, hardware/resource measurements,
operator runbooks and environment-gap register. Define the separate partner/data/
identity/network and hardware/model/runtime qualification plans. **Exit:** a reviewable
handoff with clearly unverified partner/hardware items. It does not enable central
security, connect company systems, import company data or claim AMD/Evolus approval.

## Mandatory acceptance journeys and failure tests

| Journey | Required evidence |
|---|---|
| Alice uploads; Bob uploads identical bytes | Separate private logical documents; atomic source/owner/artifacts; no duplicate/existence signal across actors |
| Alice shares; Bob asks and opens a citation | Correct grant, authorized retrieval/prompt, supported answer and correct revision/passage in real Chromium |
| Alice revokes while Bob has a query/PDF/job in flight | No subsequent unauthorized response/fetch/publication; defined transaction boundary, cleared stale UI and independently observed race |
| Admin or agent requests a private source | No implicit bypass; explicit bounded access and committed privileged audit where required; audit failure denies |
| Library exceeds former first-N bounds | An authorized match beyond each old bound is retrieved; unauthorized matches cannot affect rank/count/graph output |
| Compare, switch subjects, conflict, insufficient evidence | Stable explicit scopes, source-supported comparisons, no memory contamination, clear conflict/refusal |
| Cite repeated text, rotate/zoom, scanned/mixed/unsupported PDF | Unique native alignment only; independently correct transforms; honest fallback and no guessed exact highlight |
| Kill worker/API/database during ingest, ask or review | Bounded retry/recovery, no partial activation, no duplicate receipt/accounting/review and no stale lease publication |
| Upgrade, restore, rollback and restart | Source bytes, ACLs, source generations, audit and accepted workflows survive; previous full API/UI behavior tested |
| Clean install and unseen subject on the final image | Independent reviewer completes the advertised workflow within frozen quality/resource limits |

## Evidence and release decision

Use `evidence/end-to-end/<package>/<run-id>/` for immutable manifests, commands,
versions, exact exits, test denominators, raw results, expected/actual outcomes,
failure classification, resource measurements, cleanup and reviewer verdicts.
Keep private inputs and secrets out of submission projections. A report distinguishes
real model/server/database/browser execution from mocks and intercepted fixtures.

States: PLANNED → READY → IN_PROGRESS → VERIFYING → ACCEPTED. Use BLOCKED with a
specific prerequisite, FAILED with preserved evidence, and DEFERRED only for explicitly
approved exclusions. Current packages are planned; earlier scoped evidence is partial
input, never automatic acceptance. Reopen affected packages after material source,
schema, model, dependency, policy, fixture or environment changes.

Non-negotiable gates include every must-deny security case, custody/integrity invariant,
synthetic exact-native anchor and mandatory workflow passing; zero unresolved required
security findings; and independently accepted P1 capacity. Statistical quality, latency,
soak duration and recovery targets must be numeric, frozen and reviewed in E2E-02.
No optimistic estimate or test count replaces a missing gate.

Schedule the work by gates, not an unsupported finish date. E2E-01/02 produce measured
effort estimates, resource availability and reviewer bookings; update the schedule after
the authorization vertical slice and the P0 benchmark. Work outside the blocked scan
continues, but absent canonical clearance or independent reviewers prevents certification.

The accompanying JSON/CSV plan maps all 24 FIN packages, ten UI packages and eight ACL
cards. Its planning validator checks inventory, coverage and dependencies only; it does
not certify the product or edit any acceptance ledger.

- [Machine-readable package and requirement mappings](end-to-end-completion-plan.json)
- [Execution tracker](end-to-end-completion-tracker.csv)
- [Planning validation result](end-to-end-completion-validation.json)

Rebuild the planning mappings with
`python plans/implementation/build_end_to_end_completion_plan.py`. Existing execution
tracker rows are preserved; maintain their owners, state and evidence during work.
This command performs no Docker operation, product test, migration or deployment.
