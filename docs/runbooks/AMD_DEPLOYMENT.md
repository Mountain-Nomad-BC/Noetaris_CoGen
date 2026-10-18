# AMD ROCm / vLLM — deployment sequence and stop conditions

**Mandatory event rule:** real meaningful workload on AMD. The provided GPU configuration is only a candidate and was not GPU-tested in this environment. The model ID, ROCm image tag and memory sizing require actual host compatibility checks.

## Step 1 — Provision, inventory and budget

1. In approved AMD cloud, create the smallest compatible instance with sufficient actual VRAM for chosen model and vLLM runtime. Record GPU, VRAM, host OS/kernel, ROCm and driver versions.
2. Verify network ingress/egress and data center region; use firewall to deny public DB/model endpoints until configured.
3. Set provider budget alert; write down credits remaining and hourly instance rate from current provider UI. **Do not assume $100 credits cover any particular number of days.**
4. Prepare a new private test branch or release candidate to transfer; no company data or Remy code.

## Step 2 — Check Linux GPU device access

```bash
cd nsai
bash deploy/amd/amd-preflight.sh
ls -l /dev/kfd /dev/dri/renderD*
# If installed, print supported GPU info
rocminfo | head -80
```

If `/dev/kfd` is missing, do not run `--privileged` to guess a fix. Review the cloud provider's required ROCm/driver/VM image configuration. `renderD128` may not be the correct node; set `NSAI_GPU_RENDER_DEVICE` to the actual render node.

## Step 3 — Model choice, integrity and serving

1. Pick an open-license instruction model compatible with the ROCm/vLLM version, available VRAM and desired context window. `Qwen/Qwen3-0.6B` is a **placeholder** in the current config, not an externally validated event-best model.
2. Check official ROCm/vLLM compatibility and model license/card. Pin container by verified digest and model revision. Never substitute a random `latest` tag while submitting.
3. Download model on GPU host using approved method; avoid exposing model repository tokens.
4. `python3 scripts/bootstrap_secrets.py; cp -n .env.amd.example .env` (review each field) and ensure Compose file meets host configuration.
5. Start with exact project root as base because Compose interpolates relative paths:

```bash
docker compose -f compose.yaml -f deploy/amd/compose.amd.yaml --profile amd config --quiet
docker compose -f compose.yaml -f deploy/amd/compose.amd.yaml --profile amd up -d --build api db vllm
docker compose -f compose.yaml -f deploy/amd/compose.amd.yaml ps
docker compose -f compose.yaml -f deploy/amd/compose.amd.yaml logs --tail=100 vllm
```

Add `NSAI_MODEL_URL=http://vllm:8000/v1` and matching `NSAI_MODEL_NAME` to `.env`; restart the API after settings change. If image startup fails due to GPU permissions, inspect device group IDs and runtime policy, adjust minimum necessary device/group access, then re-run containment checks. Do not silently disable seccomp or change privileged state.

## Step 4 — Prove real AMD inference

- From an authorized service or temporary private network probe, call `/v1/models` and `/v1/chat/completions` with a trivial known prompt; verify responding model matches configured ID.
- Call NSAI `/v1/reason` via authenticated API and persist only non-sensitive timing and model metadata.
- Capture actual GPU visible device, `rocminfo`, utilization tool if provided, container image digest, model revision, input/output token counts if available, p50/p95 over actual measured calls.
- Test bad host URL, model 500, timeout, OOM. Clear error should not become fabricated response.
- Record `AMD_VERIFIED` only after this end-to-end path, not when a Compose YAML is present.

## Step 5 — Exposing for optional Evolus

The Evolus workspace is a separate cloud service and may not reach the private Docker hostname `vllm`. If connecting it to AMD model requires public ingress, use a dedicated authenticated TLS proxy/gateway with limited access, not an open vLLM port. Align the Evolus model endpoint, API authorization and networking with event workspace instructions. Store keys in mounted files or secret manager.

## Step 6 — Shut down when idle

```bash
docker compose -f compose.yaml -f deploy/amd/compose.amd.yaml stop vllm
# Stop/delete the actual AMD VM from cloud provider UI to stop compute billing.
```

Stopping only the container might not stop instance billing. Save logs and non-secret metrics before deprovisioning. Keep the AMD workload operational as required for the demo/submission evaluation period based on official event guidance and budget.

## Stop conditions

Missing GPU devices, incompatible ROCm image, inability to secure required model ingress, secrets in command history or unbounded host charges: resolve before going public. Label failed inference as unavailable, never simulate AMD usage without identifying replay.
