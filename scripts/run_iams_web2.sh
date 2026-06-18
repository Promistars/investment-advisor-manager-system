#!/usr/bin/env bash
# Foreground IAMS v2 (FastAPI + built React SPA) — for systemd Type=simple
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${CONDA_PYTHON:-python3}"
NODE="${CONDA_NODE:-}"
PORT="${IAMS_PORT:-29996}"

export IAMS_ROOT="$ROOT"
export PATH="${NODE:+$NODE:}$PATH"

cd "$ROOT/backend"
"$PYTHON" -m pip install -q -r requirements.txt

cd "$ROOT/frontend"
if ! command -v npm >/dev/null 2>&1; then
  echo "npm not found — set CONDA_NODE or install Node.js" >&2
  exit 1
fi
npm run build

cd "$ROOT"
exec env IAMS_ROOT="$ROOT" "$PYTHON" -m uvicorn app.main:app \
  --app-dir "$ROOT/backend" --host 0.0.0.0 --port "$PORT"
