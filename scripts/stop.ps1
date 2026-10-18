$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
docker compose -f compose.yaml -f deploy/local/compose.cpu.yaml down
if ($LASTEXITCODE -ne 0) { throw 'Stop failed.' }
Write-Host 'Project containers stopped; database and model volumes retained.'
