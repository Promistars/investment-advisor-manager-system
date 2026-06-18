import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PREFS_FILE = ROOT / "user_prefs.json"

DEFAULTS: dict[str, Any] = {
    "lang": "zh",
    "pnl_colors": "cn",
    "date_format": "iso",
    "compact_ui": False,
    "show_emoji": True,
    "default_view": "month",
}


def _normalize_lang(raw: Any) -> str:
    s = str(raw or "zh").strip().lower()
    if s in ("zh", "chinese", "cn", "中文"):
        return "zh"
    if s in ("en", "english", "英文"):
        return "en"
    return "zh"


def _normalize_pnl_colors(raw: Any, lang: str) -> str:
    s = str(raw or "").lower()
    if s in ("cn",) or "red up" in s or "a股" in s:
        return "cn"
    if s in ("western",) or "green up" in s or "western" in s:
        return "western"
    return "cn" if lang == "zh" else "western"


def _normalize_date_format(raw: Any) -> str:
    s = str(raw or "iso")
    return s if s in ("iso", "cn", "us") else "iso"


def _normalize_default_view(raw: Any) -> str:
    s = str(raw or "month").lower()
    if s in ("month", "monthly"):
        return "month"
    if s in ("quarter", "quarterly"):
        return "quarter"
    if s in ("year", "yearly"):
        return "year"
    return "month"


def normalize_prefs(prefs: dict[str, Any]) -> dict[str, Any]:
    lang = _normalize_lang(prefs.get("lang"))
    return {
        "lang": lang,
        "pnl_colors": _normalize_pnl_colors(prefs.get("pnl_colors"), lang),
        "date_format": _normalize_date_format(prefs.get("date_format")),
        "compact_ui": bool(prefs.get("compact_ui", False)),
        "show_emoji": prefs.get("show_emoji", True) is not False,
        "default_view": _normalize_default_view(prefs.get("default_view")),
    }


def _sync_pnl_from_lang(prefs: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_prefs(prefs)
    normalized["pnl_colors"] = "cn" if normalized["lang"] == "zh" else "western"
    return normalized


def _guest_key() -> str:
    return "_guest_"


def _load_all() -> dict:
    if not PREFS_FILE.exists():
        return {}
    try:
        with open(PREFS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_all(data: dict) -> None:
    with open(PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def user_key(username: Optional[str]) -> str:
    return username if username else _guest_key()


def get_user_prefs(username: Optional[str] = None) -> dict[str, Any]:
    merged = deepcopy(DEFAULTS)
    stored = _load_all().get(user_key(username), {})
    if isinstance(stored, dict):
        for k in DEFAULTS:
            if k in stored:
                merged[k] = stored[k]
    return _sync_pnl_from_lang(merged)


def save_user_prefs(username: Optional[str], prefs: dict[str, Any]) -> None:
    data = _load_all()
    key = user_key(username)
    current = data.get(key, {})
    if not isinstance(current, dict):
        current = {}
    incoming = normalize_prefs({**current, **prefs})
    for k in DEFAULTS:
        if k in incoming:
            current[k] = incoming[k]
    current = _sync_pnl_from_lang(current)
    data[key] = current
    _save_all(data)


def reset_user_prefs(username: Optional[str]) -> None:
    data = _load_all()
    data[user_key(username)] = deepcopy(DEFAULTS)
    _save_all(data)


def merge_on_login(username: str) -> dict[str, Any]:
    guest = get_user_prefs(None)
    user = get_user_prefs(username)
    merged = deepcopy(DEFAULTS)
    merged.update(user)
    if all(user.get(k) == DEFAULTS[k] for k in DEFAULTS):
        merged.update({k: guest[k] for k in ("lang", "pnl_colors", "date_format", "compact_ui", "show_emoji")})
    save_user_prefs(username, merged)
    return get_user_prefs(username)


def migrate_stored_prefs_file() -> None:
    """Rewrite legacy Streamlit values (Chinese, CN red up, etc.) on disk."""
    data = _load_all()
    if not data:
        return
    changed = False
    for key, stored in list(data.items()):
        if not isinstance(stored, dict):
            continue
        normalized = _sync_pnl_from_lang({**DEFAULTS, **stored})
        if normalized != stored:
            data[key] = normalized
            changed = True
    if changed:
        _save_all(data)
