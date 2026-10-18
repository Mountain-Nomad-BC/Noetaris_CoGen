# Google and GitHub sign-in contract alignment

The owner-supplied NSAI_GOOGLE_GITHUB_SIGNIN_MODEL_IMPLEMENTATION.md is binding. Its SHA-256 is `d8c9982dabb0b5c14d75855e2751801fce65b56e2c186a97be8adacdf23588ef`. Status: IMPLEMENTED IN PART / TESTED IN SCOPE / EXTERNALLY BLOCKED / NOT RELEASE-CERTIFIED.

## Current implementation and repairs

The deployed React auth screen is `frontend/noetaris/src/noetaris/pages/public/LiveSignIn.jsx`, coordinated by `state/AuthContext.jsx`. The server implementation remains `src/nsai/oauth_{providers,state,accounts,http}.py`, existing identity/security modules and migrations 0033?0036. No alternative auth framework or identity database was introduced.

The audit found unnecessary email eligibility checks. Google now requests only `openid`; signed, validated `sub` remains the identity. GitHub requests `read:user`, reads stable numeric `/user.id` without JavaScript precision loss, and never calls the private email endpoint. Missing or unverified optional email is no longer an authentication failure. Authlib signature, issuer, audience, nonce, expiry, PKCE and one-use state validation remain intact. No provider token persistence was added. Existing bindings are unchanged.

The live auth UI retains separate login/signup intent and explicit authenticated linking. Redirect progress now remains pending after navigation starts, preventing repeat clicks. The authenticated selector displays its actual link operation. Buttons have responsive widths, minimum touch height and visible keyboard focus. Disabled providers remain truthful. Local fallback is preserved.

Focused verification: 48 tests passed across provider transport, signed-token negatives, one-use state and canonical account identity. These use synthetic provider boundaries and do not establish real Google/GitHub E2E. Docker API and frontend builds passed after the repair; runtime identities are in ignored `state/integration/identity.json`. Actual Chromium checks additionally pass 320/375/768/1440px responsive layout, truthful disabled controls, 44px minimum touch targets and explicit signup selection. This is not screen-reader, high-contrast or real provider acceptance. The preceding sign-in candidate frozen-source full regression passed 1,657 tests with zero failures/errors/skips, exact coverage, unchanged source and complete cleanup: `evidence/integration-deployment/qualification-5739bd0d261945ecaf4eec248686f9ba/receipt.json`. This does not establish real provider acceptance.

## Remaining acceptance inventory

| Agent can implement or qualify locally | Owner/external prerequisites |
| --- | --- |
| Audit literal UUID representation versus legacy `local-user-*` actor compatibility before any migration; current UUID-derived actor strings do not establish the literal UUID-only contract | Registered Google and GitHub authentication applications, consent/branding approval and exact production HTTPS callbacks |
| Connected-provider listing/settings and approved branding assets; existing explicit link action alone is incomplete settings acceptance | Owned same-site app/API domains and TLS, provider client secrets installed in restricted runtime files |
| Responsive 320/375/tablet/desktop, keyboard/screen-reader/high-contrast/reduced-motion acceptance on current images | Independently controlled non-production provider accounts for real signup/login/link/logout journeys |
| Current-image auth TLS synthetic matrix, race/outage/revocation and backup/restore checks; fresh source/image/schema-bound receipts | Independent security/privacy/ACL acceptance and release admission |
| Safe original-destination restoration and full callback/error/back-forward review; no external redirect relaxation | Approved unlink and optional display-data retention policy |

Private-content DENY gates remain binding after successful sign-in. Provider flags remain disabled pending configuration and activation. No live provider journey, production cookie acceptance or independent certification is claimed. Rollback retains compatible schema, durable links/session revocation and backups; never drop identity tables to roll back an image. See existing OAuth account/browser-session documentation for the established custody and revocation design.
