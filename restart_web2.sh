#!/usr/bin/env bash
# IAMS v2 — single-port FastAPI + React (replaces Streamlit on 29996)

ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/load_local_env.sh"
CONDA_PYTHON="${CONDA_PYTHON:-python3}"
CONDA_NODE="${CONDA_NODE:-}"
PORT="${IAMS_PORT:-29996}"

echo "=================================================="
echo " 🚀 IAMS v2 — FastAPI + React (port $PORT)"
echo "=================================================="

ps -ef | grep "[s]treamlit run app.py" | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
ps -ef | grep "[u]vicorn app.main:app" | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
ps -ef | grep "[v]ite preview" | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
sleep 1

cd "$ROOT/backend"
"$CONDA_PYTHON" -m pip install -q -r requirements.txt

export PATH="${CONDA_NODE:+$CONDA_NODE:}$PATH"
cd "$ROOT/frontend"
if ! command -v npm >/dev/null 2>&1; then
  echo "  ❌ npm not found — install Node.js or set CONDA_NODE"
  exit 1
fi
if ! npm run build >> "$ROOT/web_build_log.txt" 2>&1; then
  echo "  ❌ Frontend build failed — see web_build_log.txt"
  exit 1
fi

cd "$ROOT"
nohup env IAMS_ROOT="$ROOT" "$CONDA_PYTHON" -m uvicorn app.main:app \
  --app-dir "$ROOT/backend" --host 0.0.0.0 --port "$PORT" >> "$ROOT/web_log.txt" 2>&1 &
echo "  👉 Web + API: http://127.0.0.1:$PORT/IAMS/"

if ! pgrep -f "python.*auto_fetch.py" >/dev/null; then
  nohup "$CONDA_PYTHON" "$ROOT/auto_fetch.py" >> "$ROOT/fetch_log.txt" 2>&1 &
  echo "  👉 Fetch scheduler started"
fi

echo "=================================================="
