"""User preferences: persist + session sync."""
from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any, Optional

PREFS_FILE = "user_prefs.json"

DEFAULTS: dict[str, Any] = {
    "lang": "zh",
    "pnl_colors": "cn",
    "date_format": "iso",
    "compact_ui": False,
    "show_emoji": True,
    "default_view": "month",
}

# Widget keys are separate from stored keys to avoid Streamlit session conflicts.
WIDGET_KEYS: dict[str, str] = {
    "lang": "pref_lang",
    "pnl_colors": "pref_pnl_colors",
    "date_format": "pref_date_format",
    "default_view": "pref_default_view",
    "compact_ui": "pref_compact_ui",
    "show_emoji": "pref_show_emoji",
}


def _guest_key() -> str:
    return "_guest_"


def _load_all() -> dict:
    if not os.path.exists(PREFS_FILE):
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


def widget_key(pref_key: str) -> str:
    return WIDGET_KEYS.get(pref_key, pref_key)


def get_user_prefs(username: Optional[str] = None) -> dict[str, Any]:
    merged = deepcopy(DEFAULTS)
    stored = _load_all().get(user_key(username), {})
    if isinstance(stored, dict):
        for k in DEFAULTS:
            if k in stored:
                merged[k] = stored[k]
    return merged


def save_user_prefs(username: Optional[str], prefs: dict[str, Any]) -> None:
    data = _load_all()
    key = user_key(username)
    current = data.get(key, {})
    if not isinstance(current, dict):
        current = {}
    for k in DEFAULTS:
        if k in prefs:
            current[k] = prefs[k]
    data[key] = current
    _save_all(data)


def reset_user_prefs(username: Optional[str]) -> None:
    data = _load_all()
    data[user_key(username)] = deepcopy(DEFAULTS)
    _save_all(data)


def get_pref(key: str) -> Any:
    import streamlit as st

    wk = widget_key(key)
    if wk in st.session_state:
        return st.session_state[wk]
    return DEFAULTS.get(key)


def bootstrap_from_query(query_params) -> None:
    import streamlit as st

    if "lang" in query_params and query_params.get("lang") in ("zh", "en"):
        st.session_state[widget_key("lang")] = query_params.get("lang")
    if "view" in query_params and query_params.get("view") in ("month", "quarter", "year"):
        st.session_state[widget_key("default_view")] = query_params.get("view")


def sync_session(username: Optional[str] = None, *, force_load: bool = False) -> dict[str, Any]:
    import streamlit as st

    target_user = user_key(username)
    if st.session_state.get("_prefs_user") != target_user:
        force_load = True

    if force_load or not st.session_state.get("_prefs_loaded"):
        stored = get_user_prefs(username)
        for k, v in stored.items():
            st.session_state[widget_key(k)] = v
        st.session_state._prefs_loaded = True
        st.session_state._prefs_user = target_user
    return {k: get_pref(k) for k in DEFAULTS}


def persist_session(username: Optional[str]) -> None:
    import streamlit as st

    saved = {k: st.session_state.get(widget_key(k), DEFAULTS[k]) for k in DEFAULTS}
    save_user_prefs(username, saved)
    st.session_state._prefs_user = user_key(username)


def on_user_login(username: str) -> None:
    """Persist merged prefs on login; reload on next rerun before widgets mount."""
    import streamlit as st

    guest = get_user_prefs(None)
    user = get_user_prefs(username)
    merged = deepcopy(DEFAULTS)
    merged.update(user)
    if all(user.get(k) == DEFAULTS[k] for k in DEFAULTS):
        merged.update({k: guest[k] for k in ("lang", "pnl_colors", "date_format", "compact_ui", "show_emoji")})
    save_user_prefs(username, merged)
    st.session_state._prefs_loaded = False
    st.session_state._prefs_user = None
