# Deployment stages and current operating boundary

The isolated integration UI is available at **http://127.0.0.1:8790**. It uses synthetic data and separate credentials/database storage. The original application stack and its data are separate and remain unchanged. Neither local health nor scoped test success grants production release admission.

## Local integration checks

Run from `AMD_Hackathon_Project` in PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts/check_deployment_stages.py
.\.venv\Scripts\python.exe scripts/check_integration.py
.\.venv\Scripts\python.exe scripts/qualify_integration_regressions.py
```

The stage assessment writes a dated, source-bound receipt and exits nonzero while any required stage remains blocked. It checks actual container/image/config identities, local HTTP readiness, anonymous document denial, retained workflow evidence, recovery evidence, partner commissioning and the unchanged release gate. It never supplies the independent admission artifacts. Actual runtime checks enforce the six-service inventory, exactly one UI loopback port, network ownership/internal isolation, non-root users, capability and namespace restrictions, and bounded CPU/memory/process limits. Regression assessment reconciles exact collected/JUnit cases, zero skips, current source/test/image identities and owned cleanup; old or edited evidence cannot grant a current regression PASS.

Existing local sign-in credentials are in `state/integration/secrets/`; use `operator.txt` only in the local credential field on the login page. Do not paste credentials into chat, reports, images, frontend source or browser storage. Reloading the page clears tab-memory credentials by design.

## Rebuild and start the isolated project

The source and model must already be verified. Retain the old image under a distinct tag before rebuilding an alias used by running qualification. Never replace an image reference while its tests are running.

```powershell
.\.venv\Scripts\python.exe scripts/start_integration.py --model-config state/integration/gemma-cpu.json
```

This command selects **only** the `noetaris-integration` project, verifies the Gemma artifact hash and GGUF architecture, uses immutable local image identities, and checks the owned database volume before applying migration helpers. Existing integration databases receive a bounded checksummed backup before migration. API health uses database readiness. The only published port is UI loopback port 8790.

CPU inference uses the explicit **source-selection** profile: Gemma selects complete source units, and the normal citation/support guard still validates them. Truncated units cannot enter the choice set; excluded units are counted and disclosed. Responses remain unverified candidates. This profile does not claim general synthesis or independent scientific reasoning. AMD/API synthesis is a separate commissioning stage.

The 4B CPU experiment is retained with its original checksum/provenance and failed deadline receipt. It is not the default CPU fallback. Do not enlarge deadlines or treat a single fixture as general quality qualification.

## Recovery rehearsal

```powershell
.\.venv\Scripts\python.exe scripts/qualify_integration_recovery.py
```

This captures the owned integration database, checks the exact backup manifest, restores into a disposable network-none PostgreSQL instance and reapplies the least-privilege role contract. Database-level privileges are not restored by a plain `pg_dump` alone. The rehearsal compares all public-table contents, validates the access-definition contract and uses the packaged application to verify the restored audit chain. Cleanup is part of its verdict.

The source must be quiescent; changing source table digests cause failure. This is not a concurrent-write/PITR proof or historical production rollback qualification. Receipts and private SQL backups stay under `state/integration/recovery/` and `state/integration/backups/`.

## AMD, Evolus and free hosted fallback

AMD and Evolus are core competition integrations. MiniLM remains a helper. CPU Gemma supplies local continuity, AMD Gemma is the intended elevation path, and the two OpenRouter Gemma **`:free`** identities provide research/fallback capacity when available and authorized.

Read-only provider discovery:

```powershell
.\.venv\Scripts\python.exe scripts/probe_gemma_providers.py
```

The optional `--smoke` flag makes one bounded synthetic call per model and can consume AMD allowance. It never sends corpus data. No priced OpenRouter alias is substituted. Existing provider evidence records AMD model-call success, hosted free-route 429s, and unsuccessful Evolus/notebook configuration discovery; consult its timestamps rather than treating observations as live availability.

Before actual app dispatch: supply Evolus application, agent/workflow and extractor identities; commission the intended dedicated AMD endpoint/credit allowance; qualify remote token admission, durable per-provider reservations/accounting, controlled egress, source-export decisions, fallback/cooldown behavior and supported-answer validation. A server credential or route-ordering function alone is not a working integration. Do not export private documents merely because a local provider is unavailable.

## Independent release stage

```powershell
.\.venv\Scripts\python.exe scripts/check_release_readiness.py
```

The release gate remains authoritative for production launchers. Required source-bound independent acceptance, canonical security artifact bytes, rights/provenance disposition, identity/ACL commissioning and unresolved criteria must actually be completed. Implementation tests, this runbook and developer-written readiness receipts cannot replace them. Do not publish a production port, migrate the original stack, upload an image or claim competition eligibility from an isolated synthetic test.

For the complete requested work, see `SUPPLIED_REQUIREMENTS_ALIGNMENT.md`, `REMAINING_WORK.md` and the execution ledger; many feature and independent-qualification items remain open beyond these local deployment checks.

## Regression runner environment

The reusable full-suite runner uses the exact current API/database image IDs and at most two workers within a 1800-second budget. Disposable databases have no host ports or persistent volumes. It never rebuilds images or restarts the running integration. Source and test changes during qualification invalidate the run. Missing cases, skips, timeouts, failures and incomplete cleanup all prevent PASS_SCOPED.

The host runner needs NumPy for the encoder window test. The current Windows test environment uses NumPy 2.5.1 installed with `--require-hashes --only-binary=:all: --no-deps` against its exact pin/hash set already retained in `requirements-semantic.lock` (extracted to `state/integration/numpy-test.lock`). This host test dependency does not change the production API dependency closure or image. The original encoder lock as a whole is qualified for Linux and should not be installed wholesale on Windows.

## Local vLLM admission and hosted dispatch boundary

The inference adapter now supports the local named `vllm` service. It sends chat messages to the server's native `/tokenize` endpoint with the default generation prompt, counts response-schema overhead separately, checks token-ID/count consistency and the actual server context, then reserves output plus the existing safety margin within the operator cap. A context change between counts fails admission. `NSAI_MODEL_TOKENIZER=vllm` explicitly selects the same adapter for a loopback vLLM server. This is an implementation and mocked-protocol result; an actual AMD/vLLM instance has not been commissioned or qualified.

Protocol reference: [official vLLM v0.15.1 tokenizer request and response definitions](https://raw.githubusercontent.com/vllm-project/vllm/v0.15.1/vllm/entrypoints/serve/tokenize/protocol.py). The deployed server/version/template and model artifact still need actual compatibility and image qualification. The patch does not select or provision a server image or imply that this reference version is the production recommendation.

Token-admission receipts now bind the exact request, configured model, endpoint hash and tokenizer adapter. vLLM generation requires such a receipt, and changing those bindings prevents dispatch. The implicit model default is Gemma 3 1B; the current Docker profile still explicitly selects its verified `nsai-local-gemma` alias and checksum.

Source-bearing tokenizer and completion dispatch to nonlocal endpoints is explicitly refused at both low-level seams. `free`, `amd-credits` and `evolus-credits` funding labels, or an injected admission dictionary, do not grant source-export permission. Independent bounded synthetic provider probes remain available. Hosted source dispatch remains unfinished until durable export authorization, accounting, allowance and retry/outcome handling are integrated; do not remove this guard merely to make a remote request work.

CPU release defaults now select the Gemma alias and source-selection strategy. The CPU model CLI verifies the exact digest and refuses non-Gemma GGUF architecture even if the file is renamed. Base and Ollama examples select Gemma; AMD model selection is explicit with no example Qwen fallback. Read-only normalization and the staged Gemma3 artifact check pass; no production profile was launched. Historical Qwen benchmark fixtures/receipts remain historical and are not current qualification. The original running stack remains unchanged.
