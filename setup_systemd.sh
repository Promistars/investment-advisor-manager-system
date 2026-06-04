#!/bin/bash
set -euo pipefail

WORKDIR=/home/muchenzhang/fnc/IAMS_1.2
USER_SYSTEMD="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

echo "=================================================="
echo " IAMS systemd 托管安装"
echo "=================================================="

# 用户级服务在登出后仍需运行
if [ "$(loginctl show-user "$(whoami)" -p Linger --value 2>/dev/null)" != "yes" ]; then
    echo "启用 linger（登出后仍保持 user systemd 服务）..."
    loginctl enable-linger "$(whoami)"
fi

mkdir -p "$USER_SYSTEMD"
chmod +x "$WORKDIR/iams_healthcheck.sh"
cp "$WORKDIR/systemd/"*.service "$WORKDIR/systemd/"*.timer "$USER_SYSTEMD/"

echo "清理旧 nohup 进程，避免与 systemd 重复..."
ps -ef | grep "[s]treamlit run app.py --server.port 29996" | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
ps -ef | grep "[p]ython auto_fetch.py" | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
sleep 1

systemctl --user daemon-reload
systemctl --user enable iams-web.service iams-fetch.service iams-healthcheck.timer
systemctl --user restart iams-web.service iams-fetch.service
systemctl --user start iams-healthcheck.timer

echo ""
echo "状态:"
systemctl --user status iams-web.service iams-fetch.service iams-healthcheck.timer --no-pager || true
echo ""
echo "下次探活时间:"
systemctl --user list-timers iams-healthcheck.timer --no-pager || true
echo "=================================================="
echo " 完成。Web: http://112.49.20.151:29996"
echo " 探活日志: tail -f $WORKDIR/iams_healthcheck.log"
echo " 手动探活: $WORKDIR/iams_healthcheck.sh"
echo "=================================================="
