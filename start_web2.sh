#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/load_local_env.sh"
CONDA_PYTHON="${CONDA_PYTHON:-python3}"
CONDA_NODE="${CONDA_NODE:-}"

cd "$ROOT"

echo "Starting IAMS API on :8000 ..."
cd backend
"$CONDA_PYTHON" -m pip install -q -r requirements.txt 2>/dev/null || true
cd "$ROOT"
IAMS_ROOT="$ROOT" "$CONDA_PYTHON" -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

echo "Starting IAMS Web on :5173 ..."
export PATH="${CONDA_NODE:+$CONDA_NODE:}$PATH"
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173 &
WEB_PID=$!

trap 'kill $API_PID $WEB_PID 2>/dev/null' EXIT
wait
