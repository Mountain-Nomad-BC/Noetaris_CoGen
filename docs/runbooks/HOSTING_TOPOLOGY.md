# Practical hosting topology — local -> staging -> event public prototype

## Stage A: Local WSL2 / Docker Desktop (recommended immediately)

- Run API and Postgres locally in included Compose; no external user access; verify login token, seeded evidence and persistence.
- Use synthetic documents only. Develop modules locally with actual fixture comparisons.
- No cloud GPU cost. When AMD cloud available, stage only the model endpoint first.

## Stage B: GPU integration on AMD host

- Keep API, PostgreSQL and vLLM on the same AMD Linux host temporarily for the fastest integration testing (`app_net` private; `data_net` internal). This reduces cross-cloud model ingress complexity.
- Deploy only behind controlled access. Host cost is tied to GPU instance uptime; shut the entire VM down when no longer needed, based on event evaluation needs.
- Do not expose vLLM publicly. If Evolus must reach it, add a locked-down TLS/auth ingress designed specifically for machine-to-machine requests.

## Stage C: Cheap always-on frontend + service backend (after auth/security gate)

Possible topology (illustrative; verify provider current terms):

```text
[Browser] --> [Vercel Next.js/static console + OIDC session]
                          |
                       HTTPS
                          v
                [FastAPI on secure CPU service]
                          | private TLS
                  [Managed PostgreSQL]
                          | private inference
                  [AMD ROCm vLLM host]
```

The current frontend is plain HTML/JS served by FastAPI. Splitting to Vercel requires a new frontend auth strategy, CORS configuration, API base URL and separate build/deploy process. Do **not** assume the existing `assets` folder is deployable as a secure public Vercel app without work. Keeping API+UI together behind a TLS identity-aware proxy can be faster for the event.

For managed PostgreSQL, enforce TLS with certificate validation, least-privilege DB roles, backups and project isolation. Supabase provides PostgreSQL but its auth, RLS, storage and connection pooler are **not presently configured in this starter**.

## Secrets and configuration ownership

| Secret | Who needs it | Where it must live |
|---|---|---|
| API local demo token | Browser dev/test only | local `secrets/api_token.txt`, never public deployment |
| Postgres password | API/DB only | Docker secret or managed secret store |
| AMD model API key (if any) | Model proxy + API | server-side secret file or manager |
| Evolus API key | Workflow backend only | server-side secret file or manager |
| Supabase service-role key | Backend only if used | managed backend secrets, NEVER browser |
| OIDC signing/public keys | Identity gateway/backend verifier | JWKS key configuration |

## Order to avoid deployment dead ends

1. Local acceptance first.
2. AMD model proof second (event rule).
3. Full synthetic demo + metric recording third.
4. Authorization/TLS/frontend hosting fourth (mandatory if truly public).
5. Optional Evolus only when AMD model endpoint secure and stable.
6. Google/other tracks only when main demo is safe and complete.

## Hosting go/no-go

A demo URL without authentication to the local-token API fails the public gate. A GPU YAML that never started on ROCm fails the AMD proof gate. A workflow template without live event workspace calls fails Evolus proof. Keep all three separate.
