#!/usr/bin/env bash
# 临时启动 Streamlit 1.x 对照版（与 v2 并行，默认端口 29998）

ROOT="$(cd "$(dirname "$0")" && pwd)"
CONDA_STREAMLIT="${CONDA_STREAMLIT:-streamlit}"
PORT="${STREAMLIT_PORT:-29998}"
HOST="${STREAMLIT_HOST:-127.0.0.1}"

echo "=================================================="
echo " 📋 IAMS Streamlit 临时对照部署 (localhost:$PORT)"
echo "    v2 仍在: http://127.0.0.1:29996/IAMS/"
echo "=================================================="

ps -ef | grep "[s]treamlit run app.py" | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
sleep 1

cd "$ROOT"
nohup "$CONDA_STREAMLIT" run app.py \
  --server.port "$PORT" \
  --server.address "$HOST" \
  --server.headless true \
  >> "$ROOT/streamlit_temp_log.txt" 2>&1 &

sleep 3
if curl -sf "http://127.0.0.1:$PORT/_stcore/health" >/dev/null 2>&1 || curl -sf -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT" | grep -qE '200|302'; then
  echo "  ✅ Streamlit 已启动"
  echo "  👉 对照入口: http://localhost:$PORT"
  echo "  📝 日志: tail -f $ROOT/streamlit_temp_log.txt"
  echo "  🛑 停止: bash $ROOT/stop_streamlit_temp.sh"
else
  echo "  ❌ 启动可能失败，请查看: tail -30 $ROOT/streamlit_temp_log.txt"
  tail -20 "$ROOT/streamlit_temp_log.txt" 2>/dev/null || true
fi
echo "=================================================="
