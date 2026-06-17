"""Bilingual UI strings (zh / en)."""
from __future__ import annotations

from typing import Any, Optional

STRINGS: dict[str, dict[str, str]] = {
    # ---- App meta ----
    "app.title": {"zh": "账号管理门户", "en": "Account Portal"},
    "analytics.title": {"zh": "数据看板", "en": "Analytics Dashboard"},
    # ---- Nav ----
    "nav.title": {"zh": "系统导航", "en": "Navigation"},
    "nav.console": {"zh": "系统控制台", "en": "Console"},
    "nav.analytics": {"zh": "投资分析看板", "en": "Analytics"},
    # ---- Settings ----
    "settings.title": {"zh": "系统设置", "en": "Settings"},
    "settings.lang": {"zh": "界面语言", "en": "Language"},
    "settings.lang.zh": {"zh": "中文", "en": "Chinese"},
    "settings.lang.en": {"zh": "English", "en": "English"},
    "settings.pnl_colors": {"zh": "涨跌配色", "en": "P/L colors"},
    "settings.pnl_cn": {"zh": "A股习惯 (红涨绿跌)", "en": "CN (red up / green down)"},
    "settings.pnl_western": {"zh": "国际习惯 (绿涨红跌)", "en": "Western (green up / red down)"},
    "settings.date_format": {"zh": "日期格式", "en": "Date format"},
    "settings.date_iso": {"zh": "YYYY-MM-DD", "en": "YYYY-MM-DD"},
    "settings.date_us": {"zh": "MM/DD/YYYY", "en": "MM/DD/YYYY"},
    "settings.date_cn": {"zh": "YYYY年M月D日", "en": "YYYY年M月D日"},
    "settings.default_view": {"zh": "默认报告视角", "en": "Default report view"},
    "settings.view_month": {"zh": "月报", "en": "Monthly"},
    "settings.view_quarter": {"zh": "季报", "en": "Quarterly"},
    "settings.view_year": {"zh": "年报", "en": "Yearly"},
    "settings.compact": {"zh": "紧凑布局", "en": "Compact layout"},
    "settings.emoji": {"zh": "显示界面 Emoji", "en": "Show emoji in UI"},
    "settings.refresh_pnl": {"zh": "刷新盈亏缓存", "en": "Refresh P/L cache"},
    "settings.refresh_pnl_ok": {"zh": "盈亏缓存已刷新", "en": "P/L cache refreshed"},
    "settings.clear_cache": {"zh": "清空数据缓存", "en": "Clear data cache"},
    "settings.clear_cache_ok": {"zh": "Streamlit 数据缓存已清空", "en": "Streamlit data cache cleared"},
    "settings.reset": {"zh": "恢复默认设置", "en": "Reset to defaults"},
    "settings.reset_ok": {"zh": "已恢复默认设置", "en": "Settings reset to defaults"},
    "settings.advanced_fold": {"zh": "· 系统维护 ·", "en": "· maintenance ·"},
    "settings.advanced_hint": {"zh": "以下操作会影响缓存与本地偏好，请谨慎使用。", "en": "These actions affect caches and saved preferences. Use with care."},
    "settings.refresh_pnl_desc": {"zh": "强制重新计算大厅卡片盈亏（清除磁盘快照 + 内存缓存）。", "en": "Force hall P/L cards to recalculate (disk snapshots + memory cache)."},
    "settings.clear_cache_desc": {"zh": "清空 Streamlit 行情/计算内存缓存，下次访问会重新加载数据。", "en": "Clear Streamlit in-memory market/calc cache; data reloads on next visit."},
    "settings.reset_desc": {"zh": "将语言、配色、日期格式等恢复为系统默认值。", "en": "Restore language, colors, date format, etc. to system defaults."},
    "settings.confirm_title": {"zh": "请确认操作", "en": "Confirm action"},
    "settings.confirm_yes": {"zh": "确认执行", "en": "Confirm"},
    "settings.confirm_no": {"zh": "取消", "en": "Cancel"},
    "settings.confirm_refresh_msg": {"zh": "将清除当前用户的盈亏快照与计算缓存，并立即按最新数据重算。确定继续？", "en": "This clears your P/L snapshots and recalculates from latest data. Continue?"},
    "settings.confirm_clear_msg": {"zh": "将清空所有 Streamlit 数据缓存，可能导致页面短暂变慢。确定继续？", "en": "This clears all Streamlit data caches. The app may be slower briefly. Continue?"},
    "settings.confirm_reset_msg": {"zh": "将恢复全部界面设置为默认值，且无法撤销。确定继续？", "en": "This resets all UI settings to defaults and cannot be undone. Continue?"},
    "settings.saved": {"zh": "设置已保存", "en": "Settings saved"},
    # ---- Auth ----
    "auth.eyebrow": {"zh": "IAMS · 投资账户管理", "en": "IAMS · Investment Accounts"},
    "auth.welcome": {"zh": "欢迎回来", "en": "Welcome back"},
    "auth.login_tab": {"zh": "身份登录", "en": "Sign in"},
    "auth.register_tab": {"zh": "新用户注册", "en": "Register"},
    "auth.username": {"zh": "用户名", "en": "Username"},
    "auth.password": {"zh": "密码", "en": "Password"},
    "auth.confirm_password": {"zh": "确认密码", "en": "Confirm password"},
    "auth.username_ph": {"zh": "请输入用户名", "en": "Enter username"},
    "auth.password_ph": {"zh": "请输入密码", "en": "Enter password"},
    "auth.username_set_ph": {"zh": "设置您的用户名", "en": "Choose a username"},
    "auth.password_set_ph": {"zh": "设置登录密码", "en": "Choose a password"},
    "auth.confirm_ph": {"zh": "再次输入密码", "en": "Re-enter password"},
    "auth.login_btn": {"zh": "登 录", "en": "Sign in"},
    "auth.register_btn": {"zh": "注 册", "en": "Register"},
    "auth.login_ok": {"zh": "欢迎回来，{user}！正在进入系统…", "en": "Welcome back, {user}! Loading…"},
    "auth.login_fail": {"zh": "用户名或密码错误", "en": "Invalid username or password"},
    "auth.empty_fields": {"zh": "用户名和密码不能为空", "en": "Username and password are required"},
    "auth.pwd_mismatch": {"zh": "两次密码不一致", "en": "Passwords do not match"},
    "auth.register_ok": {"zh": "注册成功，请切换到登录", "en": "Registered. Please sign in."},
    "auth.register_exists": {"zh": "用户名已存在", "en": "Username already exists"},
    "auth.change_pwd": {"zh": "修改密码", "en": "Change password"},
    "auth.old_pwd": {"zh": "原密码", "en": "Current password"},
    "auth.new_pwd": {"zh": "新密码", "en": "New password"},
    "auth.change_ok": {"zh": "修改成功", "en": "Password updated"},
    "auth.change_fail": {"zh": "原密码错误", "en": "Current password is incorrect"},
    "auth.logout": {"zh": "退出安全登录", "en": "Sign out"},
    "auth.current_user": {"zh": "当前用户", "en": "Signed in as"},
    # ---- Hall ----
    "hall.title": {"zh": "我的财富管理门户", "en": "Wealth Management Portal"},
    "hall.accounts": {"zh": "我的专属投资账号", "en": "My Investment Accounts"},
    "hall.no_accounts": {"zh": "您还没有创建任何投资账号，请在右侧创建一个。", "en": "No accounts yet. Create one on the right."},
    "hall.last_access": {"zh": "最近访问", "en": "Last accessed"},
    "hall.enter": {"zh": "进入看板", "en": "Open dashboard"},
    "hall.delete": {"zh": "删除账户", "en": "Delete account"},
    "hall.delete_confirm": {"zh": "确定要永久删除账户 **【{name}】** 及其所有流水吗？此操作不可恢复！", "en": "Permanently delete **{name}** and all transactions? This cannot be undone."},
    "hall.delete_yes": {"zh": "确认删除", "en": "Delete"},
    "hall.delete_no": {"zh": "取消", "en": "Cancel"},
    "hall.create_title": {"zh": "创建新账号", "en": "Create account"},
    "hall.create_ph": {"zh": "请输入账号名称", "en": "Account name"},
    "hall.create_btn": {"zh": "创建并直接进入", "en": "Create & open"},
    "hall.create_empty": {"zh": "账号名称不能为空", "en": "Account name is required"},
    "hall.create_exists": {"zh": "该账号名称已存在", "en": "Account name already exists"},
    # ---- Admin topbar ----
    "admin.sub": {"zh": "Investment Advisor Console", "en": "Investment Advisor Console"},
    "admin.title": {"zh": "投顾控制台 · {acc}", "en": "Advisor Console · {acc}"},
    "admin.owner": {"zh": "所属用户 · {user}", "en": "Owner · {user}"},
    "admin.back": {"zh": "返回大厅", "en": "Back to portal"},
    # ---- Client topbar ----
    "client.sub": {"zh": "Investment Performance Report · {acc}", "en": "Investment Performance Report · {acc}"},
    "client.title": {"zh": "客户汇报与展示大屏", "en": "Client Performance Report"},
    "client.export_pdf": {"zh": "导出 PDF", "en": "Export PDF"},
    # ---- Admin sidebar ----
    "admin.zone": {"zh": "内部管理员专区", "en": "Admin zone"},
    "admin.start_date_help": {"zh": "设定账户的**物理开户日**。系统将仅统计该日期及之后的资金和交易。", "en": "Set the **account start date**. Only activity on/after this date is included."},
    "admin.start_date": {"zh": "账户开户日 (基点)", "en": "Account start date"},
    "admin.add_stock": {"zh": "动态添加新股票标的", "en": "Add stock symbol"},
    "admin.stock_ph": {"zh": "股票简称 (如: 招商银行)", "en": "Stock name (e.g. CMB)"},
    "admin.stock_fetch": {"zh": "联网抓取并入库", "en": "Fetch & import"},
    "admin.stock_force": {"zh": "已存在时强制重新抓取", "en": "Force re-fetch if exists"},
    # ---- Admin console ----
    "admin.console": {"zh": "内部管理与操作台 (含持仓底牌)", "en": "Admin console (with holdings)"},
    "admin.trade_entry": {"zh": "交易录入台", "en": "Trade entry"},
    "admin.trade_date": {"zh": "操作日期", "en": "Date"},
    "admin.trade_type": {"zh": "操作类型", "en": "Type"},
    "admin.trade_asset": {"zh": "标的", "en": "Symbol"},
    "admin.trade_qty": {"zh": "数量(股)", "en": "Quantity"},
    "admin.trade_price": {"zh": "成交单价(¥)", "en": "Price (¥)"},
    "admin.trade_total": {"zh": "实际结算总金额(¥)", "en": "Total (¥)"},
    "admin.trade_submit": {"zh": "确认并录入指令", "en": "Submit trade"},
    "admin.trade_total_err": {"zh": "录入失败：结算总额必须大于 0", "en": "Total must be greater than 0"},
    "admin.holdings": {"zh": "持仓结构 (截至 **{date}**)", "en": "Holdings (as of **{date}**)"},
    "admin.cash_avail": {"zh": "可用现金", "en": "Available cash"},
    "admin.radar": {"zh": "账户实时监控雷达", "en": "Account radar"},
    "admin.radar_asof": {"zh": "截至全量最新：**{date}** 收盘", "en": "As of latest close: **{date}**"},
    "admin.metric_cash": {"zh": "可用现金储备", "en": "Cash reserve"},
    "admin.metric_fees": {"zh": "累计交易损耗 (含税费)", "en": "Cumulative friction & fees"},
    "admin.metric_principal": {"zh": "累计净本金", "en": "Net principal"},
    "admin.ledger": {"zh": "内部历史指令账本 (管理员维护区)", "en": "Transaction ledger (admin)"},
    "admin.ledger_save": {"zh": "保存账本", "en": "Save ledger"},
    "admin.ledger_unsaved": {"zh": "账本有未保存修改，请点击「保存账本」。", "en": "Unsaved changes — click Save ledger."},
    # ---- Transaction types (display only; DB stays Chinese) ----
    "tx.deposit": {"zh": "转入本金", "en": "Capital in"},
    "tx.buy": {"zh": "买入股票", "en": "Buy"},
    "tx.sell": {"zh": "卖出股票", "en": "Sell"},
    "tx.withdraw": {"zh": "提取现金", "en": "Withdraw"},
    "tx.fee_in": {"zh": "提取管理费(内扣)", "en": "Mgmt fee (internal)"},
    "tx.fee_out": {"zh": "结账重置(外付)", "en": "Settlement (external)"},
    # ---- Client metrics ----
    "metrics.section": {"zh": "核心指标与业绩分析曲线", "en": "Performance Metrics & Analytics"},
    "metrics.section_sub": {"zh": "PERFORMANCE METRICS & ANALYTICS", "en": "PERFORMANCE METRICS & ANALYTICS"},
    "metrics.pick_dim": {"zh": "请选择业绩分析维度", "en": "Select reporting period"},
    "view.monthly": {"zh": "月度报告 (上月: {month}月)", "en": "Monthly (prev: {month})"},
    "view.quarterly": {"zh": "季度报告 (上季: Q{q})", "en": "Quarterly (prev: Q{q})"},
    "view.yearly": {"zh": "年度报告 (去年: {year}年)", "en": "Annual ({year})"},
    "view.custom": {"zh": "自定义区间", "en": "Custom range"},
    "metrics.custom_range": {"zh": "请选择自定义展示区间", "en": "Custom date range"},
    "metrics.startup": {"zh": "账户处于起步期（已运行 {days} 天），暂无完整月度报表。", "en": "Account is in startup period ({days} days); no full monthly report yet."},
    "metrics.no_data": {"zh": "该区间内可用的底层行情数据不足，无法生成有效测算曲线。", "en": "Insufficient market data in this range to build curves."},
    "metrics.date_range": {"zh": "实际有效数据区间：**{start}** 至 **{end}**", "en": "Effective range: **{start}** to **{end}**"},
    "metrics.period_inflow": {"zh": "该区间净充值/流入本金", "en": "Net capital inflow (period)"},
    "metrics.period_inflow_note": {"zh": "（仅本区间内的注资−提取；≠ 累计净本金）", "en": "(Deposits − withdrawals in period only)"},
    "metrics.principal_line": {"zh": "截至 **{date}** 累计净本金 **¥{principal:,.2f}** = 注资 **¥{inflow:,.2f}** − 提取 **¥{outflow:,.2f}** （自开户日 {start} 起）", "en": "Net principal as of **{date}**: **¥{principal:,.2f}** = in **¥{inflow:,.2f}** − out **¥{outflow:,.2f}** (since {start})"},
    "metrics.principal_warn": {"zh": "累计净本金与账本核对相差 ¥{diff:,.2f}。请检查开户日 ({start}) 之前的流水。", "en": "Net principal differs from ledger by ¥{diff:,.2f}. Check trades before start date ({start})."},
    "kpi.period_return": {"zh": "区间回报", "en": "Period return"},
    "kpi.period_return_help": {"zh": "区间回报 = (期末资产 - 期初资产 - 期间净转入) / 成本基数", "en": "Period return = (end − start − net inflow) / cost base"},
    "kpi.benchmark": {"zh": "{name} 同期表现", "en": "{name} (benchmark)"},
    "kpi.benchmark_help": {"zh": "同一时间区间内基准指数的累计涨跌幅", "en": "Benchmark cumulative change over the same period"},
    "kpi.benchmark_delta": {"zh": "基准涨跌", "en": "benchmark move"},
    "kpi.alpha": {"zh": "区间超额收益", "en": "Excess return"},
    "kpi.alpha_help": {"zh": "账户区间回报率减去大盘基准涨跌幅", "en": "Portfolio return minus benchmark return"},
    "kpi.vs_benchmark": {"zh": "相较大盘", "en": "vs benchmark"},
    "kpi.total_asset": {"zh": "期末真实总资产", "en": "Ending total assets"},
    "kpi.total_asset_help": {"zh": "该区间最后一日的账户总资产估值（现金 + 持仓市值）", "en": "Cash + holdings at period end"},
    "kpi.max_dd": {"zh": "区间最大回撤", "en": "Max drawdown"},
    "kpi.max_dd_help": {"zh": "区间内净值从最高点回落的最大跌幅", "en": "Largest peak-to-trough decline in the period"},
    "kpi.max_dd_delta": {"zh": "极值跌幅", "en": "peak decline"},
    "kpi.sharpe": {"zh": "夏普比率 (Sharpe)", "en": "Sharpe ratio"},
    "kpi.sharpe_help": {"zh": "经风险调整后的回报效率，通常 >1 算优秀", "en": "Risk-adjusted return efficiency; >1 is often considered good"},
    "chart.tab_return": {"zh": "累计收益率走势图 (区间动态汇报)", "en": "Cumulative return"},
    "chart.tab_asset": {"zh": "真实资产走势图 (含净本金成本线)", "en": "Total assets vs cost"},
    "chart.benchmark": {"zh": "上证指数 (大盘基准)", "en": "SSE Index (benchmark)"},
    "chart.portfolio": {"zh": "本投资组合", "en": "Portfolio"},
    "chart.total_assets": {"zh": "真实总资产", "en": "Total assets"},
    "chart.net_principal": {"zh": "累计净本金 (成本线)", "en": "Net principal (cost)"},
    "chart.breakeven": {"zh": "盈亏平衡线 (0%)", "en": "Breakeven (0%)"},
    "share.title": {"zh": "获取发送给客户的专属汇报链接", "en": "Client report share link"},
    "share.hint": {"zh": "请选择客户打开链接时默认看到的报告维度，然后复制下方完整链接。", "en": "Choose default report view for the client link, then copy the URL below."},
    "share.view_pick": {"zh": "设置链接的默认视角", "en": "Default view in link"},
    "share.view_month": {"zh": "月报视图", "en": "Monthly"},
    "share.view_quarter": {"zh": "季报视图", "en": "Quarterly"},
    "share.view_year": {"zh": "年报视图", "en": "Yearly"},
    "share.test_link": {"zh": "点击这里，模拟客户在公网直接打开", "en": "Open as client (preview)"},
    "commentary.title": {"zh": "投顾分析与决策展望 ({period})", "en": "Advisor commentary ({period})"},
    "commentary.empty": {"zh": "本报告期暂无投顾寄语。", "en": "No commentary for this period."},
    # ---- Errors ----
    "err.no_data_dir": {"zh": "找不到 '{dir}' 文件夹", "en": "Missing folder: '{dir}'"},
    "err.no_stocks": {"zh": "个股数据文件夹为空", "en": "Stock data folder is empty"},
    "err.no_dates": {"zh": "选定日期之后没有可用的行情数据", "en": "No market data after the selected start date"},
}

