# Firebase Google and GitHub sign-in for the Oracle rollout

The owner selected Firebase Authentication for the public Spark frontend. This supersedes the historical direct-backend OAuth callback instructions for this rollout. The existing direct OAuth implementation remains in source; it is not evidence that Firebase ID tokens are already verified by the Python API.

Verified Firebase web app:

- Project and Hosting site: `noetaris-cogen`.
- App ID: `1:59248056505:web:5a3f08b2ae48bb22272368`.
- Application homepage: https://noetaris-cogen.web.app.
- Authentication domain from downloaded SDK configuration: `noetaris-cogen.firebaseapp.com`.

## GitHub OAuth application values

Homepage URL:

```text
https://noetaris-cogen.web.app
```

Authorization callback URL:

```text
https://noetaris-cogen.firebaseapp.com/__/auth/handler
```

Enter the GitHub client ID and secret in Firebase Console > Authentication > Sign-in method > GitHub. Do not put the secret into the browser bundle, public repository, or chat. Enable Google in the same Firebase provider settings. Confirm the deployed Hosting domain is authorized.

The Oracle IP, future API HTTPS address and historical `/auth/github/callback` endpoint are not the Firebase GitHub callback. No custom domain has been verified.

## Remaining implementation and verification

Firebase web-app registration and SDK configuration retrieval succeeded. Provider enablement and real user sign-in are not yet verified. The Python Firebase-token adapter and canonical per-user content/indexing qualification remain pending; public provider buttons must not pretend they work before commissioning. Firebase client configuration alone does not authorize document access.

Retain canonical UUID-derived accounts, no email-based automatic account merging, ownership checks, bounded usage and logout behavior. Test real Google and GitHub sign-in, wrong-project/expired/forged-token rejection, two-user isolation, public upload acknowledgment, indexing, retrieval, actual inference, citations and sign-out against the final public API origin before claiming success.
