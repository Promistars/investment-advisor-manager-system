"""
IAMS 项目专用网络环境（仅影响本仓库内 Python/脚本进程，不修改全局 shell 配置）。

配置：config/network.env
  IAMS_DISABLE_PROXY=1   # 默认直连，忽略 shell 里的 HTTP_PROXY / ALL_PROXY
  IAMS_HTTP_PROXY=...    # 仅当 IAMS_DISABLE_PROXY=0 时为本项目单独启用 HTTP 代理
"""
from __future__ import annotations

import os
from pathlib import Path

_PROXY_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "http_proxy",
    "https_proxy",
    "ALL_PROXY",
    "all_proxy",
    "NO_PROXY",
    "no_proxy",
)

_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "network.env"
_EASTMONEY_KLINE_HOST = "push2his.eastmoney.com"
_eastmoney_kline_cache: bool | None = None


def _parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def apply_project_network_env() -> None:
    """在 import akshare/baostock/requests 之前调用。"""
    cfg = _parse_env_file(_CONFIG_PATH)
    disable = cfg.get("IAMS_DISABLE_PROXY", "1").lower() in ("1", "true", "yes")

    for key in _PROXY_KEYS:
        os.environ.pop(key, None)

    if disable:
        return

    http_proxy = cfg.get("IAMS_HTTP_PROXY") or cfg.get("HTTP_PROXY")
    https_proxy = cfg.get("IAMS_HTTPS_PROXY") or cfg.get("HTTPS_PROXY") or http_proxy
    if http_proxy:
        os.environ["HTTP_PROXY"] = http_proxy
        os.environ["http_proxy"] = http_proxy
    if https_proxy:
        os.environ["HTTPS_PROXY"] = https_proxy
        os.environ["https_proxy"] = https_proxy


def eastmoney_kline_available(timeout: float = 6.0) -> bool:
    """
    检测东财 push2his K 线接口是否可达。
    本服务器上该域名常被防火墙拦截，其它东财接口（如分红）可能仍可用。
    """
    global _eastmoney_kline_cache
    if _eastmoney_kline_cache is not None:
        return _eastmoney_kline_cache
    try:
        import requests

        url = f"https://{_EASTMONEY_KLINE_HOST}/api/qt/stock/kline/get"
        params = {
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "klt": "101",
            "fqt": "1",
            "secid": "1.601318",
            "beg": "20260528",
            "end": "20260604",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://quote.eastmoney.com/",
        }
        r = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=timeout,
            proxies={"http": None, "https": None},
        )
        _eastmoney_kline_cache = r.status_code == 200 and "klines" in r.text
    except Exception:
        _eastmoney_kline_cache = False
    return _eastmoney_kline_cache
