# Capacity repair engineering notes

Status: ongoing implementation; no independent P0/P1 or full release acceptance.

Latest completed P1 scoped measurement is [d6edd57a](../../evidence/reference-capacity/d6edd57a03e943f99224af90b5e16a02/capacity-receipt.json): 1,000 generated sparse native PDFs, 50,000 pages/vectors, publication in 754.008 seconds and 31 successful retrievals (30 warm: median 8.07845 seconds, p95 8.32179 seconds). Migration 0024 fixes the reused-session generic lexical plan regression; the first five calls alone had concealed it. Exact image predates subsequent accounting, UI and upload-profile changes. This is neither dense/mixed/OCR/contention qualification nor independent SLO acceptance. Canonical semantic JSON and physical native-index growth remain separate measurements.

The sections below retain historical diagnostics, including failed and then-running measurements. Current execution status is in [workspace progress](RESEARCH_WORKSPACE_PROGRESS.md).

## Historical engineering snapshots

Current continuation: the prior P1 run f0479e00 published all 1,000 sources and
50,000 pages/vectors before lexical retrieval timed out. Migrations 0020–0023
move metadata materialization after ranking, avoid equivalent duplicate lexical
scoring, and derive immutable native double arrays transactionally from canonical
vectors. Native rows have no direct application grants and remain source-bound.
The 0023 diagnostic c29d1116 used the same 50,000 synthetic dense-vector seed and
completed in 3.98/4.16/4.21 seconds without instrumentation (4.80 instrumented).
Its actual nested plan shows the authorized CTE as the outer scan and 1,000
source-correlated native index scans, each constrained by source/model/generation.
This is query-plan evidence, not corpus quality or capacity acceptance.

The rebuilt API candidate 40d89a63 passed the real-encoder 25-check pipeline
de797cb7. A new actual PDF/model P1 measurement 95013381 is in progress.
The harness now records generated PDF hashes and native-index physical bytes,
retains source/fixture hashes even on failure, and labels the first post-ingestion
query honestly: the database and encoder are already warm, so it is not cold-cache
evidence. Canonical JSON budget accounting excludes derived native-index bytes;
physical database/index growth is measured separately. No live limits changed.

Completed staged mechanisms: server library paging/title filtering; natural-language
library retrieval; bounded FIFO encoder admission; actual overlapping two-worker
pipeline; compact source dependency manifests with authorization on resolution.
These do not remove the remaining capacity gates.

Latest staged repairs: ordinary evidence now selects passage claims and one witness
per distinct raw alternative for those groups. Memory selects at most 12 lexical
seeds and expands their conflict witnesses. Duplicate statements at the same source
location are compressed without merging distinct raw values; Python retains exact
quantity comparison. Overflow raises before synthesis. A real PostgreSQL test with
2,100 duplicates, 2,100 unrelated groups and an inaccessible private alternative
preserved the authorized conflict without whole-corpus Python materialization.
These synthetic rows do not qualify ingestion throughput or P0/P1 capacity.

Migration 0017 now returns every semantic passage source segment; the application
uses all segment locators for claims and conflict analysis. Column definitions are
now included in the runtime database seal; 13 drift cases pass. Remaining original
notes below describe intent and investigation targets, not wholly unfinished code.

Additional completed mechanisms: review uses authorized server keyset pages with
independent counts and explicit unknown conflict summaries on overflow. A 6,202-row
synthetic fixture and an exact Fahrenheit/Celsius fixture passed. The audit/share
lock-order investigation reproduced DeadlockDetected; source authorization now
precedes the global ledger lock, with both real transactions committing in the
regression. This qualifies that cycle, not arbitrary multi-source concurrency.

The current browser includes OCR word-region fallback, checking source/page/quote,
coordinate custody and unique page-local matching. The 24-check browser run uses
an actual pinned OCR response and independently measured raster fixture, including
zoom, actual canvas ink, coordinate tampering and duplicate/no-match fallbacks.
Broad OCR classes and native font/page geometry generalization remain open.

