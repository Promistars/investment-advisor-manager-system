import calendar
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db_manager as db
import portfolio_engine as pe

BENCHMARK = pe.BENCHMARK_NAME
ViewMode = Literal["monthly", "quarterly", "yearly", "custom"]


def _df_records(df: pd.DataFrame, cols: list[str]) -> list[dict[str, Any]]:
    if df.empty:
        return []
    out = df[cols].copy()
    if "日期" in out.columns:
        out["日期"] = pd.to_datetime(out["日期"]).dt.strftime("%Y-%m-%d")
    return out.replace({np.nan: None}).to_dict(orient="records")


def _period_bounds(view: ViewMode, account_start: date, global_max: date, *, client_mode: bool) -> tuple[date, date, date]:
    today = datetime.now().date()
    first_day_prev_month = datetime(today.year, today.month - 1 if today.month > 1 else 12, 1).date()
    if today.month == 1:
        first_day_prev_month = datetime(today.year - 1, 12, 1).date()
    last_day_prev_month = datetime(
        first_day_prev_month.year,
        first_day_prev_month.month,
        calendar.monthrange(first_day_prev_month.year, first_day_prev_month.month)[1],
    ).date()

    current_quarter = (today.month - 1) // 3 + 1
    prev_quarter = current_quarter - 1
    prev_q_year = today.year if prev_quarter > 0 else today.year - 1
    prev_quarter = prev_quarter if prev_quarter > 0 else 4
    first_day_prev_q = datetime(prev_q_year, 3 * prev_quarter - 2, 1).date()
    last_day_prev_q = datetime(
        prev_q_year, 3 * prev_quarter, calendar.monthrange(prev_q_year, 3 * prev_quarter)[1]
    ).date()

    first_day_prev_year = datetime(today.year - 1, 1, 1).date()
    last_day_prev_year = datetime(today.year - 1, 12, 31).date()

    client_max = min(global_max, last_day_prev_month)
    max_selectable = client_max if client_mode else global_max

    if view == "monthly":
        start, end = first_day_prev_month, last_day_prev_month
    elif view == "quarterly":
        start, end = first_day_prev_q, last_day_prev_q
    elif view == "yearly":
        start, end = first_day_prev_year, last_day_prev_year
    else:
        start, end = account_start, max_selectable

    if end > max_selectable:
        end = max_selectable
        start = min(start, end)
    return start, end, max_selectable


def available_views(account_start: date) -> list[str]:
    today = datetime.now().date()
    lifespan = (today - account_start).days
    keys: list[str] = []
    if lifespan >= 30:
        keys.append("monthly")
    if lifespan >= 90:
        keys.append("quarterly")
    if lifespan >= 365:
        keys.append("yearly")
        keys.append("custom")
    return keys


def report_name_for_view(view: ViewMode) -> str:
    today = datetime.now().date()
    first_day_prev_month = datetime(today.year, today.month - 1 if today.month > 1 else 12, 1).date()
    if today.month == 1:
        first_day_prev_month = datetime(today.year - 1, 12, 1).date()
    current_quarter = (today.month - 1) // 3 + 1
    prev_quarter = current_quarter - 1
    prev_q_year = today.year if prev_quarter > 0 else today.year - 1
    prev_quarter = prev_quarter if prev_quarter > 0 else 4

    if view == "monthly":
        return f"{first_day_prev_month.strftime('%Y年%m月')}-月报"
    if view == "quarterly":
        return f"{prev_q_year}年Q{prev_quarter}-季报"
    if view == "yearly":
        return f"{today.year - 1}年-年报"
    return ""


def build_admin_df(username: str, account: str) -> tuple[pd.DataFrame, date, date, list[str]]:
    if not os.path.isdir(pe.DATA_DIR):
        raise FileNotFoundError(f"Missing data dir: {pe.DATA_DIR}")
    if not os.path.isdir(pe.INDEX_DIR):
        raise FileNotFoundError(f"Missing index dir: {pe.INDEX_DIR}")

    fp = pe.compute_market_fingerprint()
    ctx = pe.get_market_context(fp)
    trades = db.get_trades(username, account)
    start = pe.get_acc_start_date(username, account, ctx.global_min_date)
    admin_df = pe.run_simulation(
        ctx.portfolio_df,
        ctx.stock_names,
        ctx.dividend_book,
        start,
        trades,
    )
    if admin_df.empty:
        raise ValueError("No simulation data")
    admin_df = pe.enrich_admin_metrics(admin_df, BENCHMARK)
    return admin_df, start, ctx.global_max_date, ctx.stock_names


