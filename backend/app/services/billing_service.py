"""High-water mark billing engine."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any, Literal

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BillingMode = Literal["pct", "asset"]


def _sniff_col(df: pd.DataFrame, keywords: list[str], default: str) -> str:
    if df.empty:
        return default
    for col in df.columns:
        for kw in keywords:
            if kw.lower() in str(col).lower():
                return col
    return default


def compute_billing_state(
    trades_df: pd.DataFrame,
    admin_df: pd.DataFrame,
    account_start_date: date,
    *,
    target_mode: BillingMode = "pct",
    target_pct: float = 20.0,
    target_asset: float | None = None,
    fee_ratio: float = 20.0,
    as_of_date: date | None = None,
) -> dict[str, Any]:
    log_df = trades_df.copy() if trades_df is not None else pd.DataFrame()
    c_type = _sniff_col(log_df, ["操作类型", "type", "类型"], "操作类型")
    c_date = _sniff_col(log_df, ["日期", "date", "时间"], "日期")
    c_tot = _sniff_col(log_df, ["实际结算总金额", "total", "总额", "金额"], "实际结算总金额(¥)")
    c_prc = _sniff_col(log_df, ["成交单价", "price"], "成交单价(¥)")

    log_sorted = log_df.copy()
    if not log_sorted.empty and c_date in log_sorted.columns:
        log_sorted["__date_val"] = pd.to_datetime(log_sorted[c_date]).dt.date

    if not log_sorted.empty and c_type in log_sorted.columns:
        billing_txns = log_sorted[log_sorted[c_type].isin(["提取管理费(内扣)", "结账重置(外付)"])].copy()
    else:
        billing_txns = pd.DataFrame()

    if not billing_txns.empty:
        billing_txns = billing_txns.sort_values(by="__date_val")
        last_row = billing_txns.iloc[-1]
        last_watermark_date = last_row["__date_val"]
        base_watermark = float(last_row[c_prc]) if pd.notna(last_row[c_prc]) else 0.0
        subsequent = log_sorted[log_sorted["__date_val"] > last_watermark_date]
    else:
        last_watermark_date = account_start_date
        base_watermark = 0.0
        subsequent = log_sorted if not log_sorted.empty else pd.DataFrame()

    recent_net_inflow = 0.0
    if not subsequent.empty and c_type in subsequent.columns and c_tot in subsequent.columns:
        inflows = pd.to_numeric(subsequent[subsequent[c_type] == "转入本金"][c_tot], errors="coerce").fillna(0).sum()
        outflows = pd.to_numeric(subsequent[subsequent[c_type] == "提取现金"][c_tot], errors="coerce").fillna(0).sum()
        recent_net_inflow = float(inflows - outflows)

    adjusted_watermark = base_watermark + recent_net_inflow
    if adjusted_watermark <= 0:
        adjusted_watermark = 1.0

    latest = admin_df.iloc[-1]
    snap_date = pd.Timestamp(latest["日期"]).date() if as_of_date is None else as_of_date
    hist = admin_df[admin_df["日期"].dt.date <= snap_date]
    current_asset = float(hist.iloc[-1]["总持仓市值"]) if not hist.empty else float(latest["总持仓市值"])
    period_profit = current_asset - adjusted_watermark

    if target_mode == "pct":
        resolved_target_asset = adjusted_watermark * (1.0 + target_pct / 100.0)
    else:
        resolved_target_asset = target_asset if target_asset is not None else adjusted_watermark * 1.2
        target_pct = ((resolved_target_asset / adjusted_watermark) - 1.0) * 100 if adjusted_watermark > 0 else 0.0

    reached = current_asset >= resolved_target_asset
    agreed_profit = resolved_target_asset - adjusted_watermark
    fee_amount = agreed_profit * (fee_ratio / 100.0) if reached else 0.0
    extra_profit = current_asset - resolved_target_asset if reached else 0.0

    history_rows: list[dict[str, Any]] = []
    if not billing_txns.empty:
        for _, row in billing_txns.sort_values(by="__date_val", ascending=False).iterrows():
            history_rows.append(
                {
                    "date": str(row["__date_val"]),
                    "type": str(row[c_type]),
                    "watermark": float(row[c_prc]) if pd.notna(row[c_prc]) else 0.0,
                    "fee_amount": float(row[c_tot]) if pd.notna(row[c_tot]) else 0.0,
                }
            )

    return {
        "last_watermark_date": str(last_watermark_date),
        "base_watermark": round(base_watermark, 2),
        "adjusted_watermark": round(adjusted_watermark, 2),
        "recent_net_inflow": round(recent_net_inflow, 2),
        "current_asset": round(current_asset, 2),
        "period_profit": round(period_profit, 2),
        "target_mode": target_mode,
        "target_pct": round(target_pct, 4),
        "target_asset": round(resolved_target_asset, 2),
        "fee_ratio": fee_ratio,
        "reached": reached,
        "fee_amount": round(fee_amount, 2),
        "extra_profit": round(extra_profit, 2),
        "agreed_profit": round(agreed_profit, 2) if reached else 0.0,
        "billing_history": history_rows,
    }


def compute_historical_billing(
    trades_df: pd.DataFrame,
    admin_df: pd.DataFrame,
    account_start_date: date,
    manual_date: date,
    *,
    target_mode: BillingMode,
    target_pct: float,
    target_asset: float | None,
    fee_ratio: float,
) -> dict[str, Any]:
    base = compute_billing_state(
        trades_df,
        admin_df,
        account_start_date,
        target_mode=target_mode,
        target_pct=target_pct,
        target_asset=target_asset,
        fee_ratio=fee_ratio,
    )
    log_df = trades_df.copy()
    c_type = _sniff_col(log_df, ["操作类型"], "操作类型")
    c_date = _sniff_col(log_df, ["日期"], "日期")
    c_tot = _sniff_col(log_df, ["实际结算总金额"], "实际结算总金额(¥)")

    log_sorted = log_df.copy()
    if not log_sorted.empty:
        log_sorted["__date_val"] = pd.to_datetime(log_sorted[c_date]).dt.date

    last_watermark_date = date.fromisoformat(base["last_watermark_date"])
    base_watermark = base["base_watermark"]
    subsequent = log_sorted[log_sorted["__date_val"] > last_watermark_date] if not log_sorted.empty else pd.DataFrame()

    hist_admin = admin_df[admin_df["日期"].dt.date <= manual_date]
    if hist_admin.empty:
        return {"ok": False, "message": "no_data"}
    hist_asset = float(hist_admin.iloc[-1]["总持仓市值"])

    hist_net_inflow = 0.0
    if not subsequent.empty and c_type in subsequent.columns:
        hist_txns = subsequent[subsequent["__date_val"] <= manual_date]
        h_in = pd.to_numeric(hist_txns[hist_txns[c_type] == "转入本金"][c_tot], errors="coerce").fillna(0).sum()
        h_out = pd.to_numeric(hist_txns[hist_txns[c_type] == "提取现金"][c_tot], errors="coerce").fillna(0).sum()
        hist_net_inflow = float(h_in - h_out)

    hist_watermark = base_watermark + hist_net_inflow
    if hist_watermark <= 0:
        hist_watermark = 1.0

    if target_mode == "pct":
        hist_target = hist_watermark * (1.0 + target_pct / 100.0)
    else:
        hist_target = target_asset if target_asset is not None else base["target_asset"]

    if hist_asset >= hist_target:
        agreed = hist_target - hist_watermark
        hist_fee = agreed * (fee_ratio / 100.0)
        target_hist_watermark = hist_target
        reached = True
    else:
        hist_profit = hist_asset - hist_watermark
        hist_fee = hist_profit * (fee_ratio / 100.0) if hist_profit > 0 else 0.0
        target_hist_watermark = hist_asset
        reached = False

    return {
        "ok": True,
        "hist_asset": round(hist_asset, 2),
        "hist_target": round(hist_target, 2),
        "hist_fee": round(max(0, hist_fee), 2),
        "target_hist_watermark": round(target_hist_watermark, 2),
        "reached": reached,
    }


def append_billing_trade(
    trades_df: pd.DataFrame,
    *,
    txn_date: date,
    txn_type: str,
    watermark: float,
    fee_amount: float,
) -> pd.DataFrame:
    new_row = {
        "日期": txn_date.strftime("%Y-%m-%d"),
        "操作类型": txn_type,
        "标的": "管理费",
        "数量(股)": 1,
        "成交单价(¥)": watermark,
        "实际结算总金额(¥)": fee_amount,
    }
    merged = pd.concat([trades_df, pd.DataFrame([new_row])], ignore_index=True)
    merged["日期"] = pd.to_datetime(merged["日期"]).dt.date
    merged = merged.sort_values(by="日期").reset_index(drop=True)
    merged["日期"] = merged["日期"].astype(str)
    return merged