A new owned reference-capacity harness first passed 2 PDF / 6 page smoke integration.
Two actual 100 PDF / 5,000 page P0 measurements passed their scoped mechanics.
Baseline d8dae7c1 published all 5,000 vectors in 78.29 seconds; 30 warm samples
had median 10.09 seconds and p95 10.44 seconds. Migration 0018 authorizes lexical
sources before chunk ranking and decodes semantic vector maps once per document.
Repeat 74e4dda0 published in 79.52 seconds with warm median 2.56 seconds and p95
4.04 seconds. These are single-machine pairs, not a signed performance SLO.

The resource-limit audit reproduced cross-owner source-count and semantic-byte
admission bypasses caused by row filtering. Migration 0019 adds a global Boolean
source-admission decision and transactional semantic-byte accounting, without
exposing private counts. Full-budget failure leaves no partial publication.
Default 100 docs / 2,000 claims / 128 MiB canonical semantic JSON is unchanged.
The explicit operator-only reference-1000 profile permits the proposed 1,000 docs
and 512 MiB semantic JSON for isolated measurement; it is not release acceptance.
File upload bounds and private HTTP admission remain unchanged.

The first 1,000 PDF / 50,000 page P1 measurement is running, bounded to 30 minutes
with 1 CPU per component, 3 GiB database RAM and 2 GiB database tmpfs. Generated
native English pages are mechanism/capacity inputs; they are not a held-out
relevance or OCR/LLM-contention acceptance workload. Mixed workloads, fairness,
recovery, backup growth, upload envelopes and independent capacity acceptance remain
open even if this measurement finishes.

Next implementation sequence:

1. Replace whole-corpus claim loads in ordinary evidence/memory with query-relevant
   candidate groups and complete, bounded conflict witnesses. Common identical
   statements across many documents must not hit the 2,000-row projection limit.
   Never hide a conflicting value behind a result limit. If alternative analysis is
   incomplete, quarantine that group's canon and withhold model synthesis explicitly.
   Preserve exact Celsius/Fahrenheit rational equivalence and supported Unicode
   behavior; do not introduce an approximate equality key to simplify indexing.
2. Semantic passages may contain multiple source segments. Propagate their locators
   into the conflict/review projection; checking only the first locator can miss a
   statement later in the returned passage. Keep citation source/hash/page binding.
3. Page the review surface and compute authorized summaries independently of the
   displayed page. One failed projection must not make the library unusable. Source
   and claim admission limits remain unchanged until the relevant measured gate.
4. Measure the JSONB cosine path with bounded owned workloads before choosing a new
   dependency. pgvector is an option for native exact distance, not yet installed.
   Official v0.8.7 documents PostgreSQL 13+ and exact/approximate search:
   https://github.com/pgvector/pgvector/blob/v0.8.7/README.md . Any adoption needs a
   pinned source/archive/license, hardened database build, schema/grant/restore
   qualification and independently reviewed package risk. Preserve authorization
   before ranking; approximate search cannot silently substitute incomplete recall.
5. Extend the runtime definition seal to column types, collations, nullability,
   generated expressions/defaults before adding generated identity/index columns.
   Existing policy/function/trigger/constraint/grant checks remain binding.
6. Profile repeated private RLS checks. A future transaction-local authorization
   fast path must expire with grants/membership, distinguish roles, retain source
   policy/group locks through commit, preserve job lease bounds and committed admin
   auditing, and never survive transaction or identity changes. No cache optimization
   is accepted from reasoning alone.
7. Reproduce multi-source/private audit and sharing lock order with real concurrent
   connections. Source/group locks followed by a transaction-held global audit-head
   lock may produce a cycle if another operation holds a later source/group. This is
   still a wider investigation target. The single audit/share cycle above has been
   reproduced and repaired; do not rewrite historical ledgers.
8. Qualify actual CPU grounded generation separately from encoder/retrieval checks.
   Citation ID/anchor fixes do not establish explanations or claim entailment. Keep
   numerical, entity, comparison, contradiction, subject-switch and refusal oracles.

Complete source lineage must remain resolvable. Migration 0016 uses opaque immutable
references, rechecks every source, and leaves the complete 16 KiB memory transport
bound intact. Full result receipts still enumerate their complete dependency sets.

Independent reviewers, approved workload/quality contracts and the managed-host
canonical scan remain external prerequisites. Existing live services, credentials,
user content and limits have not been changed.
