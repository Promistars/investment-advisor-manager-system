#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/load_local_env.sh"
USER_SYSTEMD="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
PYTHON="${CONDA_PYTHON:-python3}"
PORT="${IAMS_PORT:-29996}"

echo "=================================================="
echo " IAMS systemd 托管安装"
echo "=================================================="

# 用户级服务在登出后仍需运行
if [ "$(loginctl show-user "$(whoami)" -p Linger --value 2>/dev/null)" != "yes" ]; then
    echo "启用 linger（登出后仍保持 user systemd 服务）..."
    loginctl enable-linger "$(whoami)"
fi

mkdir -p "$USER_SYSTEMD"
chmod +x "$ROOT/iams_healthcheck.sh" "$ROOT/scripts/run_iams_web.sh" "$ROOT/scripts/run_with_iams_env.sh"

install_unit() {
    local src="$1"
    local name
    name="$(basename "$src")"
    sed -e "s|@IAMS_ROOT@|$ROOT|g" -e "s|@PYTHON@|$PYTHON|g" "$src" > "$USER_SYSTEMD/$name"
}

for f in "$ROOT/systemd/"*.service "$ROOT/systemd/"*.timer; do
    [ -f "$f" ] || continue
    install_unit "$f"
done

echo "清理旧 nohup 进程，避免与 systemd 重复..."
ps -ef | grep "[u]vicorn app.main:app" | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
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
echo " 完成。Web: http://127.0.0.1:$PORT/IAMS/"
echo " 探活日志: tail -f $ROOT/iams_healthcheck.log"
echo " 手动探活: $ROOT/iams_healthcheck.sh"
echo "=================================================="
