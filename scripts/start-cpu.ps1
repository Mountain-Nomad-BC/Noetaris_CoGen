$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$python = Join-Path (Get-Location) '.venv/Scripts/python.exe'
# Read-only release admission precedes installer, secrets, images and schema mutations.
$gatePython = if (Test-Path -LiteralPath $python) { $python } else { 'python' }
& $gatePython (Join-Path $PSScriptRoot 'check_release_readiness.py')
if ($LASTEXITCODE -ne 0) { throw 'Full-feature startup denied: foundation acceptance or canonical security qualification is incomplete. Existing runtime unchanged.' }
if (-not (Test-Path -LiteralPath $python)) { python -m venv .venv; if ($LASTEXITCODE -ne 0) { throw 'Venv failed.' } }
# Bootstrap the installer/build backend from reviewed artifact hashes first.
& $python -m pip install --require-hashes --only-binary=:all: -r requirements-build.lock
if ($LASTEXITCODE -ne 0) { throw 'Locked build tools failed.' }
& $python -m pip install --require-hashes --only-binary=:all: -r requirements.lock
if ($LASTEXITCODE -ne 0) { throw 'Locked runtime dependencies failed.' }
& $python -m pip install --require-hashes --only-binary=:all: -r requirements-dev.lock
if ($LASTEXITCODE -ne 0) { throw 'Locked verification tools failed.' }
& $python -m pip install --no-build-isolation --no-deps -e .
if ($LASTEXITCODE -ne 0) { throw 'Local package setup failed.' }
& $python scripts/bootstrap_secrets.py
if ($LASTEXITCODE -ne 0) { throw 'Secrets failed.' }
& (Join-Path $PSScriptRoot 'protect-secrets.ps1')
if (-not $env:NSAI_GGUF_PATH) {
    if (-not (Test-Path .env)) { throw 'Set NSAI_GGUF_PATH to a validated local GGUF file.' }
    foreach ($line in Get-Content .env) {
        if ($line -match '^NSAI_GGUF_PATH=(.+)$') { $env:NSAI_GGUF_PATH=$Matches[1] }
        if ($line -match '^NSAI_GGUF_SHA256=(.+)$') { $env:NSAI_GGUF_SHA256=$Matches[1] }
    }
}
& $python scripts/prepare_cpu_model.py
if ($LASTEXITCODE -ne 0) { throw 'Model validation failed.' }
& $python scripts/validate_compose_security.py
if ($LASTEXITCODE -ne 0) { throw 'Static security check failed.' }
$compose = @('-f','compose.yaml','-f','deploy/local/compose.cpu.yaml')
docker compose @compose config --quiet
if ($LASTEXITCODE -ne 0) { throw 'CPU config invalid.' }
# Offline tests and builds precede every schema mutation.
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed; database unchanged.' }
& $python scripts/check_compose.py
if ($LASTEXITCODE -ne 0) { throw 'Effective CPU security policy failed.' }
docker compose @compose build
if ($LASTEXITCODE -ne 0) { throw 'Build failed; database unchanged.' }
docker compose @compose up -d --wait db
if ($LASTEXITCODE -ne 0) { throw 'DB failed.' }
& $python scripts/migrate.py
if ($LASTEXITCODE -ne 0) { throw 'Migration failed.' }
docker compose @compose up -d --wait api parser llama-cpp
if ($LASTEXITCODE -ne 0) { throw 'Service readiness failed.' }
# Startup checks are observational; acceptance fixtures require a disposable stack.
& $python scripts/verify_system.py --readiness-only
if ($LASTEXITCODE -ne 0) { throw 'Readiness failed.' }
Write-Host 'CPU system ready at http://127.0.0.1:8787; role tokens are under secrets/.'
