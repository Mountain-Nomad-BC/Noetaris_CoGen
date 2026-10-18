# NSAI Docker, AMD, and execution security

This starter is a **hardened local demo baseline**, not a certified internet-facing deployment or a general-purpose secure sandbox for hostile executable code. The Compose manifests are intended to make the next runtime validation cheap and repeatable.

## Exact reviewed source findings

| Source | Finding | NSAI disposition |
|---|---|---|
| Remy `7_Remy/Dockerfile` | explicit `USER nonroot` | preserve non-root API image principle |
| Remy `7_Remy/docker-compose.yml` | `cap_drop: ALL`, no-new-privileges, resource limits, logging limits, `/readyz` | preserve patterns; rebuild service definitions |
| Remy `7_Remy/docker-compose.yml` | `${REMY_API_PORT:-8007}:8007` without loopback IP | fix with `127.0.0.1:${NSAI_HOST_PORT:-8787}:8787` |
| Remy `7_Remy/docker-compose.yml` | default example service token, large writable knowledge mounts, shared external network | remove token fallbacks; explicit secrets; limit mounts/network |
| Remy `7_Remy/docker-compose.gpu.yml` | `REMOTE_OLLAMA_VERIFY_TLS` has `false` fallback | never adopt; remote inference must use HTTPS, or be private internal HTTP |
| Remy `gpu-worker/docker-compose.yml` | `driver: nvidia` GPU reservation | reject for AMD; use ROCm vLLM host with `/dev/kfd` plus exact render node |
| Remy `docker-compose.monitoring.yml` | Docker socket mounted in a monitoring service (`:ro`) | do not include; Docker socket is control-plane access even if mounted read-only |
| Remy `docs/deployment/docker-hardening-pc16.md` | documents prior static Compose hardening, not end-to-end running certification | preserve methodology, require runtime revalidation |
| PX `runtime/isolated_sandbox.py` | policy definition and checks | optional policy inspiration; not Linux isolation |
| PX `runtime/gremlin/host_enforcement_backend.py` | Windows process/job enforcement | exclude from Linux deployment |
| PX `runtime/docker_model_runtime.py` | model runtime identity plans and authority checks | defer until NSAI model manager needed |

## Five independent boundaries

1. **Container runtime**: non-root API uid 10001, `cap_drop: ALL`, `no-new-privileges:true`, `read_only:true`, tmpfs ephemeral paths, pids/CPU/RAM quotas, limited logs, no host PID/network, no Docker daemon socket.
2. **Data**: PostgreSQL has no published port and is attached only to internal `data_net`. Database initialization scripts run only on a fresh named volume. Database volume is stateful and cannot have a global read-only filesystem.
3. **Credentials**: local random API and database secrets are generated into ignored `secrets/` files and mounted by Compose. The static browser interface asks for API bearer token in memory, never stores it in localStorage. This is a demo mechanism, not production SSO.
4. **Inference**: AMD model process is a separate service, not part of API; only GPU process gets device passthrough. Local HTTP is allowed only to a known internal `vllm` hostname (or loopback). For a separate remote AMD host, configure **HTTPS** or a restricted private tunnel.
5. **Autonomous code**: no general untrusted code executor exists in the starter. The `sandbox-smoke` Compose profile confirms some isolation properties; it does *not* prove resistance to container escapes, malicious kernels or arbitrary untrusted Python. Before enabling code generation/execution use a purpose-built sandbox host/VM, non-root namespaces, OS MAC/seccomp policy, no secret mounts, strict quotas, immutable image, exit/timeout controls, and verified containment receipts.

## AMD host differences

The `deploy/amd/compose.amd.yaml` override is deliberately segregated from normal local startup. It uses official upstream ROCm vLLM image `vllm/vllm-openai-rocm:v0.31.0` (check that tag/host compatibility before pulling), `/dev/kfd` and one configured `/dev/dri/renderD*` node. On the AMD host verify GPU drivers, render node, ROCm/vLLM tag, GPU memory, model download conditions and permission groups. The upstream examples may grant `SYS_PTRACE` or disable seccomp for some GPU configurations. **Do not apply those elevated permissions by default**; if GPU initialization fails, diagnose specifically and document the narrow exception, ideally isolating it to the dedicated inference VM.

The ROCm image may run as root and require writable caches depending on its published defaults. The MVP GPU override should be treated as *provisional* until non-root execution, device groups and filesystem behavior are verified on the real AMD GPU instance. `cap_drop: ALL` is a defense-in-depth measure, not a guarantee of support with every ROCm build.

## Production security gap list

| Requirement | Current | Production requirement |
|---|---|---|
| TLS on public entrypoint | not provided, loopback-only | TLS reverse proxy + host firewall |
| Multiuser authentication | static shared bearer token | trusted OIDC / identity provider, short-lived scoped tokens |
| Rate limits | none | gateway + per-user/request quotas |
| Secret management | ignored local files/Compose secrets | cloud secret manager + rotation + audit |
| Image supply chain | pinned version tags, not digests | immutable SHA256 image digests, SBOM, vulnerability scan, verified signature where available |
| Egress filtering | general outbound access on app network | outbound allowlist/firewall, network policies at host/cloud boundary |
| Database encryption/backups | ordinary Docker volume | encrypted backups, tested restore, access policies, production migrations |
| DB append-only immutability | no write APIs; SQL owner can mutate | restricted application role + append-only triggers / grant policy |
| File uploads / PDF parsing | text-only JSON endpoint | MIME allowlist, max size, PDF subprocess isolation, decompression limits, antivirus as appropriate |
| Web CORS and CSRF | same-origin Bearer API, no cookies | production origin policy, CSRF controls if cookie-based auth |
| Persistent sessions | not provided | scoped user/session storage and retention policy |
| Safe skill execution | execution disabled | sandbox runtime, execution lease, syscall/network policy, audit receipt |
| AMD inference | connector + candidate Compose only | live AMD GPU execution test and measurement |
| Observability | logging driver limits | correlation IDs, redaction, metrics, alerts and log retention |

## Never do these

- Do not put `/var/run/docker.sock` in the API/agent/worker or monitoring service.
- Do not use `privileged: true` or `network_mode: host` to fix an application wiring bug.
- Do not use `seccomp=unconfined` across the stack just because ROCm sample commands include it.
- Do not expose PostgreSQL, vLLM or admin endpoints to `0.0.0.0` by default.
- Do not bake company code, secrets, large proprietary archives, or raw employer data into public images.
- Do not let LLM content promote its own claims, adjust its own permissions, or access arbitrary URLs through an inference proxy.
- Do not label a sandbox safe simply because the process successfully ran as an unprivileged user.
