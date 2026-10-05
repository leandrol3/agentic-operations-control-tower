#!/usr/bin/env bash
# Stdio launcher: same server/capability, no HTTP request, no output on stdout.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
docker_bin="${DOCKER_BIN:-}"
if [[ -z "$docker_bin" ]]; then
  docker_bin="$(command -v docker || true)"
fi
if [[ -z "$docker_bin" ]]; then
  docker_bin=/Applications/Docker.app/Contents/Resources/bin/docker
fi
if [[ ! -x "$docker_bin" ]]; then
  echo 'Docker CLI não encontrado. Instale Docker Desktop ou configure DOCKER_BIN.' >&2
  exit 1
fi
exec "$docker_bin" compose -f compose.yaml -f compose.override.yaml -f compose.lesson04.yaml \
  exec -T -e OTEL_SERVICE_NAME=control-tower-mcp api \
  python -m control_tower.mcp.server
