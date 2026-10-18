# Data preservation acceptance

User requirement: preserving data is mandatory alongside accuracy and clean,
traceable representations. Status: **implementation and qualification in progress;
no release acceptance**.

Both original-byte integrity and derived coverage must be demonstrated. A matching
original PDF hash does not establish complete text, image, table, formula or OCR
extraction. Unsupported or incomplete content must remain visible as such.

| Required behavior | Evidence required before acceptance |
|---|---|
| Preserve original uploads | Rehash every accepted original after ingestion, indexing, restart, migration and fresh-container restore; compare with the input manifest. |
| Account for derived content | Reconcile page inventory, native/OCR/blank/failed/unsupported states, source spans, chunk intervals and published vector coverage. Reject partial publication and report extraction gaps. |
| Preserve transformations | Keep original bytes and raw-to-normalized lineage. Retain a hash-bound pre-OCR native representation when OCR becomes the active extraction; reject missing, nested, corrupted or foreign-source snapshots. |
| Preserve generations and retries | Failed jobs retain accepted originals and valid checkpoints. Idempotent retries cannot duplicate or silently replace immutable content; a failed new generation cannot replace a valid publication. |
| Recover complete application state | Compare every public table's row count and canonical row multiset digest, sequence positions, original bytes, artifact integrity, publication state and access isolation after restoring into a fresh owned container. |
| Distinguish selection from loss | Bounded retrieval, memory projections and UI pages must identify scope and omissions. Those projections do not replace the stored source or imply exhaustive coverage. |
| Prevent unintended removal | Retention/deletion remain disabled unless their separately authorized and tested workflow applies. Qualification cleanup targets only resources created and labeled by that run. |

Current work adds native-extraction snapshots to OCR output and persisted source
metadata, with a new OCR output version. Historical OCR results without those
snapshots cannot be described as having retained that intermediate representation.
Original bytes remain the reconstruction source; reprocessing requires an explicit
new generation rather than rewriting historical evidence.

The [private recovery fixture](../../evidence/implementation/private-upgrade-recovery/nsai-upgrade-74b1661b54e4/receipt.json) passes 32 scoped checks, including differing native/OCR candidates and exact raw-text, snapshot and original-byte preservation.
The real research-corpus runner is being extended to rehash all originals and compare
complete logical database state after a quiescent backup and fresh-container restore.
Synthetic OCR fixtures qualify preservation behavior, not recognition accuracy.

Concurrent-write backup, host power-loss recovery, PITR, accepted RTO/RPO targets,
representative workload coverage and independent review remain separate open gates.
No deployment or user-data deletion is authorized by this document.

## Retained evidence for the existing corpus

- [Original corpus custody](../../evidence/data-preservation/existing-corpus-adc7072fec1f4fdba816e69360072b91/receipt.json): all 174 declared files across 14 papers match their size/SHA manifests, including original acquisition/preparation custody.
- [Existing backup custody](../../evidence/data-preservation/existing-backup-4f774a71fe1e44639d21a1d74cbabf16/receipt.json): the 32,718,095-byte dump matches its recorded SHA-256. Capture-time `restore_verified:false` metadata is preserved.
- [Separate fresh-container restore](../../evidence/data-preservation/existing-restore-detail-a95d5b2e4ae249eda829bc8fb114eaaa/receipt.json): all 14 originals, persisted knowledge and embedding artifacts, prepared embedding payloads and 23 supplement checksums pass. The earlier restore also matched all eight historical table counts. No original files, backup bytes or live service were changed.

The retained failed diagnostics compared historical embedding payloads against a
newly normalized generation. The exact prepared payload hashes match the restored
payloads; renormalization introduces differences no larger than 5.6e-17. Recomputing
a transformation is not a byte-custody test and must not rewrite immutable history.
These observations do not establish arbitrary legacy compatibility, complete page
extraction, all-table logical equivalence with the original live database, or recovery
under concurrent writes.

[Current real-service browser evidence](../../evidence/grounded-application/f9de2f407d72430c97c68f847cb467bd/grounded-receipt.json)
passes original download custody and retention of the complete pre-OCR native
representation with the actual OCR worker. Its four synthetic right-angle raster
pages qualify integration and geometry, not general recognition accuracy.

## Fresh-corpus recovery harness corrections

The new current-corpus backup path now retains PostgreSQL ACLs rather than omitting
them, and bootstraps its owned application role with the same bounded private test
credential before restore. It compares every public table's row multiset and all
sequence positions, then separately compares authorization definitions and ACLs and
uses the actual packaged application to rehash originals and check private isolation.

