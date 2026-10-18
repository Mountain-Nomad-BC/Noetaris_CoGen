$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'start-cpu.ps1')
exit $LASTEXITCODE
