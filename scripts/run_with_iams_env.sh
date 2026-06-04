#!/bin/bash
# 以 IAMS 项目网络策略启动子进程（不修改全局环境）
set -euo pipefail

WORKDIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$WORKDIR/config/network.env"

if [ -f "$CONFIG" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$CONFIG"
    set +a
fi

if [ "${IAMS_DISABLE_PROXY:-1}" = "1" ]; then
    unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy NO_PROXY no_proxy
else
    if [ -n "${IAMS_HTTP_PROXY:-}" ]; then
        export HTTP_PROXY="$IAMS_HTTP_PROXY"
        export http_proxy="$IAMS_HTTP_PROXY"
        export HTTPS_PROXY="${IAMS_HTTPS_PROXY:-$IAMS_HTTP_PROXY}"
        export https_proxy="${IAMS_HTTPS_PROXY:-$IAMS_HTTP_PROXY}"
    fi
    unset ALL_PROXY all_proxy
fi

cd "$WORKDIR"
exec "$@"
