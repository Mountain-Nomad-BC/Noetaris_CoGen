# Project documentation

Version: 2026-10-17

Using Noetaris and understanding its current operating boundaries.

## Start here

Noetaris is a source-based research workspace. The current Docker integration supports synthetic document upload, indexing, retrieval, source inspection and guarded answers. Public deployment and private-user content admission are not complete. Check the workspace capabilities and access messages for your identity; a sign-in does not grant document access.

## Upload and index

With an authorized identity, open Library and select a supported document. Wait for indexing to finish: the page polls actual job state. A failed or queued job is not query-ready. The original file is preserved separately from extracted text, chunks and semantic index records. Never upload credentials, sensitive personal data or material you lack rights to use.

## Search and ask

Use Library search for indexed passages, then open the source or choose Ask Source. MiniLM helps embed and retrieve passages. Check the answer citations against the original. Conflicting or insufficient evidence can withhold generation or return evidence excerpts. Ingestion creates searchable records; it does not retrain model weights or certify a document as true.

## Review and organize

The knowledge explorer exposes actual graph records and node-type filters. Claims require separate-role review where the workflow calls for it. Topic search presets are search tools, not proof of permanent automatic folder assignment. Generated text and reviewed source claims have different authority.

## PDF and tabular work

Open an indexed PDF to inspect its pages, extracted text and citations. Download Original returns retained bytes, checked against their digest. Supported CSV calculations use the structured calculation operation; an AI prose answer is not a substitute for an exact calculation. Scanned, encrypted, damaged or unsupported files may be rejected or require a separate qualified extraction path.

## Sign in and sign out

Google and GitHub controls appear unavailable until configured by the operator. Choose Sign in or Create account explicitly. Linking is an authenticated, explicit operation; accounts are not silently merged by email. Local credentials are a separate authorized fallback and stay in memory in that tab. If logout is unconfirmed, retry server sign-out.

## Models and external processing

AMD hosted Gemma-4-31B-IT is the selected remote primary. The exact free OpenRouter Gemma 31B and 26B variants are intended fallbacks; both last returned rate limits. Automatic source-bearing hosted dispatch is still incomplete. The running local integration uses CPU Gemma, with MiniLM for retrieval. An API connectivity test is not end-to-end document routing.

## Storage and privacy

Cloudflare docs and images buckets are private Standard storage and pass synthetic object checks. Application originals currently remain in PostgreSQL; R2 offload and durable quotas are unfinished. No paid fallback or automatic limit increase is authorized. Read Privacy and AI transparency before supplying data.

## Feature availability

Templates, agent catalog, evaluations/evidence qualification, workflow studio, developer execution and voice remain wholly or partly gated. Do not interpret a menu entry as a live service. Evolus is optional and NOT_CONFIGURED until real application/workflow/agent/extractor bindings are verified.

## Operator and developer reference

The source repository contains HANDOFF.md, docs/implementation/FINAL_DELIVERY_PUNCHLIST.md, deployment topology, owner actions, release acceptance and rollback instructions. Exact run receipts are owner-held evidence, not public user data. Runtime authorization belongs to the server; no browser database access or embedded provider credentials are permitted.
