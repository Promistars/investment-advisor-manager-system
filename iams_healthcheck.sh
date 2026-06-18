#!/bin/bash
# 探活：Web 无响应或 fetch 进程不在时，通过 systemd 拉起（最多约 1h 恢复一次检查）

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG="$ROOT/iams_healthcheck.log"
PORT="${IAMS_PORT:-29996}"
WEB_URL="http://127.0.0.1:${PORT}/IAMS/api/health"
WEB_TIMEOUT=8

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

web_ok() {
    local i
    for i in 1 2 3; do
        if curl -sf --connect-timeout "$WEB_TIMEOUT" "$WEB_URL" >/dev/null 2>&1; then
            return 0
        fi
        sleep 3
    done
    return 1
}

fetch_ok() {
    systemctl --user is-active --quiet iams-fetch.service
}

recover_web() {
    log "Web 探活失败，执行: systemctl --user restart iams-web.service"
    systemctl --user restart iams-web.service
}

recover_fetch() {
    log "Fetch 探活失败，执行: systemctl --user restart iams-fetch.service"
    systemctl --user restart iams-fetch.service
}

if web_ok; then
    log "Web OK ($WEB_URL)"
else
    recover_web
fi

if fetch_ok; then
    log "Fetch OK (iams-fetch.service active)"
else
    recover_fetch
fi