Failed smoke attempts remain retained: `cbae7685` failed application authentication;
`6a72c146` failed the application's access-definition seal; `6d79c377` isolated the
ACL mismatch (PUBLIC execution entries increased from 2 to 53 after an ACL-free
restore). No acceptance or data rewrite was used to bypass those refusals. The
historical byte-custody restore above used no-ACL restoration solely as a diagnostic
and does not qualify an application-ready database.

The older `scripts/verify_recovery.py` has now been repaired to enumerate all public
tables, retain restored ACLs, compare access definitions and sequences, and recheck
backup size/SHA before consuming it. Its disposable target uses the exact database
image, a fresh test credential and no live secret mount. Cleanup requires the exact
run label and cannot classify a Docker-daemon failure as successful removal. Evidence
is written per run instead of overwriting a previous recovery receipt. The diagnostic
role is NOLOGIN: this command explicitly does not qualify application login/restart
or role-state restoration. No live invocation was performed during this repair.

[Six fresh database checks](../../evidence/data-preservation/legacy-command-13d89ad034e94203ad8c12b7a32d1e09/receipt.json)
cover all twelve fixture tables outside the old fixed list, detection of a changed
row with unchanged counts, ACL-preserving fresh restore, exact access/sequence
comparison and detection of an unintended public execution grant. Four additional
cleanup regression cases cover owned, absent, foreign-owned and unavailable-daemon
states. The complete focused operations/recovery batch passes 41 checks.

[Corrected full-table smoke recovery](../../evidence/reference-capacity/9d2ea56ba7054e56a4767b5ab1d24280/capacity-receipt.json)
passes on the current exact API/database/encoder images: two synthetic originals,
six pages/vectors, all 40 public-table row multisets and sequence values equal,
authorization definitions and ACLs equal, actual packaged application original hashes
and publication readiness verified, and second-user private isolation preserved.
Owned cleanup completed. This is a small quiescent recovery workload; it does not
qualify the failed 14-paper corpus ingestion, P0/P1, concurrent writes or power loss.

## Database process-crash recovery

[Current SIGKILL rehearsal](../../evidence/process-crash-recovery/118d163e6f1744cca9875720785b24fd/receipt.json)
passes six scoped checks in 171.17 seconds against the current packaged application
and database. The 600-second work deadline covers coordinator and per-table SQL
commands; owned cleanup remains available afterward. A prior pass is also retained.

With fsync, synchronous_commit and full_page_writes enabled, two acknowledged
synthetic private sources and a saved indexing checkpoint survive an actual database
SIGKILL and restart of the same owned persistent cluster. Every committed row in all
40 public tables matches its pre-crash fingerprint. A separate source transaction,
observed still open before the kill and never acknowledged as accepted, rolls back.
The actual packaged application then verifies originals, the complete exact pre-OCR
native snapshot, published index, checkpoint reuse and second-user isolation.
Sequence gaps after aborted transactions are valid PostgreSQL behavior and are
reported separately from committed row preservation.

This qualifies database-process interruption of this small synthetic workload. It
uses synthetic vectors and a synthetic alternative OCR result, not quality acceptance.
It does not prove host/VM power-loss survival, disk/controller durability, arbitrary
concurrent-write backup, PITR, RTO/RPO, maximum-capacity recovery, a long-lived API
connection pool across restart, or independent release acceptance. No live system,
user volume or source file was changed; the newly owned test volume was removed.

## Bounded verification scratch and final regression

[Fresh COPY/Unicode/overflow qualification](../../evidence/data-preservation/legacy-command-c2d8c131f3b24b73a33fb3f3d30b6e52/receipt.json)
passes eleven checks. The recovery command retains its existing COPY fingerprint
format and 256 MiB per-table limit, now enforced while bytes arrive by the bounded
backup stream. Server sort scratch is also bounded. Golden row hashes remain
compatible; Greek, a decomposed combining mark, math and multiline text survive
restore exactly. Oversized output fails and leaves no partial file or scratch
metadata; callers cannot disable or increase this byte limit.

The [single-worker regression](../../evidence/private-access/fe2994b1a5a84affb33f3fac44fe1b86/receipt.json)
exceeded its unchanged 1,800-second deadline and remains FAIL. Its interrupted
owned database was removed with an [immutable cleanup follow-up](../../evidence/private-access/fe2994b1a5a84affb33f3fac44fe1b86/cleanup-followup.json).
No original capture or failed receipt was rewritten.

