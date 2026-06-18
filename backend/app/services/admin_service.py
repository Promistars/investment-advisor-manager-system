"""Admin-only analytics payloads (holdings, timeline, statement)."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db_manager as db
import portfolio_engine as pe
from app.services.analytics_service import build_admin_df, compute_dashboard

BENCHMARK = pe.BENCHMARK_NAME


def suggested_price(admin_df: pd.DataFrame, asset: str, on_date: date) -> float:
    past = admin_df[admin_df["日期"].dt.date <= on_date]
    if past.empty or not asset:
        return 0.0
    raw_col = f"{asset}不复权收盘价"
    normal_col = f"{asset}收盘价"
    row = past.iloc[-1]
    if raw_col in past.columns and pd.notna(row.get(raw_col)):
        return float(row[raw_col])
    if normal_col in past.columns and pd.notna(row.get(normal_col)):
        return float(row[normal_col])
    return 0.0


def holdings_allocation(admin_df: pd.DataFrame, stock_names: list[str]) -> list[dict[str, Any]]:
    if admin_df.empty:
        return []
    latest = admin_df.iloc[-1]
    snap_cash = max(float(latest["账户可用现金"]), 0.0)
    items: list[dict[str, Any]] = [{"name": "可用现金", "value": snap_cash, "shares": 0.0}]
    for asset in stock_names:
        qty = float(latest.get(f"{asset}_持仓", 0) or 0)
        if qty > 0:
            price = float(latest.get(f"{asset}收盘价", 0) or 0)
            items.append({"name": asset, "value": qty * price, "shares": qty})
    total = sum(i["value"] for i in items)
    for i in items:
        i["pct"] = round((i["value"] / total * 100) if total > 0 else 0, 2)
        i["value"] = round(i["value"], 2)
    return [i for i in items if i["value"] > 0]


def admin_timeline(admin_df: pd.DataFrame, trades_df: pd.DataFrame) -> dict[str, Any]:
    series = admin_df[["日期", "总持仓市值", "累计净本金"]].copy()
    series["日期"] = pd.to_datetime(series["日期"]).dt.strftime("%Y-%m-%d")
    asset_line = series.replace({np.nan: None}).to_dict(orient="records")

    markers: list[dict[str, Any]] = []
    marker_styles = {
        "买入股票": {"color": "#ef4444", "name": "买入"},
        "卖出股票": {"color": "#16a34a", "name": "卖出"},
        "转入本金": {"color": "#eab308", "name": "注资"},
        "提取现金": {"color": "#78716c", "name": "赎回"},
        "提取管理费(内扣)": {"color": "#9333ea", "name": "内扣结账"},
        "结账重置(外付)": {"color": "#9333ea", "name": "外付结账"},
    }
    if not trades_df.empty:
        tdf = trades_df.copy()
        tdf["日期"] = pd.to_datetime(tdf["日期"])
        for t_type, style in marker_styles.items():
            subset = tdf[tdf["操作类型"] == t_type]
            for _, row in subset.iterrows():
                d = row["日期"]
                match = admin_df[admin_df["日期"] == d]["总持仓市值"]
                y = float(match.iloc[0]) if not match.empty else None
                if y is not None:
                    markers.append(
                        {
                            "date": d.strftime("%Y-%m-%d"),
                            "type": t_type,
                            "label": style["name"],
                            "color": style["color"],
                            "y": y,
                            "amount": float(row["实际结算总金额(¥)"]) if pd.notna(row.get("实际结算总金额(¥)")) else 0,
                        }
                    )
    return {"series": asset_line, "markers": markers}


def full_statement(admin_df: pd.DataFrame, stock_names: list[str]) -> list[dict[str, Any]]:
    ever_held = [a for a in stock_names if f"{a}_持仓" in admin_df.columns and admin_df[f"{a}_持仓"].max() > 0]
    cols = ["日期", "总持仓市值", "累计净本金", "账户可用现金", "精确组合净值", f"{BENCHMARK}收盘价"]
    show = admin_df.copy()
    for asset in ever_held:
        is_holding = (show[f"{asset}_持仓"] > 0) | (show[f"{asset}_持仓"].shift(1) > 0)
        show[f"{asset}收盘价"] = np.where(is_holding, show[f"{asset}收盘价"], np.nan)
        cols.append(f"{asset}收盘价")
    out = show[cols].copy()
    out["日期"] = pd.to_datetime(out["日期"]).dt.strftime("%Y-%m-%d")
    out = out.iloc[::-1]
    return out.replace({np.nan: None}).to_dict(orient="records")


def report_period_names() -> dict[str, str]:
    from datetime import datetime, timedelta

    today = datetime.now().date()
    last_month = today.replace(day=1) - timedelta(days=1)
    rep_month = f"{last_month.strftime('%Y年%m月')}-月报"
    pq = ((today.month - 1) // 3 + 1) - 1
    pq_yr = today.year if pq > 0 else today.year - 1
    pq = pq if pq > 0 else 4
    rep_quarter = f"{pq_yr}年Q{pq}-季报"
    rep_year = f"{today.year - 1}年-年报"
    return {"monthly": rep_month, "quarterly": rep_quarter, "yearly": rep_year}


def find_invalid_trade_indices(username: str, account: str) -> list[int]:
    invalid: list[int] = []

    def _collect(txn: dict) -> None:
        idx = txn.get("idx")
        if idx is not None:
            invalid.append(int(idx))

    try:
        fp = pe.compute_market_fingerprint()
        ctx = pe.get_market_context(fp)
        trades = db.get_trades(username, account)
        start = pe.get_acc_start_date(username, account, ctx.global_min_date)
        pe.run_simulation(
            ctx.portfolio_df,
            ctx.stock_names,
            ctx.dividend_book,
            start,
            trades,
            include_row_index=True,
            on_invalid_txn=_collect,
        )
    except (FileNotFoundError, ValueError, OSError):
        return []
    return invalid


def build_admin_bundle(
    username: str,
    account: str,
    *,
    view: str = "monthly",
    custom_start: date | None = None,
    custom_end: date | None = None,
) -> dict[str, Any]:
    admin_df, account_start, global_max, stock_names = build_admin_df(username, account)
    trades = db.get_trades(username, account)
    latest = admin_df.iloc[-1]
    snap_date = pd.Timestamp(latest["日期"]).strftime("%Y-%m-%d")
    snap_d = pd.Timestamp(latest["日期"]).date()

    engine_principal = pe.net_principal_on_date(admin_df, snap_d)
    ledger_net, ledger_in, ledger_out = pe.ledger_net_principal(trades, account_start, snap_d)
    total_asset = round(float(latest["总持仓市值"]), 2)
    holdings = holdings_allocation(admin_df, stock_names)
    cash_item = next((h for h in holdings if h["name"] == "可用现金"), None)
    cash_pct = float(cash_item["pct"]) if cash_item else 0.0
    stock_positions = [h for h in holdings if h["name"] != "可用现金"]
    nav = float(latest.get("精确组合净值", 1) or 1)

    dashboard = compute_dashboard(
        username,
        account,
        view=view,  # type: ignore[arg-type]
        client_mode=False,
        custom_start=custom_start,
        custom_end=custom_end,
        include_admin=True,
    )

    from app.services.account_config import get_last_type

    return {
        **dashboard,
        "admin": {
            "snap_date": snap_date,
            "cash": round(float(latest["账户可用现金"]), 2),
            "fees": round(float(latest["累计税费"]), 2),
            "engine_principal": round(float(engine_principal), 2),
            "ledger_net": round(float(ledger_net), 2),
            "ledger_in": round(float(ledger_in), 2),
            "ledger_out": round(float(ledger_out), 2),
            "principal_mismatch": abs(float(engine_principal) - float(ledger_net)) > 0.02,
            "account_start": account_start.isoformat(),
            "global_min_date": pe.get_market_context(pe.compute_market_fingerprint()).global_min_date.isoformat(),
            "global_max_date": global_max.isoformat(),
            "stock_names": stock_names,
            "last_trade_type": get_last_type(username, account),
            "holdings": holdings,
            "total_asset": total_asset,
            "unrealized_pnl": round(total_asset - float(engine_principal), 2),
            "return_pct": round((total_asset / float(engine_principal) - 1) * 100, 2) if engine_principal else 0.0,
            "position_count": len(stock_positions),
            "cash_pct": round(cash_pct, 2),
            "stock_pct": round(100.0 - cash_pct, 2),
            "nav": round(nav, 4),
            "trade_count": len(trades),
            "timeline": admin_timeline(admin_df, trades),
            "statement": full_statement(admin_df, stock_names),
            "report_periods": report_period_names(),
            "invalid_trade_indices": find_invalid_trade_indices(username, account),
        },
    }
