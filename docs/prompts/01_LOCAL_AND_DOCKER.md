# Copy/paste handoff — phase 0: local infrastructure and Docker

Implement/verify tasks BASE-01 through BASE-09 and SEC-01 in dependency order. Do not prematurely add a public deployment. Start by reading `docs/runbooks/LOCAL_FIRST_BOOT.md` and `docs/runbooks/DOCKER_AND_SANDBOX.md`.

1. Validate Python 3.12, Compose plugin, secrets creation, `docker compose config` and `docker compose up --build`.
2. Confirm /healthz, /readyz, bearer token rejection, seeded candidate claims, conflict group and DB persistence after restart.
3. Test `sandbox-smoke` in Docker network none; inspect actual permissions, caps, mounts, no-new-privs, limits and public port mapping. Report host/WSL Linux differences.
4. Fix actual startup issues only with minimal privileges, not `privileged: true`, host networking, Docker socket mount or disabling seccomp.
5. Add CI and dependency/image pinning work as reasonable; note if actual pinned digests cannot be established without registry access.
6. Create a gate receipt showing actual Docker output and unresolved production security requirements.

Definition of done: G0 verified locally, current tests pass, no false AMD/sandbox claims. Do not deploy public local-token app.
