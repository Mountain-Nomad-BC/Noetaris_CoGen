# NOETARIS source indexing queue

Current controls have advanced to schema0039; see [owner indexing controls](NOETARIS_INDEX_CONTROLS.md). The initial queue scope below is retained as implementation history.

The supplied `/app/queue` placeholder now connects to the existing authorized document pages and source-index status/retry APIs. This is the source indexing queue; inference scheduling, job cancellation and editable priority still need their own integration. Backend permissions remain authoritative and individual content admission remains503.

## Behavior and preservation

The queue supports explicit search and25-row cursor pages across the visible source library. Counts and observations are not a frozen queue snapshot. Selecting a source reads its exact job, index state version, attempts, completed/total passage counts, coverage, failure code and searchable publication state. Unknown progress stays unknown. Publication does not imply review or factual authority. Sources link back to the custody inspector without changing original bytes.

Retry is available only for a fresh failed observation, an admitted individual identity with ingestion permission, and source metadata declaring current ownership. The backend independently checks ownership, exact expected index epoch and terminal failure. It does not grant retry authority to legacy service operators or shared readers. Wrong-source or unsafe epoch responses are rejected.

The root-mounted store retains up to100 retry observations without silently evicting them. Failed or malformed mutation responses remain uncertain; there is no automatic retry or implicit status read. An explicit fresh read records an observation without inventing an audit receipt or attributing the change. A new retry requires explicit acknowledgement when the job is still failed. Identity cleanup aborts requests, clears retained state and rejects late writes; source switching rejects late status replies. No source, checkpoint, job or audit row is deleted by this UI.

## Evidence and current limits

The staged Docker image9d572c33 passed76 frontend contracts, including six new queue cases. The staged isolated stack passed22 browser/API assertions:30 sources over multiple pages, one actual local encoder publication, failed progress, exact job binding, a held real status response across a source switch, authorization negatives, logout, five widths and original-byte hashes. Test sources were synthetic owned fixtures. A terminal failure was seeded explicitly in that disposable database; positive HTTP source/status/publication responses were actual backend responses. No paid inference was dispatched. The current frontend has98 source files; the change map has eight paths in evidence/noetaris-integration/queue-stage/changed-files.json.

Actual positive private-owner retry UI certification remains gated by individual HTTP503. The lost-response and retry ownership contract checks use an injected transport at the store seam and do not substitute for that end-to-end qualification. Earlier fixture failures are retained: the first incorrectly expected403 instead of the backend's concealment404; the second tried selecting a source absent from its current page. Both were corrected without changing production authorization. A local static-check attempt lacked the staged TypeScript dependency; the actual Docker build installed the locked dependencies and passed the source checker and all76 contracts.

The exact APIbb6238af/frontend9d572c33 pair now passes368 browser assertions across12 scopes, including30 chat assertions with an actual local Qwen generation (35.225seconds in the bounded2CPU/2threads/4GiB/context4096 case). This is not latency, cold-start or five-user certification. The unchanged API/package/test bytes retain the prior1383-test single-run result; eight later frontend changes have their own76-contract build and368 browser assertions. The prior complete pair is preserved in pre-queue-current-evidence.json.

An additional18 actual PostgreSQL/application-function checks pass in owner-retry-9d6b39ab741244b7a9907f934ee3329b/receipt.json. They verify current owner retry, shared-reader/admin denials, stale and duplicate epochs, retained original bytes and immutable knowledge, and exact checkpoint vector/coverage recovery under a new lease. The normalized vector is synthetic lifecycle data, not semantic-quality evidence. Actual ASGI private HTTP still returns503; these checks do not certify positive owner HTTP/UI access.

Current source/test ZIP and exact candidate/rollback image archives are retained under state/backups/governed-candidate-27fc41429da446b3b01ddae3be9269da. Hashes and bindings are in evidence/noetaris-integration/queue-stage/current-evidence.json. All44 original imported files and both protected dumps were rehashed unchanged at publication. Ten supplied placeholder routes remain, alongside the explicitly unfinished queue controls.

## Retention and rollback

The pre-queue frontend40c7da76 is retained under `nsai-noetaris-hold:pre-queue-40c7da76`. This increment changes eight frontend paths and no database/API source. Before reverting frontend files, preserve any subsequent work and compare exact hashes against the saved baseline; use the held image for an isolated rehearsal first. Reverting presentation must not rewind database jobs, originals, grants, reviews or later writes. Live resources were not changed.