An explicit two-worker regression profile retains the same overall work deadline,
keeps whole test files together and uses independently named disposable database
fixtures. It inventories every collected test and requires exact JUnit identity
coverage once each, with no skipped, missing, extra or duplicated cases and matching
case/summary outcomes. Historical durations affect scheduling only. Default
single-worker behavior and all application/container safety limits are unchanged.
The focused operations/recovery/scheduler suite passes 54 checks; the full new
profile has now completed as recorded below. Its evidence is not independent release acceptance.

## Current integrated preservation evidence (2026-10-15)

[Fresh read-only custody refresh](../../evidence/data-preservation/custody-refresh-6e6a5a20f7aa427b8b76603b1795d1e1/receipt.json)
passes 192 checks: the original 174 declared checks plus one retained author-source
input previously omitted when its unsupported projection had no output files,
14 raw acquisition PDFs and their manifest, and the existing database dump and
capture manifest. All original custody sets match. Earlier checker attempts failed
on the optional `files=None` inventory and then on the expanded file count; none
reported a byte mismatch. No user file or capture manifest was rewritten.

[Exported-snapshot boundary rehearsal](../../evidence/data-preservation/snapshot-boundary-e4265dbd87d04fbcb4125c8d1a1fac17/receipt.json)
passes on API `febe1bbf`. Two actual application sources commit before an exported
snapshot; another commits afterward, before dump consumption. Fresh restore has
exactly the earlier rows in all 40 public tables; both earlier originals rehash
and second-user isolation is preserved. The later accepted source remains in the
source database and is honestly absent from the earlier backup. Sequence state
is recorded separately because sequence increments are not MVCC snapshots. This
does not prove writes during dump, scheduled/off-host backups, PITR, host power
loss or zero disaster RPO. Earlier harness startup failures remain retained.

The [current-image real browser workflow](../../evidence/grounded-application/12aa1ae3491e4083a82a3436f37665b5/grounded-receipt.json)
passes and [license/NOTICE delivery](../../evidence/package-license-delivery/74730158fef649e4894d7b4c46c298cf/receipt.json)
matches bytes. Neither establishes private HTTP admission, quality, rights or
release approval. A [further 14-paper replay](../../evidence/reference-capacity/36dd683217f94b45b5a298a23b44298b/capacity-receipt.json)
passes with full-table restore on API `febe1bbf`, alongside recorded shared-host
qualification work. The earlier intermittent 503 is still unresolved.

Two additional gaps have failing reproductions and repairs pending the frozen P1
run: [an existing partial model download is deleted on failed retry](../../evidence/implementation/model-partial-custody-before.txt),
and [temporary initialization socket readiness can precede final TCP readiness](../../evidence/data-preservation/database-readiness-b7495dbf4c6e4eb4b6374382f40e8888/receipt.json).
The staged acquisition repair passes three disposable-file checks; it is not yet
applied to production source. The readiness reproduction modifies only a newly
owned database initialized with a deliberate pause. User models/data are unchanged.

Follow-up recovery-verification repair: [the failing unused-sequence reproduction](../../evidence/data-preservation/sequence-state-8bbc5bbc3b0741e781d7d51f8a399121/receipt.json)
showed that `pg_sequences.last_value` hides an unused sequence's seed. Recovery
comparisons now read actual sequence relation state (`last_value`, `is_called`)
and generation settings (type, start, increment, bounds, cache and cycle).
[Six fresh PostgreSQL checks](../../evidence/data-preservation/sequence-state-2a8bcfcfa097448a88577c8a07e6fde8/receipt.json)
distinguish altered seeds/settings using independently observed next IDs. The
bounded identifier inventory rejects unsafe, duplicate or excessive names.
Forty-nine focused operations checks passed. The rebuilt API candidate is
`febe1bbf`; [full regression passes all 1,064 cases with zero skips](../../evidence/private-access/6cf9f03995f14c2fb011feef8d44cccb/receipt.json),
exact collected coverage, unchanged inputs and completed cleanup. Its [small all-table restore passed](../../evidence/reference-capacity/d9f80864de8b4a9286d1884b8c8b7596/capacity-receipt.json)
with the stronger sequence comparison, as did [eleven fresh legacy recovery checks](../../evidence/data-preservation/legacy-command-efd9d90cf97a4824b03d66c74306c6cc/receipt.json).
Earlier receipts below retain their original image and verification scope.

