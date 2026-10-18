# NSAI local-to-AMD deployment runbook

**Historical starter runbook — not current Noetaris deployment instructions.** As of 2026-10-17 11:48 EDT, the current Docker project has no host-published ports, authentication is unavailable, and release admission is **DENY**. The procedures below can build/start services and are not authorized for the existing persistent stack. Do not execute them against this workspace. See [current deployment state](implementation/DEPLOYMENT_STATE.md) and [Start here](../START_HERE.md).

## Stage A — local Docker CPU/data baseline (PowerShell or terminal)

```powershell
# From the extracted NSAI_Hybrid_Starter_2026-10-12 folder
python scripts/bootstrap_secrets.py
Copy-Item .env.example .env
# Edit .env to suit the local environment; leave NSAI_MODEL_URL blank initially

docker compose config --quiet
docker compose build api
docker compose up -d db api
docker compose ps
docker compose logs --tail=100 api db
```

Open `http://127.0.0.1:8787`. Paste the content of `secrets/api_token.txt` in the browser's **Session authorization** field. Never paste the database password in the UI. The token field is cleared after clicking Connect; it is stored only in live JavaScript memory. If you refresh the page, reconnect.

This is a localhost-only development entrypoint. It is **not** suitable for sharing directly via a raw public IP.

Demo inputs (upload separately, version strings `1` and `2`):

```text
Pump-X maximum operating temperature is 85 C
```

```text
Pump-X maximum operating temperature is 75 C
```

Click **Refresh evidence**. `GET /v1/claims` must show two candidates and one conflict group; chat must refuse to call either claim verified.

Basic verification commands:

```powershell
docker compose ps
docker compose exec api id
docker compose exec api python -c "import os; print(os.getuid())"
docker compose --profile sandbox run --rm sandbox-smoke
curl.exe http://127.0.0.1:8787/healthz
```

Expected API UID: `10001`, sandbox-smoke runs with `network_mode: none`; but this alone is **not** an isolation penetration test.

Stop gracefully: `docker compose down`. **Do not use `down -v`** unless you intend to destroy the database named volume. For a schema change after the first initialization, use a versioned migration; changing `deploy/init.sql` does not reinitialize an existing volume.

## Stage B — optional model on the same AMD Linux host

Before invoking Docker: confirm AMD compute permissions (`rocminfo`), `ls /dev/dri/render*`, available VRAM, Docker Compose version, and installed AMD drivers. Make sure the model is approved for the event, publicly distributable, and fits the rented accelerator.

```bash
cp .env.example .env
python3 scripts/bootstrap_secrets.py
# Edit .env, set NSAI_MODEL_URL=http://vllm:8000/v1
# Choose NSAI_GPU_RENDER_DEVICE, NSAI_VLLM_IMAGE and NSAI_VLLM_MODEL

docker compose -f compose.yaml -f deploy/amd/compose.amd.yaml --profile amd config --quiet
docker compose -f compose.yaml -f deploy/amd/compose.amd.yaml --profile amd up -d --build
# check model diagnostics:
docker compose -f compose.yaml -f deploy/amd/compose.amd.yaml --profile amd logs --tail=100 vllm
```

The API container connects to the model over the internal Compose `app_net` using `http://vllm:8000/v1`. Nothing in this override publishes the model endpoint to a host port. If ROCm cannot access GPU, resolve device and group permissions; do not immediately enable privileged mode.

To invoke real model inference, call authenticated `POST /v1/reason` with `{"question":"What is the maximum operating temperature of Pump-X?"}`. Response mode is **`model_unverified`** and should never imply the retrieved candidate claims are true. The ordinary `/v1/chat` route remains a deterministic evidence-review demonstration.

## Stage C — split local app and rented AMD host

If AMD GPU runs on a different host, do not set an `http://<public-IP>:8000` endpoint. Put the hosts on a private secured tunnel/network, or provision TLS + authenticated endpoint and network firewall. In that case `NSAI_MODEL_URL=https://<trusted-private-name>/v1` and mount its API key as a Compose secret before enabling public access. The simple starter UI does not implement browser-side cloud credentials.

## Stage D — cloud submission and continuous deployment

1. Select frontend/API host, DB (managed Supabase PostgreSQL is one option) and AMD inference VM.
2. Replace the static bearer token with gateway authentication and per-user authorization. Place all ingress behind TLS.
3. Migrate SQL with revisioned migrations. Add encryption and database backups.
4. Pin image digests, generate a software bill of materials, run dependency/container scanners.
5. Deploy first to private staging. Test: authentication, upload limits, source lineage, conflict detection, model unavailability, DB restore, network isolation, service restarts and resource exhaustion.
6. Open only documented public ports, set inbound firewalls and allowed egress destinations. Keep database and model backends private.
7. Record AMD-hosted inference evidence (GPU identity, image digest, model name, exact test input/output, timestamps and latency). No fake benchmark numbers.

## Notes about this artifact

- Docker CLI is **not available** in the artifact-building environment; Compose YAML parsing, Python compilation and isolated unit tests were completed, but image build/startup/health, OS isolation and ROCm execution were not tested here.
- No actual Remy or PX runtime module is copied into this starter. The architecture audit lists candidate adapters that require a later measured dependency/contract port.
- No raw PDF upload, genuine TurnBurn indexing, embeddings, autonomous learning or protected arbitrary-code execution has been implemented yet.