TX_DB_TO_KEY = {
    "转入本金": "tx.deposit",
    "买入股票": "tx.buy",
    "卖出股票": "tx.sell",
    "提取现金": "tx.withdraw",
    "提取管理费(内扣)": "tx.fee_in",
    "结账重置(外付)": "tx.fee_out",
}

TX_KEY_TO_DB = {v: k for k, v in TX_DB_TO_KEY.items()}

TRADE_ENTRY_TYPES = ["转入本金", "买入股票", "卖出股票", "提取现金"]


def lang() -> str:
    import iams_prefs as prefs

    return prefs.get_pref("lang")


def t(key: str, **kwargs: Any) -> str:
    entry = STRINGS.get(key, {})
    text = entry.get(lang(), entry.get("zh", key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def e(key: str, emoji: str = "") -> str:
    """Optional emoji prefix based on user pref."""
    import iams_prefs as prefs

    prefix = emoji if prefs.get_pref("show_emoji") and emoji else ""
    return f"{prefix}{t(key)}".strip()


def tx_label(db_value: str) -> str:
    ikey = TX_DB_TO_KEY.get(db_value)
    return t(ikey) if ikey else db_value


def tx_entry_options() -> list[str]:
    return list(TRADE_ENTRY_TYPES)


def tx_entry_labels() -> dict[str, str]:
    return {db: tx_label(db) for db in TRADE_ENTRY_TYPES}


def map_register_msg(msg: str) -> str:
    if msg == "注册成功":
        return t("auth.register_ok")
    if msg == "用户名已存在":
        return t("auth.register_exists")
    return msg
