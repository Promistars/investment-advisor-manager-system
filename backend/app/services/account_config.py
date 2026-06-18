"""Account config helpers (start date lives in portfolio_engine; last_type here)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ACCOUNT_CONFIG_FILE = ROOT / "account_config.json"


def _load() -> dict:
    if not ACCOUNT_CONFIG_FILE.exists():
        return {}
    try:
        with open(ACCOUNT_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    with open(ACCOUNT_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_last_type(user: str, acc: str, default: str = "转入本金") -> str:
    return _load().get(f"{user}_{acc}_last_type", default)


def save_last_type(user: str, acc: str, type_str: str) -> None:
    data = _load()
    data[f"{user}_{acc}_last_type"] = type_str
    _save(data)
