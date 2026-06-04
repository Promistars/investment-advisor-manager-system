#!/bin/bash

echo "=================================================="
echo " 🔄 IAMS 私募专户管理系统 - 自动化运维引擎启动"
echo "=================================================="

WORKDIR=/home/muchenzhang/fnc/IAMS_1.2

# 优先走 systemd（已安装时）
if systemctl --user is-enabled iams-web.service &>/dev/null; then
    echo "📦 使用 systemd 重启 iams-web / iams-fetch ..."
    ps -ef | grep "[s]treamlit run app.py --server.port 29996" | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
    ps -ef | grep "[p]ython auto_fetch.py" | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
    sleep 1
    systemctl --user restart iams-web.service iams-fetch.service
    echo "  👉 Web 大屏 (systemd: iams-web.service, 端口 29996)"
    echo "  👉 爬虫调度 (systemd: iams-fetch.service)"
    echo "  🌐 访问地址: http://112.49.20.151:29996"
    echo "  ⏱️  探活: iams-healthcheck.timer（约每 1h，被杀后自动恢复）"
    systemctl --user --no-pager status iams-web.service iams-fetch.service 2>/dev/null | head -20 || true
    echo "=================================================="
    exit 0
fi

# 回退：nohup 模式（未执行 setup_systemd.sh 时）
echo "🔪 [1/2] 正在清理历史遗留进程..."
ps -ef | grep "[s]treamlit run app.py --server.port 29996" | awk '{print $2}' | xargs -r kill -9
ps -ef | grep "[p]ython auto_fetch.py" | awk '{print $2}' | xargs -r kill -9
sleep 1

CONDA_PYTHON=/home/muchenzhang/miniconda3/envs/IAMS/bin/python
CONDA_STREAMLIT=/home/muchenzhang/miniconda3/envs/IAMS/bin/streamlit

echo "🚀 正在重新拉起核心业务线 (nohup 模式)..."
echo "  💡 建议执行: bash $WORKDIR/setup_systemd.sh"

cd "$WORKDIR" && nohup $CONDA_STREAMLIT run app.py --server.port 29996 --server.address 0.0.0.0 >> web_log.txt 2>&1 &
echo "  👉 Web 大屏服务已挂载 (端口: 29996)"
echo "  🌐 访问地址: http://112.49.20.151:29996"

nohup $CONDA_PYTHON "$WORKDIR/auto_fetch.py" >> "$WORKDIR/fetch_log.txt" 2>&1 &
echo "  👉 爬虫调度中心已挂载 (静默等待 18:00 触发)"

echo "=================================================="
echo " 🎉 一键重启大功告成！"
echo " 💡 查看网页日志: tail -f $WORKDIR/web_log.txt"
echo " 💡 查看抓取日志: tail -f $WORKDIR/fetch_log.txt"
echo "=================================================="
