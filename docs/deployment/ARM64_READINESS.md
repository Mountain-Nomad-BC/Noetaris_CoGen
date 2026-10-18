# ARM64 readiness

Status: BLOCKED for physical ARM64 qualification. The current Docker runtime is x86 and cannot establish OCI A1 readiness.

`state/arm64-readiness/base-platforms.json` records inspected immutable base indexes. `state/arm64-readiness/api-wheels/` contains hash-checked CPython 3.12 Linux ARM64 wheel downloads from the pinned API requirements. Availability is supporting evidence, not execution acceptance. Encoder/native parser dependencies, complete image builds, database initialization and restore, worker behavior and performance still need an actual ARM64 host.

`deploy/oci/compose.yaml` requests five linux/arm64 services with explicit bounds: API 768 MiB/1 CPU, PostgreSQL 1024 MiB/1 CPU, parser 384 MiB/0.5 CPU, encoder 768 MiB/1 CPU, edge 128 MiB/0.25 CPU. Total configured limits are 3072 MiB and 3.75 CPU, excluding host/Docker overhead, disk/cache and backups. This is a bounded starting profile, not a capacity guarantee. Do not assume free-tier availability. No CPU language model is provisioned on OCI by this profile; inference must report unavailable until the protected AMD path is commissioned.

Acceptance requires real ARM64 immutable image digests, native dependency execution, full regression and migration/restore checks, realistic concurrent workloads, memory/OOM/latency measurements, disk growth and off-host restore evidence. Never relabel x86 images as ARM64. No hardware was provisioned in this preparation.

## Current dependency observations

Python, Node and Nginx base indexes all advertise linux/arm64 (manifest inspection only). Hash-checked ARM64-compatible distributions for all 49 explicitly pinned API/encoder requirements were downloaded to `state/arm64-readiness/encoder-wheels/`; see `encoder-wheel-availability.log`. The command uses `--no-deps` to test each pinned distribution independently. The earlier full-resolution attempt on Windows requested Windows-only colorama through tqdm and correctly failed hash closure; `encoder-wheel-check.log` is retained. Neither attempt proves Linux transitive dependency closure. Complete image execution, native parser/encoder behavior and performance remain unqualified.

## Local execution boundary observed

On October 17, a read-only, network-none, capability-dropped attempt to run the pinned PostgreSQL ARM64 base locally failed with `exec /bin/sh: exec format error`; see `state/arm64-readiness/postgres-base-packages.log`. The Docker daemon is x86_64 and has no working ARM64 execution path in this session. No privileged emulator registration or host-kernel change was made. Actual native OCI ARM64 builds/execution remain required; the base download and wheel availability do not substitute for them.
