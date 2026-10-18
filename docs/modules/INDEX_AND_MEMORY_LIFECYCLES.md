# Distinct lifecycle machines — no authority confusion

## 1. Document lifecycle

`RECEIVED → HASHED → PARSED → SPAN_MAPPED → CLAIMS_EXTRACTED → COMPLETED` with failure transitions to `QUARANTINED` (never silently accepted). Source bytes are immutable per `sha256+revision`. New source revisions create new identities/events, not rewritten blobs.

## 2. Claim lifecycle

`CANDIDATE → REVIEW_PENDING → VERIFIED` (with authorized independent actor), or `CONTESTED`, `REJECTED`, `SUPERSEDED`. State derives from append-only events. Conflicting candidate versions can both remain visible, and a reviewer may determine insufficient evidence rather than selecting one.

### Temporal dimensions

`observed_at`: time evidence was entered/visible to NSAI. `valid_from/valid_until`: source-domain effective interval. `recorded_at`: event persistence time. These must be indexed and timezone-aware. A revised manual issued later cannot falsify what a previous version said earlier.

## 3. Retrieval index lifecycle

`BUILDING → CANDIDATE → VALIDATED → ACTIVE`; any failure -> `FAILED`, active index may roll back to **previous** `ACTIVE` generation. Index activation requires golden query evidence; it does not make its indexed content authoritative. Track source-set digest, embedding-model identity/revision, vector dimension, index artifact checksum, corpus size and evaluation receipt.

## 4. Learning candidate lifecycle

`OBSERVED → HYPOTHESIS → EXPERIMENT → EVALUATED → REVIEW_PENDING → APPROVED/REJECTED`. Evidence of improved extraction/retrieval (true positives, false positives, citations, latency) must be from disjoint test data; model judges alone do not validate themselves. A hypothesis may be promoted only through a separate actual reviewer or approved mechanism.

## 5. Skill lifecycle

`PROPOSED_DESCRIPTOR → STATIC_VALIDATED → SANDBOX_TESTED → HUMAN_APPROVED → RELEASED`. Until a genuine isolated executor exists, stop at `PROPOSED_DESCRIPTOR`. Model-supplied shell commands and Python text are inert artifacts, never executed inside NSAI API or through a Docker socket.

## 6. Why these five are separate

An embedding index can improve retrieval of false content. A model can phrase unsupported claims fluently. Successful sandbox execution can still produce unauthorized output. A valid approval can apply to one artifact digest and **not** authorize a different revision. Treat each transition as scoped and separately recorded.

## Test matrix

| Scenario | Expected behavior |
|---|---|
| Source identical re-upload | No duplicate source revision/claims |
| Revised contradictory document | Both alternatives and locators retained; contested candidate status |
| Missing PDF page locator | Claim not accepted as source-grounded |
| Candidate index golden recall failure | Staging failed; active index unchanged |
| Model instructs itself to verify claim | No approval event; prompt treated as data |
| Reviewer token replay or changed artifact hash | Denied, no truth mutation |
| Skill descriptor `execution_enabled=true` | Contract validation error |
| GPU provider timeout | Explicit error, no fake AMD usage |
| DB restart during ingest | Transactionality preserves consistent state |
| Historical query | Earlier observed/valid states still retrievable |
