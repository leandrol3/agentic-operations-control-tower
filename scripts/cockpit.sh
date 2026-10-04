#!/usr/bin/env bash
# One explicit overlay; existing lesson profiles remain untouched.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
export LOCAL_UID="$(id -u)"
export LOCAL_GID="$(id -g)"
export LLM_MODE="${LLM_MODE:-openai}"
export OTEL_ENABLED="${OTEL_ENABLED:-true}"
exec docker compose -f compose.yaml -f compose.override.yaml -f compose.lesson04.yaml \
  -f compose.lesson04-complete.yaml -f compose.lesson04-cockpit.yaml "$@"
