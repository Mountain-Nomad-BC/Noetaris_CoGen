# Docker safety implementation — enforce and verify, not merely declare

This file differentiates security baselines for the normal API, ingestion, GPU service and future executable-code sandbox. **Containers are not secure enough to run arbitrary adversarial LLM-generated code without additional OS isolation and authority separation.**

## Local topology

- `api`: user 10001, read-only root, non-privileged, dropped all Linux capabilities, no-new-privileges, resource limits, tempfs, healthcheck. Bound to `127.0.0.1` only; `app_net` has outside reachability, so it is **not** an egress-denied service.
- `db`: private `data_net` only; no published port. Persists in Docker volume. Database container is not yet strictly non-root/read-only and must use least-privilege DB roles for production.
- `sandbox-smoke`: network namespace `none`, non-root, read-only, dropped caps and bounded resources; smoke only, no untrusted arbitrary code.
- `vllm`: separate AMD GPU device binding to `/dev/kfd` and render node, private app network. Its root/cache access, GPU driver, runtime and seccomp must be checked on actual ROCm host; GPU access is a privileged hardware capability and this service **must not execute untrusted code**.

## Threat-to-control matrix

| Threat | Primary prevention | Mandatory verification |
|---|---|---|
| Prompt injection changes trusted truth | Candidate status + human authorization external to model | Untrusted document injection tests, no promotion endpoint without verified reviewer |
| Model attempts Docker control | No Docker socket, no host network, no privileged containers | Static + `docker inspect`, grep mounts and environment |
| Worker fetches attacker URL | No network by default in untrusted executor; explicit allowlists on intentional fetch worker | Denied external DNS/HTTP test on executor |
| Host filesystem read | Non-root, read-only root, no arbitrary host mounts, LSM/seccomp | Attempt to read synthetic host sentinel in isolated executor; must fail |
| Container DoS | `pids_limit`, CPU/memory limits, input size/time budgets | Resource exhaustion and cancellation tests without killing host |
| Secret exfiltration | Secrets only in required processes, never in browser or runner; no model token in prompts | Inspect process env/mounts/logs; negative search |
| Lateral DB access | Private data network, separate API/DB roles; sandbox never shares DB net | Network inspection; worker denied DB route |
| Bad model image/dependency | Pin digest, SBOM, vulnerability scan | Provenance report and scan before public release |
| Old or altered knowledge | Immutable hashes and versions, authorization gate | Hash tamper and bitemporal tests |
| Failed GPU inference | Strict timeouts and clear "model unavailable" rather than fake answer | Force 5xx, timeout, disconnected host and verify state |
| Unbounded billing | Stop GPU after test, budget alerts at cloud provider | Actual GPU instance uptime and credit records |

## Docker verification commands

```bash
python scripts/validate_compose_security.py
docker compose config --quiet
docker compose ps --format json
# Check each effective service configuration; Docker output not copied blindly into public logs
docker inspect "$(docker compose ps -q api)" --format '{{json .HostConfig.SecurityOpt}} {{json .HostConfig.CapDrop}} {{json .HostConfig.ReadonlyRootfs}} {{json .HostConfig.NetworkMode}}'
docker inspect "$(docker compose ps -q db)" --format '{{json .NetworkSettings.Networks}} {{json .HostConfig.PortBindings}}'
docker compose --profile sandbox run --rm sandbox-smoke
```

Inspect in addition: Linux kernel LSM profile, seccomp, `no_new_privs`, actual UID, cgroup limits, interface addresses, mounts, published ports, volume ownership, reboot behavior, and rootless engine status. Docker Desktop/WSL2 and remote Linux do not have identical security semantics.

## How to build the later executable sandbox (NOT provided as working code)

1. Use a dedicated runner process/service that alone can launch immutable jobs; never give the NSAI agent or API the host Docker socket.
2. Prefer a stronger isolation backend (microVM/gVisor/Kata or hardened rootless containers with host-enforced seccomp/AppArmor/SELinux) based on cloud-host feasibility; document its threat model.
3. Default deny network, mount read-only input artifacts by content hash, mount a writable scratch directory only, cap disk/CPU/memory/pids and execution wall time.
4. Attach immutable artifact digests, work admission ID, approved capabilities and independent issuer signature to each job; verify prior to launch.
5. Collect tool results in bounded output files, scan artifacts and copy out by trusted host process, never allow container -> Docker API.
6. Test escapes and failure behavior on isolated host; if sandbox cannot prove containment, **disable generated-code execution entirely** and use declarative plans only.

## Never use these shortcuts

- `privileged: true` or blanket `seccomp=unconfined` to fix an incompatibility.
- Mounting `/var/run/docker.sock` even as `:ro` into API, worker or agent.
- `network_mode: host` for the public API or GPU without deliberate separate hardening review.
- Running arbitrary new code in the API's `sandbox-smoke` container.
- Reusing PX Windows Gremlin Job Object backend as Linux enforcement.
- Checking only a compose YAML and claiming isolation was runtime validated.

## Host firewall and public topology

Only the HTTPS frontend/API ingress should be reachable externally. Keep DB and vLLM private by default. Evolus may require reaching a self-hosted AMD model endpoint from its cloud; implement a dedicated HTTPS, authenticated ingress with strict rate/IP restrictions and monitor access. The current `NSAI_MODEL_URL` HTTP exception for internal Docker `vllm` is **not** safe for an internet-exposed model service.
