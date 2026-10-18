#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo 'This legacy launcher is retired. Use scripts/start-cpu.ps1 for the supported CPU workflow; no services were changed.' >&2
exit 2
