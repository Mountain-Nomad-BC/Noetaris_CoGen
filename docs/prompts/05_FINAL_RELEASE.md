# Copy/paste handoff — release and submission gates

Implement OPS-01..06 and any still-blocking security tasks. Read `docs/runbooks/PUBLIC_DEPLOYMENT.md`, `docs/event/DEMO_AND_SUBMISSION.md`, `docs/validation/RELEASE_GATES.md` and event dashboard.

1. Run all unit/integration/negative security tests; save exact result receipts, not guessed counts.
2. Prove end-to-end conflict scenario on original synthetic vendor docs; capture source and revision links.
3. Verify real AMD usage and billable time; measure precision/recall/citation support and inferencing metrics with raw fixtures.
4. Run robust secret/license/SBOM scanning, check Git history; this package's offline regex checker is not comprehensive.
5. Do NOT publish local shared-token API. If OIDC/TLS/authorization/rate limits are incomplete, choose a private controlled demo/screen recording and clearly describe scope; do not claim hosted security.
6. Only include proprietary Remy source if separate written authorization explicitly obtained; otherwise remain clean-room. Apache-licensed PX files require notices and release compatibility review if adopted.
7. Produce submission fields, public GitHub README, video, slides, hosted URL only if safely available, and verify actual portal deadline time rather than assuming.
8. Leave traceable NEXT tasks and rollout/rollback instructions, shut down unused GPU spend when demo rules allow.

Output: actual release artifact, verification ledger, truthful status table, demo script and submission proof. Block unsafe release rather than hiding failures.
