# Durable conversation history foundation

Read-only Python endpoints expose existing canonical sessions and retained messages. The NOETARIS live chat now uses these endpoints and the existing retrieval/generation APIs. No identity store, schema migration, source rewrite or alternate conversation authority was introduced.

| Endpoint | Contract |
| --- | --- |
| GET /v1/chat/sessions?limit=25&cursor=... | Current actor's session IDs/timestamps only; owner-bound keyset cursor; no conversation snippets. Limit 1?50. |
| GET /v1/chat/sessions/{id}/messages?limit=25&before_id=... | Owner-only, currently readable/provenance-complete message IDs, roles and timestamps; descending IDs with next_before_id. No text released by this listing. |
| GET /v1/chat/sessions/{id}/messages/{message_id} | Owner-only full retained receipt and stored text_preview, after current complete source checks and assistant receipt/envelope consistency validation. |

Message IDs are strings on the wire, preserving values above JavaScript's exact-integer range. Actor/role authority is never accepted from cursor or request data. Shared legacy project roles are explicitly restricted to their own conversations even though legacy RLS permits broader project reads. Unknown/cross-owner conversations return unavailable rather than a directory probe.

For assistant messages, full_text_field is receipt.answer. This retains responses longer than the historical 12,000-character text column prefix. The response does not duplicate the full answer into another field; raw receipt is bounded to 16 MiB before retrieval. Larger records remain retained and fail with an explicit qualified-bound error rather than truncating stored content. Public question limits already bound user text. No existing history was rewritten or deleted.

Source RLS, explicit current visibility checks, original source envelopes and existing final private-response reauthorization apply. Messages without complete provenance or currently authorized inputs remain stored but are withheld from the read interface; pagination's content_policy states this explicitly. Revocation cannot become a usable cached answer. Regrant recovers the original unchanged record. Individual-user HTTP admission remains closed; the new endpoints do not bypass it.

Evidence:

- 9 focused tests, including real PostgreSQL and actual HTTP handlers: evidence/implementation/conversation-history-focused.xml. Covers full retained response beyond 12,000 characters, exact message IDs above 2^53, pagination/cross-owner cursors, legacy-role isolation, source revoke/regrant without deletion, anonymous denial and unchanged individual admission.
- Full fresh exact packaged API qualification: **1,339 passed, zero failures/errors/skips**, evidence/private-access/91ba28ee4f174155984516f2f9eacc79/receipt.json.
- Actual clone dump/restore: evidence/operational-cost-recovery/14559484671341a7ba1f02c7140c3687/receipt.json. Retained full response hash/length, original message ID and owner denial survived alongside 50-table fingerprints, ACL/sequence state/settings, CSV/JSON/XLSX originals, sessions/revocation, queues and ledgers.
- Current paired-image regression: 30 PDF, 49 library, 23 Docker/session and 21 HTTPS OAuth/resilience checks. Exact receipt hashes are in evidence/noetaris-integration/current-evidence.json. These do not imply that the unfinished chat UI or real external providers are qualified.

**Historical qualification image pair only:** API `sha256:1d190a228b73a52dc4813d0e6449a7b6cbf59a79e9ba0757a77bdbd56b16b94d` with frontend `sha256:3264f18999cf0b0ad7a55550ff203930b8ac69f7360cb0fbf9d0c0b2b2924151`. These digests scope the receipts below and are not current live image identities. Fresh live provenance is unresolved; see [current-tree reconciliation](../../reports/current-tree-diff.md). Original live/research backup hashes and all 44 supplied frontend download files were rechecked unchanged in that historical qualification run.

Changed files: src/nsai/conversation_history.py and api.py; new conversation_history_pg_fixture.py/test_conversation_history.py; isolated test helper allowlist; structured recovery oracle; refreshed static runtime inventory. Exact file hashes are recorded in evidence/noetaris-integration/history-changed-files.json. Static inventory now records 65 service routes/71 sealed SQL functions; counts do not grant acceptance.

Rollback selects the retained previous API image; no data downgrade or deletion is needed because the added endpoints are reads over existing storage. Older API images lack the new history endpoints, so any future history-enabled frontend must be rolled back or paired with a compatible API. Existing messages/original receipts remain preserved.

Next: wire real NOETARIS chat threads to canonical server sessions and history, explicit library/source/revision/page scope, bounded cancellation and idempotent request IDs; connect actual returned citations into the verified PDF workspace. Qualify against actual local encoder publication and approved inference, not manually published/fake vectors or invented completions. Wider semantic/voice/provider/capacity/deployment and independent certification gates remain open.


## Live chat Docker integration

The live route now binds to the canonical session returned by the backend, restores paginated authorized history, preserves string message IDs and reads full retained receipt answers. Message previews explicitly disclose their bounds; full records remain accessible. Unsent drafts and their explicit scopes are kept in tab memory across source navigation and conversation switches, with a reachable resume control. They are cleared on identity changes and are not durable across browser reloads.

Questions preserve their original whitespace and validate the backend character/source/revision/page limits. Whole-library retrieval has no UI document-count truncation. Explicit scope is captured per request and checked against the returned receipt. A citation opens the actual PDF anchor or library source without changing question scope. Generated explanations remain labelled unverified.

Cancellation aborts the browser request and invalidates its response epoch. It cannot promise server cancellation. Unresolved request IDs remain inspectable through the actual durable invocation receipt, without retrying a generation or inserting an old response into a different conversation. Missing inference is explicit and leaves source retrieval available. Individual-user content admission remains closed.

The exact frontend build runs 18 transport and nine chat-state contracts. Actual owned-stack browser evidence covers real local encoder publication, source switching, original user text retention, durable canonical sessions, actual returned citation highlighting, insufficient evidence, zero inference admission for retrieval, delayed-response isolation, receipt recovery, history restoration and five viewport widths. These synthetic checks do not qualify every historical message size, arbitrary corpus, OCR, provider, full-duplex voice or independent release acceptance.

Changes: frontend App/provider wiring, live route gate and shell, ChatPage dispatch, LiveChatPage, LiveLibrary source navigation, LiveChatContext, chatContracts, liveChatStore, nine Node contracts and build script. The exact imported-file hash map is evidence/noetaris-integration/changed-imported-files.json. No backend change in this frontend increment.

Rollback: restore the retained preceding frontend image from the prior current-evidence receipt (sha256:3264f18999cf0b0ad7a55550ff203930b8ac69f7360cb0fbf9d0c0b2b2924151); retain the current API image and database. The frontend has no authoritative persistent data to migrate or erase. Qualification stacks clean up only their labelled resources; existing live containers remain untouched.


Fresh proof: evidence/noetaris-integration/current-evidence.json binds the current image to 152 browser checks (29 chat,30 PDF,49 library,23 session,21 HTTPS OAuth), plus27 frontend contracts. The chat runner additionally starts a hash-verified owned CPU model after proving unavailable inference behavior: one actual source-bound unverified explanation takes24.368seconds and consumes exactly one admission. No cash or external provider calls. The same runner proves ordinary retrieval consumes zero generation admissions. This single synthetic case is not a throughput, broad grounding or provider certification.
