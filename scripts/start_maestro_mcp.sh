#!/usr/bin/env bash
# Stdout is reserved for MCP. Reuse the running cockpit API's image/env/knowledge mount.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
exec bash scripts/cockpit.sh exec -T -e OTEL_SERVICE_NAME=control-tower-maestro-mcp api \
  python -m control_tower.mcp.server --with-maestro
