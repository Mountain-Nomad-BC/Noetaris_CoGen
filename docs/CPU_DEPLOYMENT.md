# CPU-first deployment used for this build

**Historical deployment record — not current operating instructions.** As of 2026-10-17 11:48 EDT, the existing Docker services have no host-published ports, host `/healthz` is unreachable, the release gate is **DENY**, and the runtime Compose overlay is unresolved. Do not run start/stop/restart/build/migration commands against the existing stack. See [current deployment state](implementation/DEPLOYMENT_STATE.md) and [Start here](../START_HERE.md). The configuration and model evidence below do not attest to the current running image or deployment.

The demonstrated local backend uses the upstream llama.cpp CPU server image with a single validated,
existing Qwen 2.5 Coder 3B GGUF mounted read-only. GPU layers are explicitly zero, and the model
service runs as UID 10001 with no capabilities, a read-only root, private internal networking, no published
ports, no secrets, and CPU/memory/PID limits. The existing model SHA256 is recorded in
`evidence/raw/cpu-model-provenance.json`; weights are not copied or bundled.

Run `powershell -ExecutionPolicy Bypass -File scripts/start-cpu.ps1`. The local `.env` selects the
validated GGUF file and digest. For another machine, set `NSAI_GGUF_PATH` and `NSAI_GGUF_SHA256`
to an appropriately licensed, verified local GGUF. Never assume registry availability implies a runtime.
The Qwen 3B artifact's supplied model metadata declares a Qwen Research License; this is not a claim
that the weights are MIT/Apache or approved for public redistribution.

The original Ollama overlay remains an alternative. Its large image download was stopped when an
existing local model enabled a smaller CPU-only server deployment. Ollama runtime validation for this
upgraded build remains pending; its manifest and adapter tests do not establish that runtime. Docker
Model Runner was inspected and reported a missing CUDA capability probe; it was not repaired or used.

Stop this CPU project with `scripts/stop.ps1`, preserving volumes. Use `compose.yaml` plus
`deploy/local/compose.cpu.yaml` for inspection/restart, and do not combine CPU, Ollama and AMD
inference overlays. Only one inference backend should configure API at a time.

Upstream implementation references: [llama.cpp Docker images](https://github.com/ggml-org/llama.cpp/blob/master/docs/docker.md),
[server contracts](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).
PDF budget/extraction limitations follow the [pypdf extraction documentation](https://pypdf.readthedocs.io/en/stable/user/extract-text.html).
Local secrets are service-scoped using [Docker Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/).
