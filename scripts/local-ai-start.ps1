$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'start-cpu.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Canonical CPU startup failed.' }
