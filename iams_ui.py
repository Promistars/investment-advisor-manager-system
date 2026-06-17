"""Shared UI: sidebar, settings, formatting."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import streamlit as st

import iams_i18n as i18n
import iams_prefs as prefs


def prefs_css() -> str:
    compact = """
        section[data-testid="stMain"] .block-container { padding-top: 0.35rem !important; }
        section[data-testid="stMain"] [data-testid="stVerticalBlock"] { gap: 0.55rem !important; }
        div[data-testid="stMetric"] { padding: 0.35rem 0 !important; }
        div[data-testid="stMetricValue"] { font-size: 1.15rem !important; }
    """ if prefs.get_pref("compact_ui") else ""
    return f"<style>{compact}</style>"


def pnl_color_hex(positive: bool) -> str:
    scheme = prefs.get_pref("pnl_colors")
    if scheme == "western":
        return "#10b981" if positive else "#ef4444"
    return "#ef4444" if positive else "#10b981"


def format_pnl_html(pnl: float, pnl_pct: float, *, currency: str = "¥") -> str:
    if pnl > 0:
        c = pnl_color_hex(True)
        return (
            f"<span style='color:{c};font-size:28px;font-weight:bold;'>"
            f"+{pnl:,.2f} <span style='font-size:16px;'>(+{pnl_pct:.2f}%)</span></span>"
        )
    if pnl < 0:
        c = pnl_color_hex(False)
        return (
            f"<span style='color:{c};font-size:28px;font-weight:bold;'>"
            f"{pnl:,.2f} <span style='font-size:16px;'>({pnl_pct:.2f}%)</span></span>"
        )
    return (
        "<span style='color:gray;font-size:28px;font-weight:bold;'>"
        f"{currency}0.00 <span style='font-size:16px;'>(0.00%)</span></span>"
    )


def format_date(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value[:10]).date()
        except ValueError:
            return value
    elif hasattr(value, "date") and callable(value.date):
        value = value.date()
    fmt = prefs.get_pref("date_format")
    if fmt == "us":
        return value.strftime("%m/%d/%Y")
    if fmt == "cn":
        return f"{value.year}年{value.month}月{value.day}日"
    return value.strftime("%Y-%m-%d")


def render_sidebar_nav() -> None:
    nav_icon = "🧭 " if prefs.get_pref("show_emoji") else ""
    home_icon = "🏠 " if prefs.get_pref("show_emoji") else ""
    chart_icon = "📈 " if prefs.get_pref("show_emoji") else ""
    with st.sidebar:
        st.markdown(f"### {nav_icon}{i18n.t('nav.title')}")
        st.page_link("app.py", label=f"{home_icon}{i18n.t('nav.console')}")
        st.page_link("pages/analytics.py", label=f"{chart_icon}{i18n.t('nav.analytics')}")
        st.markdown("---")


def render_settings_panel(username: Optional[str], *, show_report_default: bool = True) -> None:
    gear = "⚙️ " if prefs.get_pref("show_emoji") else ""

    def _save_prefs() -> None:
        prefs.persist_session(username)

    with st.sidebar.expander(f"{gear}{i18n.t('settings.title')}", expanded=False):
        lang_opts = {"zh": i18n.t("settings.lang.zh"), "en": i18n.t("settings.lang.en")}
        st.selectbox(
            i18n.t("settings.lang"),
            list(lang_opts.keys()),
            format_func=lambda x: lang_opts[x],
            key=prefs.widget_key("lang"),
            on_change=_save_prefs,
        )

        pnl_opts = {"cn": i18n.t("settings.pnl_cn"), "western": i18n.t("settings.pnl_western")}
        st.selectbox(
            i18n.t("settings.pnl_colors"),
            list(pnl_opts.keys()),
            format_func=lambda x: pnl_opts[x],
            key=prefs.widget_key("pnl_colors"),
            on_change=_save_prefs,
        )

        date_opts = {"iso": i18n.t("settings.date_iso"), "us": i18n.t("settings.date_us"), "cn": i18n.t("settings.date_cn")}
        st.selectbox(
            i18n.t("settings.date_format"),
            list(date_opts.keys()),
            format_func=lambda x: date_opts[x],
            key=prefs.widget_key("date_format"),
            on_change=_save_prefs,
        )

        if show_report_default:
            view_opts = {
                "month": i18n.t("settings.view_month"),
                "quarter": i18n.t("settings.view_quarter"),
                "year": i18n.t("settings.view_year"),
            }
            st.selectbox(
                i18n.t("settings.default_view"),
                list(view_opts.keys()),
                format_func=lambda x: view_opts[x],
                key=prefs.widget_key("default_view"),
                on_change=_save_prefs,
            )

        st.checkbox(i18n.t("settings.compact"), key=prefs.widget_key("compact_ui"), on_change=_save_prefs)
        st.checkbox(i18n.t("settings.emoji"), key=prefs.widget_key("show_emoji"), on_change=_save_prefs)

    render_maintenance_panel(username)


def _run_refresh_pnl(username: Optional[str]) -> None:
    import portfolio_engine as pe

    if username:
        pe.invalidate_user_snapshots(username)
    st.cache_data.clear()
    st.success(i18n.t("settings.refresh_pnl_ok"))


def _run_clear_cache() -> None:
    st.cache_data.clear()
    st.success(i18n.t("settings.clear_cache_ok"))


def _run_reset_prefs(username: Optional[str]) -> None:
    prefs.reset_user_prefs(username)
    prefs.sync_session(username, force_load=True)
    st.cache_data.clear()
    st.success(i18n.t("settings.reset_ok"))


def _confirm_refresh_dialog(username: Optional[str]) -> None:
    @st.dialog(i18n.t("settings.confirm_title"))
    def _inner() -> None:
        st.warning(i18n.t("settings.confirm_refresh_msg"))
        c_yes, c_no = st.columns(2)
        if c_yes.button(i18n.t("settings.confirm_yes"), type="primary", use_container_width=True, key="dlg_refresh_yes"):
            _run_refresh_pnl(username)
            st.rerun()
        if c_no.button(i18n.t("settings.confirm_no"), use_container_width=True, key="dlg_refresh_no"):
            st.rerun()

    _inner()


def _confirm_clear_dialog() -> None:
    @st.dialog(i18n.t("settings.confirm_title"))
    def _inner() -> None:
        st.warning(i18n.t("settings.confirm_clear_msg"))
        c_yes, c_no = st.columns(2)
        if c_yes.button(i18n.t("settings.confirm_yes"), type="primary", use_container_width=True, key="dlg_clear_yes"):
            _run_clear_cache()
            st.rerun()
        if c_no.button(i18n.t("settings.confirm_no"), use_container_width=True, key="dlg_clear_no"):
            st.rerun()

    _inner()


def _confirm_reset_dialog(username: Optional[str]) -> None:
    @st.dialog(i18n.t("settings.confirm_title"))
    def _inner() -> None:
        st.warning(i18n.t("settings.confirm_reset_msg"))
        c_yes, c_no = st.columns(2)
        if c_yes.button(i18n.t("settings.confirm_yes"), type="primary", use_container_width=True, key="dlg_reset_yes"):
            _run_reset_prefs(username)
            st.rerun()
        if c_no.button(i18n.t("settings.confirm_no"), use_container_width=True, key="dlg_reset_no"):
            st.rerun()

    _inner()


def render_maintenance_panel(username: Optional[str]) -> None:
    """Advanced cache / prefs tools — tucked at the bottom of the sidebar."""
    st.sidebar.markdown(
        "<div style='margin-top:2rem;font-size:11px;color:#a8a29e;text-align:center;'>"
        f"{i18n.t('settings.advanced_fold')}</div>",
        unsafe_allow_html=True,
    )
    with st.sidebar.expander(i18n.t("settings.advanced_fold"), expanded=False):
        st.caption(i18n.t("settings.advanced_hint"))

        st.markdown(f"**{i18n.t('settings.refresh_pnl')}**")
        st.caption(i18n.t("settings.refresh_pnl_desc"))
        if st.button(i18n.t("settings.refresh_pnl"), use_container_width=True, key="settings_refresh_pnl"):
            _confirm_refresh_dialog(username)

        st.markdown(f"**{i18n.t('settings.clear_cache')}**")
        st.caption(i18n.t("settings.clear_cache_desc"))
        if st.button(i18n.t("settings.clear_cache"), use_container_width=True, key="settings_clear_cache"):
            _confirm_clear_dialog()

        st.markdown(f"**{i18n.t('settings.reset')}**")
        st.caption(i18n.t("settings.reset_desc"))
        if st.button(i18n.t("settings.reset"), use_container_width=True, key="settings_reset"):
            _confirm_reset_dialog(username)


def init_app_session(username: Optional[str] = None, *, query_params=None, force_load: bool = False) -> None:
    if query_params is not None:
        prefs.bootstrap_from_query(query_params)
    prefs.sync_session(username, force_load=force_load)
