#!/bin/bash

echo "========================================"
echo "🔄 开始重启 量化私募看板系统..."
echo "========================================"

# 1. 杀掉原有的进程 (清理门户)
echo "🧹 正在清理旧进程..."
pkill -f "python auto_fetch.py" || true
pkill -f "streamlit run app.py" || true
pkill -f "ngrok http" || true

# 稍微等待 2 秒，确保端口完全释放
sleep 2 

# 2. 启动数据爬虫引擎
echo "🚀 [1/3] 启动 数据爬虫引擎 (auto_fetch.py)..."
nohup python auto_fetch.py > fetch_log.txt 2>&1 &

# 3. 启动前端网站引擎
echo "🖥️ [2/3] 启动 前端网站引擎 (app.py)..."
nohup streamlit run app.py --server.port 29996 --server.address 0.0.0.0 > web_log.txt 2>&1 &

# 4. 启动域名穿透引擎
echo "🌐 [3/3] 启动 域名穿透引擎 (ngrok)..."
nohup /home/muchenzhang/fnc/IAMS_1.1/ngrok http --url=https://unintimate-armida-insensibly.ngrok-free.dev 29996 > ngrok_log.txt 2>&1 &

# 等待 1 秒，让所有进程稳定跑起来
sleep 1

echo "========================================"
echo "✅ 所有服务启动完成，系统已在后台稳定运行！"
echo "========================================"
echo "👉 运行状态/报错排查请使用以下命令："
echo "   tail -n 20 web_log.txt"
echo "   tail -n 20 fetch_log.txt"
echo "   tail -n 20 ngrok_log.txt"
echo "----------------------------------------"
echo "🎉 系统公网访问地址已就绪 (通常按住 Ctrl 点击可直接打开)："
echo -e "\033[1;34m👉 https://unintimate-armida-insensibly.ngrok-free.dev\033[0m"
echo "========================================"