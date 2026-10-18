# Copy/paste handoff — AMD ROCm/vLLM and honest measurements

Complete AMD-01..04 after G0; see `docs/runbooks/AMD_DEPLOYMENT.md`, `docs/validation/METRIC_DEFINITIONS.md` and current host-specific hardware information.

- On an actual AMD Linux GPU cloud host, prove `/dev/kfd` and correct render node; record ROCm, GPU/VRAM, kernel, instance type and image/model digests.
- Verify chosen ROCm vLLM image tag actually exists and is compatible with target GPU; current default is illustrative, not certified. Pin digest only after working.
- Keep GPU endpoint private. Connect NSAI API through internal `http://vllm:8000/v1` in same isolated app network, or authenticated HTTPS on separate hosts. No public unauthenticated vLLM.
- Execute real model call and record raw time, outcome and token/model metadata. Force timeout and 5xx tests; no fake fallback labeled AMD.
- Use synthetic golden fixture and measured reproducible experiment; do not claim improvement without baseline, same test set and raw evidence. Save budget usage and stop GPU/VM after tests if allowed by judging requirements.

Done means ACTUAL GPU-verified inference in working end-to-end NSAI demo; not only YAML config.
