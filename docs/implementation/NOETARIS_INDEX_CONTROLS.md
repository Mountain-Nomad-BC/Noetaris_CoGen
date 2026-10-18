# Owner indexing controls: schema0039

The Docker API2978c0d1/frontend5d70cff5 candidate integrates owner cancellation, queued priority and explicit resume into the NOETARIS Task Queue. The exact bindings are in evidence/noetaris-integration/queue-controls-stage/current-evidence.json. This is scoped verification, not independent release acceptance.

## Authorization and data preservation

Cancellation applies to queued or running source indexing under current individual owner authority and an exact index-state epoch. It atomically invalidates the worker lease, records attributed immutable control details, and increments the index epoch. It retains original bytes, knowledge, existing checkpoints and any prior valid publication. Completed work cannot be cancelled. Failed or cancelled work can resume explicitly under a fresh lease.

Priority0 through9 applies only to queued jobs, within the existing fairness between owners and bounded global concurrency. A stale, shared-reader, admin-only, non-ingestion-role or background-lease request cannot change another owner's job. The API accepts strict bounded integers and cannot select the actor from request content. No control dispatches paid services or counts as an AI generation.

The Python control transaction validates source policy before taking job and audit locks. Queue changes and their complete source-bound audit entry commit together; audit failure rolls them back together. New event control_details retain actor, original epoch, resulting epoch and prior state/priority. Historical events receive an empty metadata field and jobs receive the declared default priority0; no historical actor or decision is invented. Upgrade checks compare every original column, including immutable event fields, and require all old journal timestamps unchanged.

While processing, the worker checks the exact SQL source/lease capability once per second. Lost authority cancels the pending encoder coroutine and releases its HTTP connection; it cannot commit more checkpoints or publish under that lease. A publication completed while the probe runs retains its actual completed result. A stale failure cannot report a nonexistent automatic requeue.

The UI binds observations and confirmations to exact source, job, epoch and server audit hash. Uncertain replies preserve the attempted action and body in the root store, survive navigation, and never auto-replay. Explicit observation does not invent attribution. Original documents remain accessible through the custody inspector. Private individual HTTP admission remains503, so positive private-owner UI control acceptance remains unqualified.

## Verification

- 1,408 backend tests passed in one bounded two-worker run, with API package/source checks and unchanged backend/test bytes. Four frontend paths changed afterward.
- The final frontend build passed80 contracts, including10 queue cases. Source checker and bundle build passed inside Docker.
- 375 browser assertions cover12 exact-image scopes. Ten passed scopes were retained from the original batch; the Atlas scope was rerun after correcting a fixture wait that matched the old graph before navigation committed. The diagnostic captured the new URL with the still-old graph header. The unchanged strict late-detail assertion then passed against the bound target source. The original failed batch and failed scope remain retained; this is not a clean original-batch claim.
- Twelve packaged runtime checks used actual HTTP cancellation and real MiniLM vectors: a real checkpoint survived cancellation exactly, its pending HTTP request disconnected, explicit resume reused the same job with a new lease, and real encoding completed full atomic publication. No successful vector response was fabricated.
- Fourteen schema38-to39 upgrade checks preserve all original columns, sequence state, originals, partial checkpoints and full26k-plus answer history. Previous API38 refuses namespace39. Independent upgrades record their own new migration timestamps; every older journal row and timestamp remains exact. The initial overstrict timestamp-comparison failure remains retained.
- A fresh50-table clone restore compares complete rows, ownership/ACLs, definitions, sequences and settings, including priority/cancelled state, attributed control history and audit hashes. Existing structured analyses, OAuth revocation, credit ledgers, reflection and claim/governed history remain in that recovery fixture.
- Candidate/source and prior-image archives were locally saved, hashed and loaded. All44 imported originals and both protected dumps matched their retained hashes at publication. Live services were not replaced or migrated.

The one local Qwen case took12.362seconds under2CPU/2threads/4GiB/context4096. This does not establish a latency distribution, cold-start result, capacity, or that this change caused a speed improvement. Earlier timeouts remain retained.

## Rollback and remaining gates

Prefer a forward repair preserving namespace39, its lease guards, all control history and subsequent writes. The old API refuses the new namespace. Do not drop privacy/lease guards, delete checkpoints/events, or rewind live data to discard later writes. The previous API38/frontend9d572c33 pair and exact images are retained for isolated clone rehearsals; frontend-only rollback is not qualified against new cancelled states.

The exact12-path change map is in evidence/noetaris-integration/queue-controls-stage/changed-files.json. Private-owner HTTP/UI acceptance, inference queue UI, ten supplied placeholder routes, wider operational expansion, voice, provider commissioning, held-out quality/capacity, managed security/rights review and independent release acceptance remain open. Upload limits and zero-cash policy are unchanged.
