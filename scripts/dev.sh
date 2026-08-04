#!/usr/bin/env bash
# Dev helpers for HH Leads Dashboard.
# Usage:
#   ./scripts/dev.sh api      # uvicorn :8000
#   ./scripts/dev.sh web      # vite :5173 (proxy /api → :8000)
#   ./scripts/dev.sh build    # vue production build

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cmd="${1:-}"

case "$cmd" in
  api)
    cd "$ROOT"
    # shellcheck disable=SC1091
    source .venv/bin/activate
    exec uvicorn api:app --reload --host 127.0.0.1 --port 8000
    ;;
  web)
    cd "$ROOT/web"
    exec npm run dev
    ;;
  build)
    cd "$ROOT/web"
    exec npm run build
    ;;
  *)
    echo "Usage: $0 {api|web|build}" >&2
    exit 1
    ;;
esac
