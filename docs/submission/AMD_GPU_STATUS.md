# AMD deployment and GPU validation status

Status: **PENDING**. No approved native Linux ROCm GPU host is available in this session.
Docker Desktop CPU integration does not prove ROCm compatibility or GPU performance.

The application retains an OpenAI-compatible replaceable inference adapter. The AMD Compose overlay
selects `amd-vllm`, private inference networking, explicit `/dev/kfd` and render-node devices, bounded
resources, private IPC, health checks and cache storage. The starter image tag is a candidate only;
immutable image selection is required by `scripts/amd_preflight.py` before any AMD deployment.

On an approved AMD host, verify its supported driver/kernel, model license, VRAM, device groups,
container image and runtime UID/cache ownership. Set `NSAI_VLLM_IMAGE` to a reviewed digest,
`NSAI_VLLM_MODEL` to the exact model and `NSAI_MODEL_LICENSE_REVIEWED=true`. Run preflight;
inspect raw results in `evidence/raw/amd-preflight.json`. Do not loosen seccomp, add privileged mode,
share host IPC/network, or grant broad capabilities to mask incompatibility.

Then follow the local DB migration process, start the AMD overlay without the Ollama overlay, and prove:
GPU visibility in the actual inference container; `/v1/models` readiness; `/v1/reason` real inference;
provider/model provenance; resolving citations; kernel/runtime/image/model digests; GPU utilization;
measured per-case latency and p50/p95 across a disclosed dataset; dropped-GPU and timeout behavior.
Stop GPU resources after validation; provider credit/cost controls are separate from local call limits.

Required receipt fields: UTC timestamp, hardware model/VRAM, host kernel/driver/ROCm versions,
image digest, model revision/license, exact commands and exit codes, raw probe/inference output,
dataset IDs, timing samples and failures. Preserve pending status until this evidence exists.
