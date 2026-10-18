"""Reconcile all existing requirements into a remaining-work plan; planning writes only."""
from pathlib import Path
import csv
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def read(relative):
    raw=(ROOT/relative).read_bytes()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()


def main():
    backlog,backlog_sha=read('plans/implementation/backlog.json')
    extension,extension_sha=read('plans/implementation/release-validation-extension.json')
    execution,execution_sha=read('plans/implementation/execution-status.json')
    allocation,allocation_sha=read('plans/implementation/current-function-allocation.json')
    progress,progress_sha=read('plans/implementation/release-validation-execution.json')
    index,index_sha=read('evidence/release-validation/current.json')
    cards=[]
    def card(number,title,ids,dependencies,lane,steps,acceptance,refs=()):
        cards.append(dict(id=f'FIN-{number:02d}',title=title,
            priority='P0' if number in (1,2,3,4,5,6,7,20,21,22) else 'P3_DESIGN_ONLY' if number==23 else 'P2_DEMO_REQUIRED' if number in (19,24) else 'P1',
            original_cards=[f'NSAI-{n:03d}' for n in ids],dependencies=[f'FIN-{n:02d}' for n in dependencies],
            lane=lane,status='EXTERNAL_PREREQUISITE' if number==2 else 'DESIGN_ONLY' if number==23 else 'PLANNED',
            owner_role='Host operator + independent security reviewer' if number==2 else 'Implementation engineer + separate verifier',
            additional_research_cards=list(refs),implementation_steps=steps,acceptance_criteria=acceptance,
            evidence_directory=f'evidence/completion-repair/FIN-{number:02d}/',
            execution_boundary='Owned isolated CPU fixtures; no live mutation or deferred-provider activation.',
            recovery='Declare changed files/schema/resources before execution; preserve previous image, originals, failed receipts and cleanup ownership. Rehearse schema compatibility/restore before any authorized deployment.',
            accepted=False))
    card(1,'Reconcile baseline, claims and exact evidence', [1,2,3,47,81],[], 'Independent now',[
        'Archive current source/image/model/configuration and input hashes, runtime inventory, schema, redacted logs, effective policies and known failures. Preserve absent Git metadata honestly; resolve any required commit/versioning decision explicitly rather than inventing IDs or committing without authorization.',
        'Reconcile old 0df/634/3db receipts with current4bd and later host-tool changes. Update stale56/42/487 counts and design-only semantic wording without overwriting historical records.',
        'Create requirement -> contract -> implementation -> test -> exact evidence -> reviewer links; identify active candidate, live, disabled, unsupported and simulated states separately.'
    ],['Every89 original card,301 criterion,209 checklist requirement and9research card has a disposition/owner/evidence need.',
       'A verifier can reproduce exact current artifact identities and locate immutable catalog snapshots; no PASS inherited from counts.',
       'Test/evaluation/submission evidence stays separate from deployment; baseline missing facts remain explicit.'])
    card(2,'Recover canonical security scan environment',[77,78],[1],'Host prerequisite; independent work continues',[
        'Host operator selects a managed workspace filesystem profile using the permissions menu or CLI /permissions and refreshes the environment. Windows sandbox=elevated alone is not proof; project files cannot change the active parent profile.',
        'Inspect effective refreshed session context. If unchanged, preserve the existing pre-start blocker and continue other lanes; use a new scoped session if the client cannot refresh. Do not retry the same failed invocation or broaden global permissions.',
        'Once the prerequisite actually changes, run the installed canonical DeepScan workflow against a frozen candidate, retain its real scanId/artifacts, resolve validated findings in separate patches and requalify affected gates.'
    ],['Actual managed parent profile and successful scanner start demonstrated, not inferred from menu labels.',
       'Canonical result belongs to exact source; every required finding is fixed/retested or independently dispositioned.',
       'No shell-authored canonical report, scan substitution, invented scanId or security clearance while blocked.'])
    card(3,'Resolve image/package findings and reproducibility',[21,22,23],[1],'Independent now',[
        'Inventory exact API/parser/OCR/DB/model images, pinned dependency inputs, SBOMs and runtime restrictions. The latest API scan retains28advisories, including1HIGH; preserve exit2.',
        'For CVE-2026-85091, independently match installed zlib binary/source/package patches and reachable non-blocking gzip writer callers against vendor/upstream evidence. Keep needs_review until the affected-version discrepancy is resolved.',
        'For confirmed applicable findings, select supported patched packages/base digest, rebuild locked images and rerun affected parser/model/browser/restore checks. If no supported fix exists, document precise containment, owner and release impact; do not suppress or apply speculative C patches.'
    ],['Every exact-image advisory has component/version, applicability, evidence, owner and next action; no zero-CVE claim.',
       'Clean/offline-compatible build reproduction and effective network/mount/user/capability/secret/PID/CPU/RAM controls are verified at runtime.',
       'No unresolved release-blocking applicable defect; any unresolved required finding keeps release denied.'])
    card(4,'Complete local identity, object permissions and inactive central contracts',[10,11,27,65,66,85],[1],'Independent now; local only',[
        'Specify local actor identity, role binding, source ACL default, session ownership, token expiry/revocation/rotation and cache invalidation. Shared role credentials are the current compatibility baseline, not individual identity.',
        'Implement versioned local identity/source-authorization contracts in an owned clone; filter originals, chunks, graph nodes/edges, vectors, memory, citations and exports before model access and after fusion. Legacy missing ACLs require explicit migration policy and fail-closed ambiguous access.',
        'Test every role/object read/write/review/export/promotion path, forged role requests, revocation and delayed browser replies. Stage central adapter and scoped secret lifecycle only; activation remains denied.'
    ],['Cross-actor/source/existence/metadata/graph-bridge/cache tests deny unauthorized content before it reaches prompts.',
       'Authenticated, independent reviewer actions cannot be self-approved; effective local auth remains on.',
       'Central configuration cannot bypass local controls; no OIDC/central commissioning or live credential rotation implied.'],['REF-04'])
    card(5,'Prove Windows/private-state and database least privilege',[7,8,26],[1],'Independent now',[
        'Capture effective ACL inheritance/owner/grants on synthetic private-state directories, then perform hostile-identity denial using an available isolated Windows test identity; record unavailable identity as blocked rather than fake proof.',
        'Exercise migration role convergence, excess memberships, runtime table privileges, immutable evidence triggers, FK constraints and concurrent writes on clean/old databases.',
        'Rehearse scoped credential lifecycle using synthetic keys, including same-size replacement, cache invalidation and browser clearing; preserve current live values.'
    ],['Actual denied reads under a distinct identity or an explicit external prerequisite; no ACL-text-only acceptance.',
       'Runtime roles cannot rewrite source/evidence or inherit excess privileges; invalid states are rejected transactionally.',
       'Credential/cache race fixtures and required rollback paths pass without exposing secret bytes.'])
    card(6,'Finish startup, import, transport and interface integrity',[4,5,6,24,28,29],[1],'Independent now',[
        'Reconstruct actual module/import/API/SQL/UI/worker flows; classify stubs, TODOs, dead code, duplicate implementations, cyclic imports and hidden local assets.',
        'Exercise every supported launcher on clean state, startup races, missing dependencies and graceful shutdown. Keep readiness observational and release admission ahead of secrets/migrations/build/service mutation.',
        'Verify strict schemas, TLS/host/proxy/redirect policy, bounded worker custody and subprocess deadlines on valid and hostile transport responses; retain the fixed GET/HEAD operation-ID regression.'
    ],['Every advertised path is executable and matches diagrams/contracts; unsupported paths are clearly excluded.',
       'No import-time mutation, launcher bypass or startup side effect before required admission.',
       'Partial migration/install/provider failure has an owned recoverable state and tested next-run behavior.'])
    card(7,'Finish CPU commissioning, recovery and rollback',[9,25,32],[3,5,6],'Independent rehearsal; release later',[
        'Freeze exact maximum source/database/backup limits and supported previous schema/image compatibility before experiments.',
        'Test concurrent-write backups, maximum-size/time, process kill, partial dump, storage exhaustion, DB restart, interrupted migration and restore into a fresh volume; verify all source/graph/memory/review/audit/configuration state.',
        'Rehearse supported prior-image HTTP/API rollback and fresh candidate startup with preserved user volumes; repeat final-artifact startup measurements rather than reusing historical100-start proof.'
    ],['Protected backup integrity and actual restore independently verified; no restore claim from dump creation.',
       'Prior/new schema compatibility and recovery triggers are explicit and pass realistic failure fixtures.',
       'Foundation acceptance waits for its original dependencies and security gates; rehearsal does not deploy LIVE.'])
    card(8,'Qualify typed values, formula contracts and safe calculations',[33,34,57,58],[1],'Independent now',[
        'Complete finite decimal/unit/dimension/interval/rounding/negation/condition/time schemas with original multidomain fixtures and exact source offsets.',
        'Separate native math-looking quotes, author LaTeX quotes, OCR guesses and allowlisted deterministic computations. Preserve assumptions, units and unsupported cases; never execute TeX, Python or arbitrary formulas.',
        'Independently compare supported formula/symbol/quantity cases to labeled originals and dimensioned arithmetic oracles; retain the PDF-only author endpoint as unavailable TeX rather than inventing source.'
    ],['85C/185F and equivalent precision compare correctly; incompatible dimensions/conditions do not merge.',
       'Symbol/critical-token errors are measured separately from source custody and plain-text extraction.',
       'Unsupported recognition/computation abstains explicitly; no formula correctness claim from a quoted JSON candidate.'])
    card(9,'Finish contradiction, relevance and bounded memory',[17,35,36,37],[8],'Independent now',[
        'Apply one scoped conflict policy across retrieval, reflection and learning; preserve competing and conditional/historical evidence.',
        'Rank eligible reviewed memory by query relevance and invalidate stale source/review/rule dependencies rather than selecting by hash order.',
        'Measure complete JSON/token envelopes including IDs/schema/receipt/quarantine and every omission; test persistence, eviction/retention and restart replay.'
    ],['Conflicting75/85 examples quarantine or propose review without overwriting observations.',
       'More than12eligible records select relevant evidence and respect source/page/revision/actor scope.',
       'Full envelope stays within actual bytes/token budgets; no hidden dropped records or self-reinforcing canon promotion.'])
    card(10,'Complete extraction lineage and source generations',[13,14,18,38,39],[1],'Independent now',[
        'Finish reversible raw/normalized Unicode/chunk/source-region mappings and independently validate all page classes, truncation and source references.',
        'Add durable bounded encoder jobs with leases/backpressure/retry and idempotent document/model keys, plus versioned extraction/index/projection generations with staged/reviewed/active/historical states and explicit consumer pins. Same original bytes may produce a new generation without overwriting prior artifacts.',
        'Implement interruption/cancel/retry/idempotency and source revision/withdrawal invalidation across chunks, vectors, graph, memory and caches; design retention/legal holds before destructive deletion.'
    ],['Every emitted quote/region maps exactly or is explicitly unanchored; line0/guessed coordinates are not accepted.',
       'Crash/concurrent activation tests pin one coherent generation; historical citations remain resolvable.',
       'Withdrawn or inaccessible sources cannot remain retrievable through derivatives, graph bridges or stale cache.'],['REF-05','REF-06','REF-07'])
    card(11,'Qualify lexical, semantic and hybrid retrieval',[40,41,48,49,87],[8,9,10],'Independent now; optional worker only',[
        'Register fresh independently labeled mixed-domain golden/holdout questions before tuning; the existing14papers/seven exploratory queries are development material and their mathematics miss remains recorded.',
        'Evaluate actual PostgreSQL lexical retrieval, pinned CPU semantic retrieval and existing RRF using the same authorized corpus. Add hybrid wiring only after paired quality/resource evidence; test dense failure with bounded lexical fallback.',
        'Implement source-bound exact-answer lane and conservative support/abstention controls. Compare citation support to original pages, not just source IDs; test conflict, ambiguity, stale versions and cross-domain prompts.'
    ],['Recall@k/MRR/nDCG and citation-support/refusal metrics have predeclared labels/thresholds and raw outcomes.',
       'Source authorization occurs before ranking/prompt entry and after hydration/fusion; model/vector generations match.',
       'No general semantic truth or long-context answer-quality claim without independent evidence. Global index activation remains separate.'],['REF-03'])
    card(12,'Repair grounded CPU responses and intelligence/resource balance',[12,15,16,20],[1,8,9],'Independent now',[
        'Reduce prior strict-citation0/60 and long-prompt timeout failures to tokenizer/template/transport/support mechanisms using owned model clones and fixed independent questions.',
        'Improve only the diagnosed failure or deliberately constrain unsupported responses; exercise terminal settlement/cancel/expiry/process-death/idempotent retry races with real storage.',
        'Benchmark matched4K and candidate8K quality, cold/warm latency, token admission, concurrency/queue/memory and verified outcomes. Keep LIVE4K until qualification; do not add vLLM, larger models or16K/32K to hide failures.'
    ],['Grounded supported responses and abstentions meet independently set quality bounds; fabricated citations/quantities withheld.',
       'Actual tokenizer covers the complete prompt and output allowance; all terminal states reconcile once.',
       'Resource/latency receipts are measured and bounded; unknown financial cost and verified-outcome cost stay unknown.'])
    card(13,'Complete PDF workspace, OCR lifecycle and geometry',[50,51,52,53,54,55,56,59],[5,6,10],'Independent now',[
        'Add bounded durable OCR queue/leases, cancel/restart/retry/recovery and backpressure without parser access to DB/model secrets or outbound network.',
        'Construct independent quarter-turn/crop/UserUnit/DPI/deskew geometry oracles before adding support for UNISEP pages12/13. Rerun actual refused pages only after synthetic geometry passes.',
        'Calibrate separate text/CER/WER/critical-negation/table/formula and coordinate metrics on untouched source-family holdouts; retain native/OCR separation, unsupported language/handwriting states and all failed cohorts.'
    ],['Native/scanned/mixed/blank/unsupported/failed pages are classified honestly with observable bounded jobs.',
       'All transform corners and inverse mappings agree with independent oracle; highlights never use guessed positions.',
       'Degraded tables/negation/formulas stay unqualified until their own thresholds pass; general accuracy is not inferred from33processed pages.'],['REF-09'])
    card(14,'Finish typed knowledge assembly, structural units and provenance',[60,62,67,68],[8,10],'Independent now',[
        'Complete typed observation/claim/entity/relationship/event/measurement/uncertainty contracts and distinguish source statements from lexical mentions and similarity.',
        'Independently qualify section/block heuristics on unseen layouts and surface13,831existing candidate units in the source workspace with original-span links; calibrate quality signals without ASCII corruption scoring.',
        'Extend graph invariants to disambiguation, contradictions, reorder/determinism, source withdrawal, procedure manifests and bounded UI traces; preserve original and supplemental namespaces.'
    ],['No invented factual/causal edge or type assignment silently becomes accepted knowledge.',
       'Unknown/multilingual/math/table/ambiguous layouts retain original content and uncertainty.',
       'Every graph/flow edge and unit links to exact source/version or explicit interpretation, with consistent rejected/superseded states.'],['REF-01','REF-02','REF-07'])
    card(15,'Complete governed learning, correction and temporal contracts',[61,63,64,88,89],[4,9,10,14],'Independent now; signing design only',[
        'Implement proposal/shadow/holdout/review/reject/supersede/rollback/source-withdrawal state transitions with independently authenticated review and stale-version checks.',
        'Track correction/outcome uncertainty and valid-time versus observation-time where supported; abstain outside qualified temporal contracts.',
        'Measure genuine held-out improvement without evaluation contamination or automatic trust amplification. Document external signing/anchoring/rotation/revocation prerequisites as future contracts; do not commission signing keys.'
    ],['Submitter cannot approve itself; duplicate, expired, concurrent and stale reviews fail consistently and are audited.',
       'Rollback/replay/source withdrawal preserves evidence and invalidates affected accepted projections.',
       'Learning improvement is measured independently; local hash chains are not called immutable external signatures.'])
    card(16,'Complete issue-to-engineering-flow work',[69,70,71,76],[8,14,15],'Independent now',[
        'Use the approved engineering-issue scope instead of literal transcript/speaker processing; preserve the archived superseded criteria and explicit user correction.',
        'Distinguish symptoms, source-reported measurements, hypotheses, candidate checks, reported actions and verified outcomes, including applicability/safety restrictions and missing-measurement questions.',
        'Evaluate unfamiliar engineering domains, contradictory/unsafe/insufficient reports and versioned flow review/publish/rollback; keep flows data-only and prevent execution privileges.'
    ],['Every proposed diagnostic step has source/rationale/applicability or is withheld as unsupported.',
       'Review-order edges are not labeled proven physical causality or successful diagnosis.',
       'Independent outcome evidence and reviewer state determine completion; no transcript product or production executor is activated.'])
    card(17,'Complete utilization, task continuity and cost accounting',[72,73,74,75],[9,12,15],'Independent now',[
        'Define durable task/cohort denominators, attempts, outcomes, units and ownership before drawing utilization/business conclusions.',
        'Implement CAS/crash/day-rollover/concurrent reservation reconciliation and distinguish continuation, recurrence and new tasks with auditable reasons.',
        'Connect measured local CPU/time/token/resource usage to governed budgets; label hypothetical prices/savings separately and retain unknowns. Derive original logic without DVA data/code or business dictionaries.'
    ],['No duplicated/abandoned reservation corrupts daily budgets or outcome denominators.',
       'Resources and limits can be traced to tasks, versions and actual evidence.',
       'No fabricated dollar costs, ROI or causal business outcomes; reviewed assumptions remain visible.'])
    card(18,'Finish bounded storage, async performance and retention',[42,45,46],[5,10,17],'Independent now',[
        'Measure real application SQL plans, pool contention/event-loop lag, list/query pagination and large inspectors under predeclared mixed workloads.',
        'Profile growth of sources/chunks/embeddings/graphs/sessions/audit/jobs and implement capacity/backpressure plus dry-run retention/hold reports before any cleanup.',
        'Optimize measured bottlenecks only, preserving authorization/coherent snapshots/transaction behavior. Include storage-full/OOM/saturation recovery and cleanup receipts.'
    ],['Declared workload stays within fixed CPU/RAM/PID/storage limits with transparent denial/queueing.',
       'Matched before/after quality, fairness and recovery show no regressions; adequate raw sample counts support any percentile claim.',
       'No automatic destructive retention, lost holds, orphaned derivatives or concealed saturation.'])
    card(19,'Finish real browser PDF and workflow experience',[19,43,44],[4,10,13,14],'Independent now',[
        'Exercise upload stage progress, document/version switching, source-unit display, citation navigation, cross-document links, graph provenance and review states through the real owned browser stack.',
        'Qualify authenticated extensionless originals, GET/HEAD/range/content type, catalog rejection, Unicode safe downloads, logout, delayed/out-of-order replies and retry idempotency.',
        'Test empty/loading/partial/denied/offline/timeout states, keyboard/focus/screen-reader labels/contrast/mobile layouts; remove debug-only user friction.'
    ],['Principal user/reviewer/admin scenarios complete without developer-only intervention on the owned candidate.',
       'Every citation/highlight opens the right authorized source revision/page/region or displays uncertainty.',
       'Private buffers/workers/caches clear on identity changes, and accessibility checks have observable evidence.'],['REF-08'])
    card(20,'Complete adversarial, fuzz, fault and function qualification',[30,79],[1],'Independent now; coverage expands with changes',[
        'Trace all507catalogued Python functions and new additions, UI handlers, container workers and public/internal contracts to original fixtures, owner and card. Current237unit-observed entries are a starting point, not complete coverage.',
        'Close all18checklist adversarial scenarios with harmless original owned fixtures and version-pinned OWASP mapping. Add property/fuzz/branch/race/fault cases for parser/API/graph/promotion/secrets/SSRF/traversal and resource boundaries.',
        'For every function/capability, record direct or justified caller-workload performance qualification, raw timing/resource method and remaining gaps; do not fabricate microbenchmarks or invoke destructive functions against LIVE to increase a count. Replay major claims independently.'
    ],['No unmapped function/feature/contract or falsely inferred coverage; every required failure branch has relevant evidence or an explicit blocker.',
       'Logs/traces/export contain no secret/source payload leakage; denied actions leave trusted state unchanged.',
       'Each failed run has classification, impact, owner, retained artifacts and retest; test harness cannot pass by mocks or omitted inventory alone.'])
    card(21,'Clear provenance, rights and exact submission archive',[31,80],[1],'Independent now',[
        'Review current original NSAI contracts and legacy compatibility adapters separately from the historical imported-source ledger. Verify retained notices and test historical hash/span compatibility on cloned records.',
        'Inventory exact source/dependency/PDF.js/model/paper licenses, private reference boundaries and data rights; document necessary independent reviewer/legal decisions without claiming a comprehensive legal audit.',
        'Build an allowlisted draft archive, reopen it and inspect exact membership/hashes for credentials, raw papers/private fixtures/reference code, restricted assets and unsupported claims; prepare a separately redacted evidence projection.'
    ],['Current source and every distributed component have traceable origin/license disposition; no restricted private reference content included.',
       'Actual archive bytes, not an intended file list, pass secret/privacy/rights review.',
       'Archive is reviewable locally; publication/submission remains a separate user action.'])
    card(22,'Accept and deploy the controlled CPU release',[82],[2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,24],'Final mandatory gate',[
        'Freeze selected CPU scope and exact source/image/config/model/input versions; independently review every required original/research/checklist criterion and unresolved finding.',
        'Prepare authentic fixed-path admission evidence bound to source, plans and reviewer findings. The gate requires original89-card inventory, foundation dependencies, pinned209extension requirements,9research cards and real canonical artifacts; never hand-author fake PASS to unblock startup.',
        'After acceptance, verify protected backup/restore and rollback readiness, deploy the immutable CPU candidate under existing authorization, observe health/integrity/RBAC/resources and revert on defined failures. Publication and deferred activations remain excluded.'
    ],['All applicable mandatory gates have independently reviewed evidence; actual read-only release guard returnsADMITTED for the frozen artifacts.',
       'Fresh deployment preserves user data/configuration and passes the agreed observation window and rollback conditions.',
       'Documentation, demo, final archive and deployed artifacts agree; any permitted correction reopens affected gates.'])
    card(23,'Close deferred boundaries through design and truthful exclusions',[83,84,86],[1],'Design only; no activation',[
        'Keep AMD/ROCm/Evolus, extra providers, optional voice/duplex and central activation outside current commissioning scope; document absent hardware and unsupported claims accurately.',
        'Record future hardware/image/model/license/protocol/identity/resource/cost/quality/rollback prerequisites and explicit activation decision points.',
        'Exclude voice and actual AMD checks using the current plan\'s reasoned NOT_APPLICABLE disposition only; no CPU result is GPU proof and no optional service is launched.'
    ],['Deferred design/exclusion records are complete and independently reviewed without requiring forbidden activation.',
       'No actual AMD, voice, partner eligibility, enterprise identity or external-signature claim is presented as verified.',
       'Later commissioning requires explicit scope selection and its own real environment evidence.'])
    card(24,'Complete untouched-subject challenge and judge demonstrations',[],[4,10,11,12,13,14,15,16,19,20,21],'After feature freeze',[
        'Freeze code and choose a genuinely unseen scientific/engineering subject beyond the seven development topics; seal source provenance, questions and independently labeled expected results before running. Development papers cannot be relabeled holdout.',
        'Without application edits, prove all ten final challenge steps through the real UI/API, including ingestion/typed knowledge/uncertainty/scoped memory/retrieval/citation/navigation/restart and malicious-document containment.',
        'Rehearse demosA-E and record duration, input/expected/actual results, build hashes, screenshots/video fallback and exact evidence. If a fix is needed, invalidate the attempt, rerun affected gates and select a new untouched holdout.'
    ],['All ten challenge steps and every included demo have measured, reproducible evidence on one frozen candidate.',
       'Contradictory/cross-domain/security/PDF scenarios preserve authority and source accuracy; unreliable voice remains omitted.',
       'Independent judge-style cold-start replay succeeds; recordings and live demonstration use identical artifacts.'])

    primary={0:1,1:1,2:3,3:4,4:10,5:14,6:11,7:16,8:19,9:23,10:20,11:20,12:23,13:24,14:1,15:20,16:22,17:24}
    original_owners={}
    for c in cards:
        for identity in c['original_cards']:original_owners.setdefault(identity,[]).append(c['id'])
    requirements=[]
    for row in extension['requirements']:
        mapped={f'FIN-{primary[row["section"]]:02d}'}
        for identity in row['existing_cards']:mapped.update(original_owners[identity])
        requirements.append(dict(id=row['id'],original_section=row['section'],primary_completion_card=f'FIN-{primary[row["section"]]:02d}',completion_cards=sorted(mapped),source_line=row['source_line']))
    original_state={c['id']:c for c in execution['cards']}
    originals=[dict(id=c['id'],title=c['title'],completion_cards=original_owners[c['id']],
                    last_recorded_status=original_state[c['id']]['execution_status'],
                    original_dependencies=c['dependencies'],
                    current_reconciliation='Historical status is not refreshed acceptance; overlay with current scoped evidence.',
                    criteria=c['acceptance_criteria']) for c in backlog['cards']]
    research={f'REF-{n:02d}':[] for n in range(1,10)}
    for c in cards:
        for identity in c['additional_research_cards']:research[identity].append(c['id'])
    functions=[]
    for function in allocation['functions']:
        owners=set()
        for identity in function['punch_cards']:
            if identity in original_owners:owners.update(original_owners[identity])
            elif identity in research:owners.update(research[identity])
        owners.add('FIN-20')
        functions.append(dict(path=function['path'],name=function['name'],line=function['line'],completion_cards=sorted(owners),
                              entry_status=function['status'],benchmark_status=function['benchmark_status']))
    checks=dict(original_cards=len(originals),original_criteria=sum(len(c['criteria']) for c in originals),
                checklist_requirements=len(requirements),research_cards=len(research),functions=len(functions))
    assert checks==dict(original_cards=89,original_criteria=301,checklist_requirements=209,research_cards=9,functions=507)
    assert len({row['id'] for row in requirements})==209, 'Duplicate checklist requirement'
    assert len({(row['path'],row['name'],row['line']) for row in functions})==507, 'Duplicate function allocation'
    assert set(original_owners)=={c['id'] for c in backlog['cards']}, 'Missing original card allocation'
    assert all(original_owners.values())
    assert all(research.values()), 'Missing research card allocation'
    byid={c['id']:c for c in cards};visiting=set();visited=set()
    def visit(identity):
        assert identity not in visiting,'Completion dependency cycle'
        if identity in visited:return
        visiting.add(identity)
        for dependency in byid[identity]['dependencies']:visit(dependency)
        visiting.remove(identity);visited.add(identity)
    for identity in byid:visit(identity)
    plan=dict(version=1,planning_date='2026-10-14',scope='Remaining repairs and unblock plan only; preserves original specifications and acceptance gates.',
        release_approved=False,input_bindings=dict(backlog=backlog_sha,extension=extension_sha,historical_execution=execution_sha,
            current_progress=progress_sha,current_allocation=allocation_sha,evidence_navigation=index_sha),
        baseline_candidate=index['api_candidate'],cards=cards,original_card_coverage=originals,
        checklist_coverage=requirements,research_coverage=research,function_coverage=functions,
        coverage_counts=checks,limitations=['Mapping/planning coverage is not implementation, tested behavior or acceptance.',
            'Original transcript criteria remain archived; approved engineering replacement scope must govern their implementation.',
            'Exact host/code/artifact changes invalidate affected evidence; independent review is substantive, not an asserted PASS string.'])
    (HERE/'completion-repair-plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    with (HERE/'completion-repair-tracker.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.writer(stream);writer.writerow(['id','title','priority','lane','status','dependencies','original_cards','research_cards','owner'])
        for c in cards:writer.writerow([c['id'],c['title'],c['priority'],c['lane'],c['status'],','.join(c['dependencies']),','.join(c['original_cards']),','.join(c['additional_research_cards']),c['owner_role']])
    text=['# Repair, unblock and completion plan','',
        'This plan consolidates remaining work into24 completion packages. It preserves the89 original cards/301 criteria,209 checklist requirements and9research cards. All507 catalogued Python functions are allocated. None of these mappings marks a requirement accepted.',
        '', 'The [machine plan](completion-repair-plan.json) records full coverage, dependencies, input hashes, owners, acceptance and recovery. The [tracker](completion-repair-tracker.csv) supports assignment. Current scoped results and remaining failures stay in [execution progress](RELEASE_VALIDATION_EXECUTION.md).',
        '', '## Repair order and unblock strategy','',
        '1. FIN-01 locks the baseline and reconciles claims. FIN-02 resolves the host-only canonical-scan prerequisite alongside other work. An unchanged pre-start failure is not retried.',
        '2. FIN-03–06 and FIN-20 establish image/dependency, identity/ACL, database and interface safety. FIN-21 rights/archive review starts early. Independent CPU implementation continues while scan admission is blocked.',
        '3. FIN-08/10 begin typed values and source lineage. Then FIN-09/11/12/13/14 complete memory, retrieval, grounded responses, OCR/PDF and knowledge structures. Follow the explicit DAG for individual prerequisites.',
        '4. FIN-15–19 complete learning, engineering issue flows, utilization, performance and browser workflow. FIN-07 recovery expands for every schema/artifact change. FIN-20 adversarial/fault/coverage work runs throughout.',
        '5. FIN-23 closes deferred design/exclusion contracts without activation. After feature freeze, FIN-24 performs untouched-subject/demonstration acceptance; FIN-22 decides and executes the controlled CPU release only after every mandatory gate.',
        '', '## Decisions that prevent avoidable blockers','',
        '- The package DAG schedules independently testable work; acceptance still requires the original per-card dependencies and every associated criterion. This overlay never replaces the original dependency gates.',
        '- Managed scanner profile: host operator action, followed by effective-context verification and actual tool start. Windows elevated sandbox configuration alone is insufficient. Project code cannot retrofit the parent session.',
        '- Missing reviewer: assign a separate verifier for each slice now. Independent agents may verify narrow engineering results; human/domain/rights judgments must be identified where required. Reviewer-name metadata alone is not authenticated identity.',
        '- Package HIGH finding: reconcile the exact shipped source/version/caller before choosing a patch. Retain all28 current advisory results and the CVE exit code. Never suppress uncertainty to obtain a green dashboard.',
        '- Quality failures: build an independent oracle and sealed holdout first, repair the diagnosed mechanism, then rerun. Two rotated OCR pages, one unavailable TeX source, mathematics exploratory miss and earlier strict-citation/long-context failures remain explicit.',
        '- Scope: literal transcript processing is superseded by engineering issue assembly. Candidate optional CPU semantics exist; global index activation is not commissioned. AMD/Evolus, central activation, generated execution, voice and external signing remain disabled/deferred.',
        '- Resources: retain the existing CPU-first bounds and LIVE4K context. Use on-demand bounded workers, small deterministic baselines, actual tokenizer admission and predeclared quality/resource limits. Larger models/contexts/GPU services require evidence and explicit scope; unknown dollar costs stay unknown.',
        '- Evaluation contamination: the14 researched papers are development data. Final challenge requires a new subject beyond those seven topics, a frozen build and untouched labels. Any tuning invalidates that holdout.',
        '- Required feature cannot meet acceptance: retain FAIL/BLOCKED with cause, owner and concrete repair options. Do not silently remove a requested core feature, weaken a gate or present partial support as complete.',
        '', '## Completion punch cards','']
    for c in cards:
        text += [f'### {c["id"]}: {c["title"]}','',f'Priority: {c["priority"]}. Lane: {c["lane"]}. Status: {c["status"]}. Owner: {c["owner_role"]}.',
                 '','Dependencies: '+(', '.join(c['dependencies']) or 'none')+'.',
                 'Original cards: '+(', '.join(c['original_cards']) or 'new final challenge coverage')+'. Research cards: '+(', '.join(c['additional_research_cards']) or 'none')+'.','']
        text += [f'{i}. {step}' for i,step in enumerate(c['implementation_steps'],1)]
        text += ['', 'Acceptance:', '']+['- '+criterion for criterion in c['acceptance_criteria']]
        text += ['',f'Evidence: `{c["evidence_directory"]}`. {c["recovery"]}','']
    text += ['## Testing and evidence, separate from deployment','',
        'Each package retains a source/image/config/model/input-bound receipt, exact commands/exit statuses, expected versus actual observations, raw metrics and sample sizes, original fixtures, failed/retest chain, cleanup/recovery, limitations and separate reviewer decision. Validate item inventories and actual evidence bytes; an aggregate PASS or invoked command is insufficient.',
        '', 'Update status only when the complete criterion is demonstrated; a narrow reviewed result may close a subcriterion without accepting the entire card. Preserve old receipts as historical. Freeze corrections reopen every affected gate. Keep a curated redacted submission projection separate from private papers, vectors, credentials, reference sources and raw diagnostics.',
        '', '## Release and deployment boundary','',
        'The latest4bd candidate has706unit passes,31owned stack checks,587owned database checks and57runtime-file bindings. Those are baseline scoped evidence, not proof that all work above is finished. LIVE remains the privacy-only2ffe image.',
        '', 'FIN-22 requires all applicable original/research/checklist acceptance and real canonical security evidence. Rehearse backup, restore, upgrade and rollback before an immutable CPU deployment. Leave the existing denial guard intact until authentic evidence satisfies it. No publication, partner submission or deferred-provider activation is authorized by this planning artifact.',
        '', '## Plan validation','',
        'Run `python plans/implementation/build_completion_repair_plan.py` to regenerate and validate only these planning files. It checks89/301/209/9/507 coverage, nonempty allocations and an acyclic24-package DAG. It reads planning/evidence metadata and writes planning artifacts only; it never runs Docker, imports the application, reads secret values or changes the operative release extension.','']
    (HERE/'J_REPAIR_UNBLOCK_COMPLETION_PLAN.md').write_text('\n'.join(text),encoding='utf-8')
    receipt=dict(status='PASS_PLANNING_COVERAGE_ONLY',packages=len(cards),coverage=checks,dependency_cycles=0,
                 plan_sha256=hashlib.sha256((HERE/'completion-repair-plan.json').read_bytes()).hexdigest(),release_approved=False)
    (HERE/'completion-repair-validation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))


if __name__=='__main__':main()
