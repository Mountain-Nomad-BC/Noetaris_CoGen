#!/usr/bin/env bash
# Run ON AMD Linux host. Probe only; never changes system configuration.
set -euo pipefail
uname -a
printf '\nDevice access:\n'
for f in /dev/kfd /dev/dri/renderD128; do
  if test -e "$f"; then ls -l "$f"; else printf 'MISSING: %s\n' "$f"; fi
done
printf '\nDocker versions:\n'
command -v docker >/dev/null && docker version --format '{{.Server.Version}}' || true
command -v docker >/dev/null && docker compose version || true
printf '\nROCm available?\n'
if command -v rocminfo >/dev/null; then rocminfo | grep -E 'Name:|Marketing Name:' | head -20; else echo 'rocminfo not installed on host'; fi
printf '\nDisk/Memory:\n'; df -h .; free -h || true
printf '\nNo GPU proof is implied if checks above fail.\n'
