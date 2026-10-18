# NOETARIS canonical authentication integration

The supplied React UI now verifies existing local credentials through the Python capabilities endpoint and browser sessions through /auth/config and /auth/session. Google/GitHub start operations use the existing backend authorization-code/PKCE/state/account-linking implementation. Explicit login/signup/link operations are separate. No new identity database or Supabase dependency is introduced.

The transport uses the same-origin Docker proxy. Backend credentials stay in memory; browser sessions remain Secure HttpOnly SameSite cookies. The client sends CSRF and expected-actor proofs, rejects arbitrary authentication-header overrides, external/traversal paths, unexpected redirects, malformed JSON and SPA fallbacks. Epoch changes abort outstanding requests and reject stale replies even if the underlying fetch ignores cancellation. Private source authorization remains on the server.

Identity transitions clear conversation/voice state and cancel speech. Live mode cannot invoke browser cloud speech recognition; the local-first voice backend is still unfinished. Logout clears visible identity immediately, broadcasts clearing without credentials, and rebinds anonymous CSRF before another provider login. A server revocation failure remains explicitly unconfirmed; visibility refresh cannot silently reauthenticate, and retry remains available.

The live gate remains closed for unfinished fixture screens. Successful login is not private-content admission. The capabilities response supplies the separate content_access state; individual document access remains gated. Next integration is the actual authorized library, upload/index state and source inspector, followed by qualified chat/PDF/Atlas/memory and governed operational screens. All 14 placeholder routes remain pending.

Current evidence:

- 11 transport contract tests execute as part of every frontend Docker build.
- 23 actual loopback Docker/Python/Chromium checks: evidence/noetaris-integration/9e60f6ba857948a0bf8b66acfe417e77/receipt.json. Covers local identity, invalid credential, registry revocation, storage, content gate, SPA routing, headers and five viewport widths.
- 21 actual HTTPS UI/API/PostgreSQL checks: evidence/oauth-browser-tls/c36c5733ad3044e49cbf85b02ac87c3f/receipt.json. Only external identity-provider responses are synthetic; NSAI endpoints are not intercepted. Covers both providers' signup/login/linking, cross-tab logout, secure cookies, mobile width, fixture PDF refusal, actual database outage, unconfirmed logout and successful retry after recovery. This does not qualify real Google/GitHub accounts, public TLS or provider activation.
- Release fingerprints now include frontend source/lock/build/proxy inputs while excluding generated dependencies/build outputs and environment secrets. Sixteen focused release-gate tests passed: evidence/implementation/noetaris-source-binding.xml.
- Explicit icon imports reduced the emitted initial JavaScript chunk from 1,149.54 kB to 385.95 kB (uncompressed Vite artifact measurement). The separately lazy 3D chunk remains 880.13 kB; actual latency/memory and hardware WebGL performance are not certified by bundle size.

Configuration: deploy/local/compose.noetaris.yaml is an optional overlay using the pinned frontend image and same-origin Python API routing. Layer deploy/local/compose.noetaris-tls.yaml for supplied loopback certificate/key. Provider overlays remain optional and disabled until configured. The current isolated TLS tests use ephemeral self-signed certificates trusted only by their own Chromium context. Existing live services were not replaced.

Rollback: retain the original UI/API image and original downloaded frontend manifest. Choose the retained image digest, remove only explicitly owned isolated qualification resources, and restore proxy profile configuration if necessary. This frontend integration changes no database schema and performs no source migration. Existing preserved originals and backup evidence stay intact. Seven build dependency advisories and remaining feature integration prevent release certification.
