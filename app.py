# 文件1：app.py (数据库版大厅 - 卡片式 UI 与盈亏透视)
import os
import streamlit as st
import pandas as pd
import db_manager as db
import portfolio_engine as pe
import iams_prefs as prefs
import iams_i18n as i18n
import iams_ui as ui
from datetime import datetime
import json

prefs.bootstrap_from_query(st.query_params)
_boot_lang = st.query_params.get("lang", "zh")
if _boot_lang not in ("zh", "en"):
    _boot_lang = "zh"

st.set_page_config(page_title=i18n.STRINGS["app.title"][_boot_lang], page_icon="🏦", layout="wide")

if st.query_params.get("clear_session") == "1":
    st.session_state.pop("trade_log", None)
    st.session_state.pop("current_loaded_acc", None)

db.init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "active_acc" not in st.session_state:
    st.session_state.active_acc = None
if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = None

if st.session_state.logged_in and st.session_state.current_user is None:
    st.session_state.logged_in = False

_prefs_user = st.session_state.current_user if st.session_state.logged_in else None
ui.init_app_session(_prefs_user, query_params=st.query_params)
st.markdown(ui.prefs_css(), unsafe_allow_html=True)

# 0. 检测：不仅检查文件是否存在，还要检查文件大小是否大于 0
file_path = "financial_data/中国平安.csv"

if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
    try:
        # 2. 尝试读取
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        # 3. 如果刚好撞上爬虫在清空重写，静默忽略，等下一秒自动刷新
        pass
    except Exception as e:
        # 拦截其他一切报错，避免红框弹到前台
        pass

