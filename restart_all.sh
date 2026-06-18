#!/bin/bash

echo "=================================================="
echo " 🔄 IAMS 私募专户管理系统 - 自动化运维引擎启动"
echo "=================================================="

ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT="${IAMS_PORT:-29996}"

# 优先走 systemd（已安装时）
if systemctl --user is-enabled iams-web.service &>/dev/null; then
    echo "📦 使用 systemd 重启 iams-web / iams-fetch ..."
    ps -ef | grep "[u]vicorn app.main:app" | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
    ps -ef | grep "[p]ython auto_fetch.py" | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
    sleep 1
    systemctl --user restart iams-web.service iams-fetch.service
    echo "  👉 Web (systemd: iams-web.service, 端口 $PORT)"
    echo "  👉 爬虫调度 (systemd: iams-fetch.service)"
    echo "  🌐 访问地址: http://127.0.0.1:$PORT/IAMS/"
    echo "  ⏱️  探活: iams-healthcheck.timer（约每 1h，被杀后自动恢复）"
    systemctl --user --no-pager status iams-web.service iams-fetch.service 2>/dev/null | head -20 || true
    echo "=================================================="
    exit 0
fi

# 回退：nohup 模式（未执行 setup_systemd.sh 时）
echo "🔪 [1/2] 正在清理历史遗留进程..."
ps -ef | grep "[u]vicorn app.main:app" | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
ps -ef | grep "[p]ython auto_fetch.py" | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
sleep 1

echo "🚀 正在重新拉起核心业务线 (nohup 模式)..."
echo "  💡 建议执行: bash $ROOT/setup_systemd.sh"

bash "$ROOT/restart_web.sh"

echo "=================================================="
echo " 🎉 一键重启大功告成！"
echo " 💡 查看网页日志: tail -f $ROOT/web_log.txt"
echo " 💡 查看抓取日志: tail -f $ROOT/fetch_log.txt"
echo "=================================================="