Current API candidate is `3b0fd264`, OCR candidate `6d724dfd`, and encoder
candidate `d8e8c44b`; exact full identities are retained in the linked receipts.
The [fresh full regression](../../evidence/private-access/268fd650a2694d59bcf0359687cb7d28/receipt.json)
passes all 1,056 collected cases exactly once, with zero failures, errors or skips,
verified packaged source, unchanged inputs and completed owned cleanup. The prior
1,042-case pass predates the inline-image repair; failed and interrupted runs remain
retained. Host unit Python and packaged application Python remain distinct.

A [real PDF reproduction](../../evidence/data-preservation/inline-image-probe-5ed923fa7f694647a57c941673a2d129/receipt.json)
exposed an extraction-completeness bug: native text plus a visible inline image
could be classified as fully extracted. The repair detects actual inline-image
operations, including indirect resources and empty resource dictionaries, without
treating literal image-marker text as an image. The [same original PDF now passes](../../evidence/data-preservation/inline-image-probe-9553001542994f1b89dc62791b2d3458/receipt.json):
native extraction requests OCR, the real raster contains ink, and the isolated OCR
worker retains the entire exact native snapshot before replacement. Native version
3 / OCR version 4 distinguish the changed behavior; legacy native-2 / OCR-3
snapshots remain readable. The focused parser/history/geometry batch passes 55
checks. This synthetic fixture does not establish general OCR recognition accuracy.

Current-image recovery results:

- [Private upgrade/restore/resume](../../evidence/implementation/private-upgrade-recovery/nsai-upgrade-aa7eef430226/receipt.json): 32 scoped checks, including exact original and pre-OCR history retention, grants/revocation and checkpoint reuse.
- [Database SIGKILL recovery](../../evidence/process-crash-recovery/d1e5ecd6e59d43a2a5c2492304357fde/receipt.json): six scoped checks, all 40 committed table row multisets preserved and an unacknowledged source transaction rolled back; owned persistent volume removed afterward.
- [Full-table quiescent restore](../../evidence/reference-capacity/0fe30ff54e704732abd430dc5df68d38/capacity-receipt.json): two synthetic PDFs / six pages, exact table rows, sequence positions, authorization definitions and ACLs; actual application original hashes, publication readiness and second-user isolation verified.
- [Existing user backup through current migrations and application](../../evidence/data-preservation/existing-current-upgrade-f41ab45d27a045899421b4cf961eecb1/receipt.json): all 14 original downloads and 14 knowledge artifacts match expected hashes after isolated restore and migration through 0029. Original archive and its capture-time manifest remain unchanged.
- [Real-service browser](../../evidence/grounded-application/131904e432494e64b857645be751eb0b/grounded-receipt.json): current API/parser/OCR/encoder/database/model, original download hashes and retained extraction snapshots, native and rotated/cropped OCR citations. Individual-user HTTP content remains withheld.

These checks do not establish host power-loss durability, concurrent backup,
PITR, RTO/RPO, maximum-capacity recovery, independent recognition quality or full
release certification. Current [P0 sparse-workload qualification](../../evidence/reference-capacity/2fdc24fcdae44e29b0893c5b9f45bb0f/capacity-receipt.json)
passes 100 PDFs / 5,000 pages / 5,000 vectors, repeat-upload idempotency, complete
pagination and second-user isolation. Warm retrieval median is 0.88 seconds and
p95 0.93 seconds; database/index caches were used during ingestion. This is not
maximum-capacity recovery or dense/mixed/OCR capacity acceptance. The separate
[current real-paper attempt](../../evidence/reference-capacity/888e95481c37403688bba8002aef5897/capacity-receipt.json)
fails after ten accepted originals / 159 pages with a backend 503. A [diagnostic rerun](../../evidence/reference-capacity/b940c0888e9d4953aa9832b5e407fa17/capacity-receipt.json)
passes all 14 originals / 240 pages / 1,233 vectors and full-table isolated
restore on API `3b0fd264`. The intermittent 503 remains unresolved; a passing
retry does not remediate it. The diagnostic fixture now records internal type,
SQLSTATE and traceback frames without error messages, source text or credentials
if it recurs. User originals remain untouched and owned cleanup completed.
The [current raw package scan](../../evidence/package-risk/e80329dc797a40549d93d32de9489de2/package-receipt.json)
still reports nine HIGH package entries across five images; package acceptance,
managed-host security scanning and independent review remain open.


## Live-library preservation and legacy indexing ? 2026-10-15

The [read-only live inventory](../../evidence/data-preservation/live-readonly-ad41d3c30956487c85ebe66d05b19d27/receipt.json) found 20 original byte records, no missing originals and no hash mismatches. The live PostgreSQL data directory uses its existing named volume, with fsync, synchronous_commit and full_page_writes enabled. This inspection made no database changes.

