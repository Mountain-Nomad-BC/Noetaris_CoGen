$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$python = Join-Path (Get-Location) '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run scripts/start-cpu.ps1 to prepare the local environment first.' }
& $python -m compileall -q src scripts
if ($LASTEXITCODE -ne 0) { throw 'Python compilation failed.' }
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Pytest failed.' }
& $python scripts/validate_compose_security.py
if ($LASTEXITCODE -ne 0) { throw 'Static Compose policy failed.' }
& $python scripts/check_secret_hygiene.py
if ($LASTEXITCODE -ne 0) { throw 'Local secret hygiene failed.' }
Write-Host 'Checks passed (runtime Docker/AMD verification NOT included)' -ForegroundColor Green