def compute_dashboard(
    username: str,
    account: str,
    *,
    view: ViewMode = "monthly",
    client_mode: bool = False,
    custom_start: date | None = None,
    custom_end: date | None = None,
    include_admin: bool = False,
) -> dict[str, Any]:
    admin_df, account_start, global_max, stock_names = build_admin_df(username, account)
    trades = db.get_trades(username, account)

    if view == "custom" and custom_start and custom_end:
        perf_start, perf_end = custom_start, custom_end
        _, _, max_selectable = _period_bounds("monthly", account_start, global_max, client_mode=client_mode)
        if perf_end > max_selectable:
            perf_end = max_selectable
        perf_start = min(perf_start, perf_end)
    else:
        perf_start, perf_end, max_selectable = _period_bounds(view, account_start, global_max, client_mode=client_mode)

    client_df = admin_df[(admin_df["日期"].dt.date >= perf_start) & (admin_df["日期"].dt.date <= perf_end)].copy()
    if len(client_df) < 2:
        return {
            "ok": False,
            "message": "insufficient_data",
            "available_views": available_views(account_start),
            "account_start": account_start.isoformat(),
            "global_max_date": global_max.isoformat(),
            "max_selectable_date": max_selectable.isoformat(),
        }

    c_first = client_df.iloc[0]
    c_latest = client_df.iloc[-1]
    client_start_idx = client_df.index[0]
    bench_col = f"{BENCHMARK}收盘价"

    if client_start_idx == 0:
        prev_asset, prev_principal, prev_index = 0.0, 0.0, float(admin_df[bench_col].iloc[0])
    else:
        prev_asset = float(admin_df.loc[client_start_idx - 1, "总持仓市值"])
        prev_principal = float(admin_df.loc[client_start_idx - 1, "累计净本金"])
        prev_index = float(admin_df.loc[client_start_idx - 1, bench_col])

    period_net_inflow = float(c_latest["累计净本金"] - prev_principal)
    period_pnl = float(c_latest["总持仓市值"] - prev_asset - period_net_inflow)
    period_cost_base = prev_asset + max(0, period_net_inflow)
    if period_cost_base <= 0:
        period_cost_base = max(float(client_df["累计净本金"].max()), 1.0)

    portfolio_change = (period_pnl / period_cost_base) * 100
    index_change = (float(c_latest[bench_col]) / prev_index - 1.0) * 100
    alpha = portfolio_change - index_change

    as_of_date = pd.Timestamp(c_latest["日期"]).date()
    engine_principal = pe.net_principal_on_date(admin_df, as_of_date)
    ledger_net, ledger_in, ledger_out = pe.ledger_net_principal(trades, account_start, as_of_date)

    client_df = client_df.copy()
    client_df["历史最高净值"] = client_df["精确组合净值"].cummax()
    client_df["回撤幅度"] = (client_df["精确组合净值"] - client_df["历史最高净值"]) / client_df["历史最高净值"]
    max_drawdown = float(client_df["回撤幅度"].min() * 100)

    delta_days = max(1, (c_latest["日期"] - c_first["日期"]).days)
    daily_returns = client_df["账户当日收益率"] / 100.0
    daily_volatility = float(daily_returns.std())
    daily_rf = 0.02 / 252
    excess_returns = daily_returns - daily_rf
    sharpe_ratio = (
        float((excess_returns.mean() / daily_volatility) * np.sqrt(252)) if daily_volatility > 0 else 0.0
    )

    client_df["区间内累计净流入"] = client_df["累计净本金"] - prev_principal
    client_df["区间内累计净盈亏"] = client_df["总持仓市值"] - prev_asset - client_df["区间内累计净流入"]
    client_df["区间成本基数"] = prev_asset + client_df["区间内累计净流入"].clip(lower=0)
    client_df["账户累计收益率"] = np.where(
        client_df["区间成本基数"] > 0,
        (client_df["区间内累计净盈亏"] / client_df["区间成本基数"]) * 100,
        0.0,
    )
    client_df["大盘累计收益率"] = (client_df[bench_col] / prev_index - 1.0) * 100

    chart_cols = ["日期", "账户累计收益率", "大盘累计收益率", "总持仓市值", "累计净本金"]
    charts = _df_records(client_df, chart_cols)

    rep_name = report_name_for_view(view)
    commentary = db.get_commentary(username, account, rep_name) if rep_name else ""

    latest = admin_df.iloc[-1]
    result: dict[str, Any] = {
        "ok": True,
        "benchmark": BENCHMARK,
        "account": account,
        "username": username,
        "view": view,
        "client_mode": client_mode,
        "available_views": available_views(account_start),
        "account_start": account_start.isoformat(),
        "global_max_date": global_max.isoformat(),
        "max_selectable_date": max_selectable.isoformat(),
        "period_start": pd.Timestamp(c_first["日期"]).strftime("%Y-%m-%d"),
        "period_end": pd.Timestamp(c_latest["日期"]).strftime("%Y-%m-%d"),
        "kpi": {
            "period_return": round(portfolio_change, 4),
            "benchmark_level": round(float(c_latest[bench_col]), 2),
            "benchmark_return": round(index_change, 4),
            "alpha": round(alpha, 4),
            "total_asset": round(float(c_latest["总持仓市值"]), 2),
            "max_drawdown": round(max_drawdown, 4),
            "sharpe_ratio": round(sharpe_ratio, 4),
            "period_net_inflow": round(period_net_inflow, 2),
            "engine_principal": round(float(engine_principal), 2),
            "ledger_net": round(float(ledger_net), 2),
            "ledger_in": round(float(ledger_in), 2),
            "ledger_out": round(float(ledger_out), 2),
        },
        "charts": charts,
        "commentary": {"period": rep_name, "html": commentary},
        "snapshot": {
            "cash": round(float(latest["账户可用现金"]), 2),
            "fees": round(float(latest["累计税费"]), 2),
            "as_of": pd.Timestamp(latest["日期"]).strftime("%Y-%m-%d"),
        },
    }

    if include_admin and not client_mode:
        hold_cols = ["日期", "总持仓市值", "账户可用现金", "累计净本金", "累计税费"]
        for name in stock_names:
            col = f"{name}_持仓"
            if col in admin_df.columns:
                hold_cols.append(col)
        result["holdings"] = _df_records(admin_df.tail(1), hold_cols)
        result["trades"] = trades.replace({np.nan: None}).to_dict(orient="records") if not trades.empty else []
        for row in result["trades"]:
            if row.get("日期"):
                row["日期"] = pd.Timestamp(row["日期"]).strftime("%Y-%m-%d")
        result["stock_names"] = stock_names

    return result