A [protected local backup and independent restore](../../evidence/data-preservation/live-backup-ac6e8ae3f38e48ff90ae601b78859ec6/receipt.json) preserved all 11 historical table row multisets, sequence definitions/state and access controls. The 63,468-byte archive has SHA-256 `0441db9feb9238414c72beb2025f322213bc4e11c1b4c828ae28d6faeeae8b12`; its directory and files admit only the current Windows account and SYSTEM. The capture manifest remains unchanged. This establishes a tested local recovery point, not off-host disaster recovery, scheduled backups, PITR or zero data loss since capture.

The [current packaged application on a restored copy](../../evidence/data-preservation/live-current-upgrade-abba42af7e2349abbb62c82487ca7b85/receipt.json), API `f89b0ab1`, migrates and preserves every original column value and all 20 original hashes. New legacy commissioning builds derived artifacts from the exact retained spans, leaves historical files/manifests/locators untouched, queues durable jobs and publishes through the real encoder. All 20 jobs became ready and source-scoped retained-text queries retrieved each source with semantic retrieval available. A repeat preparation batch queued nothing. Extraction completeness remains explicitly unverified for parser-1 history.

The prior [failed integrated check](../../evidence/data-preservation/live-current-upgrade-4cbc0454e75342658c2961eefd38ef8a/receipt.json) reached publication but incorrectly required a generic question to match every document. The corrected check uses retained source excerpts; it does not certify held-out question relevance or answer quality. All runs operate on owned restored copies; the live database has not been migrated or backfilled.

The model-partial custody and final TCP-readiness repairs are now applied, with [1,071 regression checks passing](../../evidence/private-access/a751fadee1bc4a18a3f4e3ff5e9bb4e1/receipt.json) on the preceding API `2e9c503e`; earlier pending-work descriptions are historical. The [1,000-PDF / 50,000-page sparse measurement](../../evidence/reference-capacity/b22153b5fda741329b0fe736807514cb/capacity-receipt.json) completed on API `febe1bbf`: warm median 8.73 seconds and p95 11.46 seconds, with co-running checks explicitly recorded. This is measured capacity, not independent latency acceptance or dense/OCR capacity qualification.

No release criterion is accepted by these scoped checks. Individual-user content access, independent security/rights review, managed-host scanning, operational disaster recovery, and the unresolved intermittent research-ingestion 503 remain open.


The [injected preparation-failure rehearsal](../../evidence/data-preservation/live-current-upgrade-cba0c1f7c53146b093adc158fcb6d448/receipt.json) verifies transaction rollback after artifact/audit preparation and before enqueue completion: artifact count, audit head and index state remain exact. Normal retry then publishes and retrieves all 20 originals; repeat batching remains idempotent. Cleanup completed. This is an application transaction-failure check, not host power-loss evidence.


The [final concurrency rehearsal](../../evidence/data-preservation/live-current-upgrade-968b14d6b12f4c30bf9db775054af9cd/receipt.json) adds two simultaneous preparations of the same legacy source: exactly one queues a job; the other returns its existing state. The remaining batch completes all 20 sources, with exact historical row preservation and original hashes. The same API image passes [1,091 tests with zero skips](../../evidence/private-access/18e86b7041d444ada48d92aac08a38df/receipt.json) and a [fresh real-service browser run](../../evidence/grounded-application/b749e6c94553480ab047abfaf11d68ac/grounded-receipt.json). Owned cleanup completed for each run. This closes the scoped legacy projection implementation, not independent acceptance or live commissioning.


## No-cash operational continuation

The user's correction prohibits cash dispatch; migration 0031 disables cash without deleting historical accounts/events, and migration 0032 adds durable operation admissions. The [current existing-library rehearsal](../../evidence/data-preservation/live-current-upgrade-a4789e599cba4722880448eda696870d/receipt.json) preserves every historical original column value and all 20 original byte hashes through these migrations, publication/retrieval, repeat/concurrent preparation and injected rollback. The [44-table synthetic recovery](../../evidence/operational-cost-recovery/545e339e6f40441ea91760f543cfd210/receipt.json) preserves credit history, unknown reservations, disabled cash and live/queued operation records, with all rows, ACLs/access definitions and sequence seeds/state/settings compared. Existing backups, originals and live services remain unchanged. This is not host power-loss, PITR, off-host backup or RTO/RPO certification. See [operational evidence and limitations](ZERO_CASH_AND_SHARED_OPERATIONS.md).
