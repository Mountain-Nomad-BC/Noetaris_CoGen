# Google and GitHub SSO registration

## GitHub OAuth App

Homepage URL: **https://noetaris-cogen.web.app**

Use a GitHub OAuth App for the existing authentication-only integration. The actual NSAI callback path is `/auth/github/callback`. Its full registered URL must use the commissioned, public HTTPS API origin. That origin is **not yet available**. Do not use the homepage itself, a Firebase SDK `/__/auth/handler` callback, a `.test` rehearsal, a guessed domain or an unconfigured static SPA route as a claimed working NSAI callback. The backend callback can be finalized once the API host/routing decision is complete; an existing registration may need its callback edited then.

The direct server integration uses S256 PKCE, one-use state and transient provider token exchange followed by stable numeric GitHub user ID binding. Requested scope is `read:user`; no repository/workflow/admin or private-email access is required. Provider email is not an account-merge key. Do not persist GitHub login tokens as application credentials.

Install the client ID as operator configuration and the client secret as a restricted ignored server file referenced by `NSAI_OAUTH_GITHUB_CLIENT_SECRET_FILE`. Enable only after the actual origin and secret configuration are verified. Do not paste the secret into chat, GitHub source, frontend env or public CI.

## Google

Use a registered Google web OAuth/OIDC client for the same commissioned environment. The backend callback path is `/auth/google/callback`, using the real public HTTPS API origin. The current server requests only `openid` and verifies signed issuer/audience/expiry/nonce and stable subject with Authlib. Gcloud/Firebase CLI login is operator access, not application SSO registration. No Firebase Auth SDK identity-store replacement is implemented.

## Verification before claiming working SSO

Test real separate provider accounts through signup, repeat login to the same canonical identity, explicit linking, logout and revocation, errors/cancellation, CSRF/state/PKCE negatives and actual HTTPS cookies on desktop/mobile. Preserve per-user document isolation and existing quotas. No invitations, waitlists or manual approval flow are part of this public adult demo. Failed/unconfigured SSO must remain truthful and grant no access.