# ==========================================
# 🧭 自定义侧边栏导航系统
# ==========================================
# 1. 使用 CSS 强制隐藏 Streamlit 默认的英文文件名导航
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none !important;}
        .stApp, [data-testid="stAppViewContainer"] {
            background: linear-gradient(180deg, #ffffff 0%, #fffaf8 100%) !important;
        }
        section[data-testid="stMain"] h1, section[data-testid="stMain"] h2,
        section[data-testid="stMain"] h3, section[data-testid="stMain"] h4,
        section[data-testid="stMain"] .stMarkdown p { color: #44403c !important; }
        section[data-testid="stMain"] .stMarkdown strong, section[data-testid="stMain"] .stMarkdown b {
            color: #1c1917 !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff !important;
            border: 1px solid #fde8e8 !important;
            border-radius: 16px !important;
            box-shadow: 0 2px 12px rgba(196, 30, 58, 0.06) !important;
        }
        /* ---- 登录页：柔和卡片 + 分段切换 ---- */
        .iams-auth-hero {
            text-align: center;
            padding: 0.25rem 0 1.25rem 0;
        }
        .iams-auth-hero__eyebrow {
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.12em;
            color: #a8a29e;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }
        .iams-auth-hero__title {
            font-size: 1.65rem;
            font-weight: 800;
            color: #991b1b;
            margin: 0;
            letter-spacing: -0.02em;
        }
        .iams-auth-hero__line {
            width: 36px;
            height: 3px;
            margin: 0.55rem auto 0;
            background: linear-gradient(90deg, #c9a227, #dc2626);
            border-radius: 2px;
        }
        /* 登录卡片内：身份登录 / 注册 平铺占满一行 */
        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stRadio"] {
            margin-bottom: 0.35rem;
            width: 100% !important;
        }
        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stRadio"] > div,
        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stRadio"] > div > div {
            width: 100% !important;
        }
        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stRadio"] div[role="radiogroup"] {
            display: flex !important;
            flex-direction: row !important;
            align-items: stretch !important;
            gap: 4px !important;
            width: 100% !important;
            box-sizing: border-box !important;
            background: #f5f5f4 !important;
            border: 1px solid #e7e5e4 !important;
            border-radius: 12px !important;
            padding: 4px !important;
        }
        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stRadio"] div[role="radiogroup"] > label {
            flex: 1 1 0 !important;
            width: 50% !important;
            min-width: 0 !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            background: transparent !important;
            border: none !important;
            border-radius: 9px !important;
            padding: 0.62rem 0.35rem !important;
            margin: 0 !important;
            cursor: pointer;
            transition: background 0.2s ease, box-shadow 0.2s ease, color 0.2s ease;
            min-height: 2.5rem !important;
            white-space: nowrap !important;
        }
        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
            display: none !important;
        }
        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stRadio"] div[role="radiogroup"] > label > div:last-child,
        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stRadio"] div[role="radiogroup"] > label p {
            flex: 1 1 auto !important;
            width: 100% !important;
            text-align: center !important;
            font-size: 0.92rem !important;
            font-weight: 500 !important;
            color: #78716c !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            line-height: 1.3 !important;
        }
        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
            background: #ffffff !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 2px 8px rgba(196, 30, 58, 0.07) !important;
        }
        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) > div:last-child,
        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) p {
            color: #991b1b !important;
            font-weight: 650 !important;
        }
        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stTextInput"] label p {
            font-size: 0.88rem !important;
            color: #57534e !important;
            font-weight: 500 !important;
        }
        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stTextInput"] input {
            border-radius: 10px !important;
            border: 1px solid #e7e5e4 !important;
            background: #fafaf9 !important;
            padding: 0.65rem 0.85rem !important;
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }
        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stTextInput"] input:focus {
            border-color: #f87171 !important;
            box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.08) !important;
        }
        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stFormSubmitButton"] button {
            margin-top: 0.35rem;
            border-radius: 10px !important;
            padding: 0.62rem 1rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.04em;
        }
        .iams-auth-topbar {
            height: 3px;
            margin: -1rem -1rem 1.1rem -1rem;
            background: linear-gradient(90deg, #c9a227 0%, #e8c547 45%, #dc2626 100%);
            border-radius: 16px 16px 0 0;
        }
        section[data-testid="stMain"] div[data-testid="stButton"] button[kind="primary"] {
            background: linear-gradient(135deg, #b91c1c 0%, #dc2626 100%) !important;
            border: 1px solid #c9a227 !important;
            color: #fff !important;
        }
        section[data-testid="stMain"] div[data-testid="stButton"] button[kind="primary"] p,
        section[data-testid="stMain"] div[data-testid="stButton"] button[kind="primary"] span {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }
        hr { border-color: #fde8e8 !important; }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #ffffff 0%, #fffaf8 100%) !important;
            border-right: 1px solid #fde8e8 !important;
        }
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] [data-testid="stExpander"] summary p,
        [data-testid="stSidebar"] [data-testid="stPageLink"] p { color: #44403c !important; }
        [data-testid="stSidebar"] [data-testid="stPageLink"] a { color: #b91c1c !important; }
        [data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] {
            background: #fef2f2 !important;
            border-left: 3px solid #c9a227 !important;
            border-radius: 8px;
        }
        [data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] a,
        [data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] p { color: #991b1b !important; }
        [data-testid="stSidebar"] hr { border-color: #fde8e8 !important; }
        [data-testid="stSidebar"] [data-testid="stExpander"] details {
            border: 1px solid #fde8e8 !important;
            background: #ffffff !important;
            border-radius: 8px;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] button,
        [data-testid="stSidebar"] [data-testid="stExpanderDetails"] [data-testid="stButton"] button {
            background: #ffffff !important;
            border: 1px solid #fecaca !important;
            color: #991b1b !important;
            border-radius: 8px !important;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
            background: linear-gradient(135deg, #b91c1c 0%, #dc2626 100%) !important;
            color: #ffffff !important;
            border: 1px solid #c9a227 !important;
        }
    </style>
""", unsafe_allow_html=True)

# 2. 侧边栏：导航（设置面板在登录态分支内渲染）
ui.render_sidebar_nav()

# ==========================================
# 0. 大厅盈亏：与看板共用 portfolio_engine（批量 + 磁盘缓存）
# ==========================================
@st.cache_data(ttl=300, show_spinner=False)
def _hall_snapshots(username: str, account_names: tuple, market_fp: str):
    return pe.batch_account_snapshots(username, list(account_names))

# ==========================================
# 1. 🛡️ 登录与注册拦截系统
# ==========================================
if not st.session_state.logged_in:
    ui.render_settings_panel(None, show_report_default=False)
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.35, 1])
    with col2:
        st.markdown(
            f"""
            <div class="iams-auth-hero">
                <div class="iams-auth-hero__eyebrow">{i18n.t('auth.eyebrow')}</div>
                <h2 class="iams-auth-hero__title">{i18n.t('auth.welcome')}</h2>
                <div class="iams-auth-hero__line"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.markdown('<div class="iams-auth-topbar"></div>', unsafe_allow_html=True)
            auth_mode = st.radio(
                "auth_mode",
                options=["login", "register"],
                format_func=lambda x: i18n.t("auth.login_tab") if x == "login" else i18n.t("auth.register_tab"),
                horizontal=True,
                label_visibility="collapsed",
                key="auth_mode",
            )
            if auth_mode == "login":
                with st.form("login_form"):
                    log_user = st.text_input(i18n.t("auth.username"), placeholder=i18n.t("auth.username_ph"))
                    log_pwd = st.text_input(i18n.t("auth.password"), type="password", placeholder=i18n.t("auth.password_ph"))
                    if st.form_submit_button(i18n.t("auth.login_btn"), use_container_width=True):
                        if db.verify_user(log_user, log_pwd):
                            st.session_state.logged_in = True
                            st.session_state.current_user = log_user
                            prefs.on_user_login(log_user)
                            st.success(i18n.t("auth.login_ok", user=log_user))
                            st.rerun()
                        else:
                            st.error(i18n.t("auth.login_fail"))
            else:
                with st.form("register_form"):
                    reg_user = st.text_input(i18n.t("auth.username"), placeholder=i18n.t("auth.username_set_ph"))
                    reg_pwd = st.text_input(i18n.t("auth.password"), type="password", placeholder=i18n.t("auth.password_set_ph"))
                    reg_pwd2 = st.text_input(i18n.t("auth.confirm_password"), type="password", placeholder=i18n.t("auth.confirm_ph"))
                    if st.form_submit_button(i18n.t("auth.register_btn"), use_container_width=True):
                        if reg_user == "" or reg_pwd == "":
                            st.warning(i18n.t("auth.empty_fields"))
                        elif reg_pwd != reg_pwd2:
                            st.error(i18n.t("auth.pwd_mismatch"))
                        else:
                            success, msg = db.register_user(reg_user, reg_pwd)
                            if success:
                                st.success(i18n.t("auth.register_ok"))
                            else:
                                st.error(i18n.map_register_msg(msg))
    st.stop()

# ==========================================
# 2. 已登录状态：账号大厅与个人中心
# ==========================================
current_user = st.session_state.current_user

user_icon = "👤 " if prefs.get_pref("show_emoji") else ""
st.sidebar.markdown(f"### {user_icon}{i18n.t('auth.current_user')}：{current_user}")
with st.sidebar.expander(i18n.e("auth.change_pwd", "⚙️ ")):
    old_pwd = st.text_input(i18n.t("auth.old_pwd"), type="password")
    new_pwd = st.text_input(i18n.t("auth.new_pwd"), type="password")
    if st.button(i18n.t("auth.change_pwd"), type="secondary", use_container_width=True):
        if db.update_password(current_user, old_pwd, new_pwd):
            st.success(i18n.t("auth.change_ok"))
        else:
            st.error(i18n.t("auth.change_fail"))

ui.render_settings_panel(current_user, show_report_default=True)

if st.sidebar.button(i18n.e("auth.logout", "🚪 "), type="secondary", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.delete_confirm = None
    st.rerun()

st.title(i18n.e("hall.title", "🏦 "))
st.markdown("---")

col_list, col_add = st.columns([2.5, 1], gap="large")

with col_list:
    st.subheader(i18n.e("hall.accounts", "📁 "))
    accounts = db.get_user_accounts(current_user)
    
    if not accounts:
        st.info(i18n.t("hall.no_accounts"))
    else:
        acc_names = tuple(a["name"] for a in accounts)
        market_fp = pe.compute_market_fingerprint()
        snapshots = _hall_snapshots(current_user, acc_names, market_fp)

        for acc in accounts:
            acc_name = acc['name']
            
            # 💡 状态一：删除确认模式
            if st.session_state.delete_confirm == acc_name:
                with st.container(border=True):
                    st.warning(i18n.t("hall.delete_confirm", name=acc_name))
                    c_yes, c_no = st.columns(2)
                    if c_yes.button(i18n.e("hall.delete_yes", "🚨 "), key=f"yes_{acc_name}", type="primary", use_container_width=True):
                        db.delete_account(current_user, acc_name)
                        st.session_state.delete_confirm = None
                        st.rerun()
                    if c_no.button(i18n.t("hall.delete_no"), key=f"no_{acc_name}", use_container_width=True):
                        st.session_state.delete_confirm = None
                        st.rerun()
                continue

            # 💡 状态二：正常展示模式（卡片化UI设计）
            snap = snapshots.get(acc_name)
            if snap:
                invested, pnl, pnl_pct = snap.as_tuple()
            else:
                invested, pnl, pnl_pct = 0.0, 0.0, 0.0
            
            with st.container(border=True): # 使用边框容器打包整个账户信息
                # 按照 3:1 比例划分左侧数据区和右侧按钮区
                c_info, c_action = st.columns([3, 1])
                
                with c_info:
                    acc_icon = "💼 " if prefs.get_pref("show_emoji") else ""
                    st.markdown(f"#### {acc_icon}{acc_name}")
                    st.markdown(ui.format_pnl_html(pnl, pnl_pct), unsafe_allow_html=True)
                    clock = "🕒 " if prefs.get_pref("show_emoji") else ""
                    st.caption(f"{clock}{i18n.t('hall.last_access')}: {acc['last_accessed']}")
                
                with c_action:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button(i18n.t("hall.enter") + " ➔", key=f"go_{acc_name}", type="primary", use_container_width=True):
                        db.update_account_access(current_user, acc_name) 
                        st.session_state.active_acc = acc_name
                        st.switch_page("pages/analytics.py")
                        
                    if st.button(i18n.e("hall.delete", "🗑️ "), key=f"del_{acc_name}", use_container_width=True):
                        st.session_state.delete_confirm = acc_name
                        st.rerun()

with col_add:
    st.subheader(i18n.e("hall.create_title", "➕ "))
    with st.container(border=True):
        new_acc = st.text_input(i18n.t("hall.create_ph"), key="new_acc_input")
        if st.button(i18n.t("hall.create_btn"), use_container_width=True):
            clean_acc_name = new_acc.strip()
            if clean_acc_name == "":
                st.warning(i18n.t("hall.create_empty"))
            else:
                if db.create_account(current_user, clean_acc_name):
                    st.session_state.active_acc = clean_acc_name
                    st.switch_page("pages/analytics.py")
                else:
                    st.warning(i18n.t("hall.create_exists"))