"""Shared portfolio simulation engine for hall cards and analytics dashboard."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pandas as pd

DATA_DIR = "financial_data"
INDEX_DIR = "all_indices_data"
DIVIDEND_DIR = "dividend_data"
ACCOUNT_CONFIG_FILE = "account_config.json"
BENCHMARK_NAME = "上证指数"
SNAPSHOT_CACHE_DIR = Path(".cache/hall_snapshots")
ENGINE_VERSION = "2.1.1"


@dataclass(frozen=True)
class AccountSnapshot:
    principal: float
    total_asset: float
    pnl: float
    pnl_pct: float
    as_of_date: str
    cash: float = 0.0

    def as_tuple(self) -> tuple[float, float, float]:
        return self.principal, self.pnl, self.pnl_pct


@dataclass
class MarketContext:
    portfolio_df: pd.DataFrame
    stock_names: list[str]
    stock_info: dict[str, str]
    dividend_book: dict[str, pd.DataFrame]
    global_min_date: date
    global_max_date: date
    fingerprint: str


def _file_mtime(path: str | Path) -> float:
    p = Path(path)
    return p.stat().st_mtime if p.exists() else 0.0


def compute_market_fingerprint() -> str:
    """Fingerprint of market/dividend inputs (not per-account trades)."""
    parts = [ENGINE_VERSION, BENCHMARK_NAME]
    for directory in (DATA_DIR, DIVIDEND_DIR):
        if os.path.isdir(directory):
            for name in sorted(os.listdir(directory)):
                if name.endswith(".csv"):
                    parts.append(f"{name}:{_file_mtime(os.path.join(directory, name))}")
    index_path = os.path.join(INDEX_DIR, f"{BENCHMARK_NAME}.csv")
    parts.append(f"index:{_file_mtime(index_path)}")
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def trades_fingerprint(trades_df: pd.DataFrame) -> str:
    if trades_df is None or trades_df.empty:
        return "empty"
    df = trades_df.sort_values("日期").reset_index(drop=True)
    payload = df.to_csv(index=False).encode()
    return hashlib.sha256(payload).hexdigest()[:16]


def discover_stock_info(
    data_dir: str = DATA_DIR,
    benchmark: str = BENCHMARK_NAME,
) -> tuple[list[str], dict[str, str], list[str]]:
    if not os.path.isdir(data_dir):
        return [], {}, []
    csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    stock_info: dict[str, str] = {}
    for file in csv_files:
        df_temp = pd.read_csv(os.path.join(data_dir, file), nrows=1)
        cols = [
            col for col in df_temp.columns
            if "收盘价" in col and col != f"{benchmark}收盘价"
        ]
        if cols:
            stock_info[file] = cols[0].replace("收盘价", "")
    return csv_files, stock_info, list(stock_info.values())


def load_portfolio_df(
    stock_files: list[str],
    stock_info: dict[str, str],
    benchmark: str = BENCHMARK_NAME,
) -> pd.DataFrame:
    index_path = os.path.join(INDEX_DIR, f"{benchmark}.csv")
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Missing benchmark index file: {index_path}")

    pdf = pd.read_csv(index_path)[["日期", f"{benchmark}收盘价"]]
    pdf["日期"] = pd.to_datetime(pdf["日期"])

    for file in stock_files:
        if file not in stock_info:
            continue
        df = pd.read_csv(os.path.join(DATA_DIR, file))
        df["日期"] = pd.to_datetime(df["日期"])
        s_name = stock_info[file]
        cols_to_merge = ["日期", f"{s_name}收盘价"]
        if "raw_close" in df.columns:
            df = df.rename(columns={"raw_close": f"{s_name}不复权收盘价"})
            cols_to_merge.append(f"{s_name}不复权收盘价")
        pdf = pd.merge(pdf, df[cols_to_merge], on="日期", how="outer")

    return pdf.sort_values("日期").reset_index(drop=True).ffill().bfill()


def load_dividend_events(stock_names: list[str]) -> dict[str, pd.DataFrame]:
    all_divs: dict[str, pd.DataFrame] = {}
    for name in stock_names:
        path = os.path.join(DIVIDEND_DIR, f"{name}_分红.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            df["日期"] = pd.to_datetime(df["日期"]).dt.date
            all_divs[name] = df
    return all_divs


@lru_cache(maxsize=4)
def get_market_context(fingerprint: str) -> MarketContext:
    csv_files, stock_info, stock_names = discover_stock_info()
    portfolio_df = load_portfolio_df(csv_files, stock_info)
    dividend_book = load_dividend_events(stock_names)
    return MarketContext(
        portfolio_df=portfolio_df,
        stock_names=stock_names,
        stock_info=stock_info,
        dividend_book=dividend_book,
        global_min_date=portfolio_df["日期"].min().date(),
        global_max_date=portfolio_df["日期"].max().date(),
        fingerprint=fingerprint,
    )


def load_account_config() -> dict:
    if not os.path.exists(ACCOUNT_CONFIG_FILE):
        return {}
    try:
        with open(ACCOUNT_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def get_acc_start_date(user: str, acc: str, default_date: date) -> date:
    data = load_account_config()
    d_str = data.get(f"{user}_{acc}_start_date")
    if d_str:
        try:
            return datetime.strptime(d_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    return default_date


def save_acc_start_date(user: str, acc: str, date_obj: date) -> None:
    data = load_account_config()
    data[f"{user}_{acc}_start_date"] = date_obj.strftime("%Y-%m-%d")
    with open(ACCOUNT_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    invalidate_user_snapshots(user)


def ledger_net_principal(
    trades_df: pd.DataFrame,
    account_start_date: date,
    as_of_date: date,
) -> tuple[float, float, float]:
    if trades_df is None or trades_df.empty:
        return 0.0, 0.0, 0.0
    df = trades_df.dropna(subset=["日期", "操作类型", "实际结算总金额(¥)"]).copy()
    df["日期"] = pd.to_datetime(df["日期"], errors="coerce").dt.date
    df["实际结算总金额(¥)"] = pd.to_numeric(df["实际结算总金额(¥)"], errors="coerce").fillna(0)
    df = df[(df["日期"] >= account_start_date) & (df["日期"] <= as_of_date)]
    inflows = float(df.loc[df["操作类型"] == "转入本金", "实际结算总金额(¥)"].sum())
    outflows = float(df.loc[df["操作类型"] == "提取现金", "实际结算总金额(¥)"].sum())
    return inflows - outflows, inflows, outflows


def net_principal_on_date(df: pd.DataFrame, on_date: date) -> float:
    mask = df["日期"].dt.date == on_date
    if not mask.any():
        return 0.0
    return float(df.loc[mask, "累计净本金"].iloc[-1])


def build_txns_by_date(
    trades_df: pd.DataFrame,
    account_start_date: date,
    include_row_index: bool = False,
) -> dict[date, list[dict]]:
    txns_by_date: dict[date, list[dict]] = {}
    if trades_df is None or trades_df.empty:
        return txns_by_date

    for idx, row in trades_df.dropna(subset=["日期", "操作类型", "实际结算总金额(¥)"]).iterrows():
        dt = pd.to_datetime(row["日期"]).date()
        if dt < account_start_date:
            continue
        txn = {
            "type": row["操作类型"],
            "asset": str(row["标的"]) if pd.notnull(row["标的"]) else "",
            "qty": float(row["数量(股)"]) if pd.notnull(row["数量(股)"]) else 0.0,
            "price": float(row["成交单价(¥)"]) if pd.notnull(row["成交单价(¥)"]) else 0.0,
            "total": float(row["实际结算总金额(¥)"]),
        }
        if include_row_index:
            txn["idx"] = idx
        txns_by_date.setdefault(dt, []).append(txn)
    return txns_by_date


def run_simulation(
    portfolio_df: pd.DataFrame,
    stock_names: list[str],
    dividend_book: dict[str, pd.DataFrame],
    account_start_date: date,
    trades_df: pd.DataFrame,
    *,
    include_row_index: bool = False,
    on_invalid_txn: Optional[Callable[[dict], None]] = None,
) -> pd.DataFrame:
    admin_df = portfolio_df[portfolio_df["日期"].dt.date >= account_start_date].copy().reset_index(drop=True)
    if admin_df.empty:
        return admin_df

    txns_by_date = build_txns_by_date(trades_df, account_start_date, include_row_index=include_row_index)
    dates = admin_df["日期"].tolist()
    n = len(dates)

    total_asset_series = [0.0] * n
    cash_series = [0.0] * n
    daily_fee_series = [0.0] * n
    cum_fee_series = [0.0] * n
    principal_series = [0.0] * n
    holdings_series = {name: [0.0] * n for name in stock_names}

    current_principal = 0.0
    current_cash = 0.0
    cumulative_fees = 0.0
    current_holdings = {name: 0.0 for name in stock_names}

    for i, row in admin_df.iterrows():
        day = row["日期"].date()
        daily_friction_cost = 0.0

        for asset, qty in current_holdings.items():
            if qty > 0 and asset in dividend_book:
                day_div = dividend_book[asset][dividend_book[asset]["日期"] == day]
                if not day_div.empty:
                    div_info = day_div.iloc[0]
                    cash_gain = (qty / 10.0) * div_info["每10股派息"]
                    if cash_gain > 0:
                        current_cash += cash_gain
                    new_shares = (qty / 10.0) * (div_info["每10股送股"] + div_info["每10股转增"])
                    if new_shares > 0:
                        current_holdings[asset] += new_shares

        for txn in txns_by_date.get(day, []):
            is_valid = True
            t_type = txn["type"]

            if t_type == "转入本金":
                current_cash += txn["total"]
                current_principal += txn["total"]
            elif t_type == "提取现金":
                if current_cash >= txn["total"]:
                    current_cash -= txn["total"]
                    current_principal -= txn["total"]
                else:
                    is_valid = False
            elif t_type == "买入股票":
                if not txn["asset"] or current_cash < txn["total"]:
                    is_valid = False
                else:
                    current_holdings[txn["asset"]] += txn["qty"]
                    current_cash -= txn["total"]
                    diff = txn["total"] - (txn["qty"] * txn["price"])
                    if diff > 0:
                        daily_friction_cost += diff
            elif t_type == "卖出股票":
                if not txn["asset"] or current_holdings.get(txn["asset"], 0) < txn["qty"]:
                    is_valid = False
                else:
                    current_holdings[txn["asset"]] -= txn["qty"]
                    current_cash += txn["total"]
                    diff = (txn["qty"] * txn["price"]) - txn["total"]
                    if diff > 0:
                        daily_friction_cost += diff
            elif t_type == "提取管理费(内扣)":
                if current_cash >= txn["total"]:
                    current_cash -= txn["total"]
                else:
                    is_valid = False
            elif t_type == "结账重置(外付)":
                pass

            if not is_valid:
                if on_invalid_txn is not None:
                    on_invalid_txn(txn)
                continue

        total_market_val = 0.0
        for name in stock_names:
            raw_col = f"{name}不复权收盘价"
            price = row[raw_col] if raw_col in row else row[f"{name}收盘价"]
            total_market_val += current_holdings[name] * price

        total_asset_series[i] = current_cash + total_market_val
        cash_series[i] = current_cash
        daily_fee_series[i] = daily_friction_cost
        cumulative_fees += daily_friction_cost
        cum_fee_series[i] = cumulative_fees
        principal_series[i] = current_principal
        for name in stock_names:
            holdings_series[name][i] = current_holdings[name]

    admin_df["总持仓市值"] = total_asset_series
    admin_df["账户可用现金"] = cash_series
    admin_df["当日产生税费"] = daily_fee_series
    admin_df["累计税费"] = cum_fee_series
    admin_df["累计净本金"] = principal_series
    for name in stock_names:
        admin_df[f"{name}_持仓"] = holdings_series[name]

    return admin_df


def enrich_admin_metrics(
    admin_df: pd.DataFrame,
    benchmark: str = BENCHMARK_NAME,
) -> pd.DataFrame:
    if admin_df.empty:
        return admin_df

    admin_df = admin_df.copy()
    admin_df["每日净流入"] = admin_df["累计净本金"].diff().fillna(admin_df["累计净本金"])
    admin_df["前日总资产"] = admin_df["总持仓市值"].shift(1).fillna(0)
    admin_df["单日成本基数"] = admin_df["前日总资产"] + admin_df["每日净流入"].clip(lower=0)
    admin_df["单日盈亏"] = admin_df["总持仓市值"] - admin_df["前日总资产"] - admin_df["每日净流入"]
    admin_df["账户当日收益率"] = np.where(
        admin_df["单日成本基数"] > 0,
        (admin_df["单日盈亏"] / admin_df["单日成本基数"]) * 100,
        0.0,
    )
    admin_df["精确组合净值"] = (1.0 + admin_df["账户当日收益率"] / 100.0).cumprod()
    bench_col = f"{benchmark}收盘价"
    if bench_col in admin_df.columns:
        admin_df["大盘当日收益率"] = admin_df[bench_col].pct_change().fillna(0) * 100
    return admin_df


def snapshot_from_admin_df(admin_df: pd.DataFrame) -> AccountSnapshot:
    if admin_df.empty:
        return AccountSnapshot(0.0, 0.0, 0.0, 0.0, "", 0.0)

    latest = admin_df.iloc[-1]
    principal = float(latest["累计净本金"])
    total_asset = float(latest["总持仓市值"])
    pnl = total_asset - principal
    pnl_pct = (pnl / principal * 100) if principal > 0 else 0.0
    as_of = pd.Timestamp(latest["日期"]).strftime("%Y-%m-%d")
    return AccountSnapshot(
        principal=principal,
        total_asset=total_asset,
        pnl=pnl,
        pnl_pct=pnl_pct,
        as_of_date=as_of,
        cash=float(latest["账户可用现金"]),
    )


def compute_account_snapshot(
    username: str,
    acc_name: str,
    trades_df: pd.DataFrame,
    market_ctx: Optional[MarketContext] = None,
    account_start_date: Optional[date] = None,
) -> AccountSnapshot:
    fingerprint = compute_market_fingerprint()
    ctx = market_ctx or get_market_context(fingerprint)

    if trades_df is None or trades_df.empty:
        return AccountSnapshot(0.0, 0.0, 0.0, 0.0, "", 0.0)

    start = account_start_date or get_acc_start_date(username, acc_name, ctx.global_min_date)
    admin_df = run_simulation(
        ctx.portfolio_df,
        ctx.stock_names,
        ctx.dividend_book,
        start,
        trades_df,
    )
    return snapshot_from_admin_df(admin_df)


def _cache_path(username: str) -> Path:
    safe = hashlib.sha256(username.encode()).hexdigest()[:12]
    return SNAPSHOT_CACHE_DIR / f"{safe}.json"


def _load_user_cache(username: str) -> dict:
    path = _cache_path(username)
    if not path.exists():
        return {"market_fp": "", "accounts": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"market_fp": "", "accounts": {}}
        data.setdefault("accounts", {})
        return data
    except (json.JSONDecodeError, OSError):
        return {"market_fp": "", "accounts": {}}


def _save_user_cache(username: str, data: dict) -> None:
    SNAPSHOT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(username)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def invalidate_user_snapshots(username: str) -> None:
    path = _cache_path(username)
    if path.exists():
        path.unlink(missing_ok=True)


def batch_account_snapshots(
    username: str,
    account_names: list[str],
    trades_by_account: Optional[dict[str, pd.DataFrame]] = None,
) -> dict[str, AccountSnapshot]:
    """Compute hall-card snapshots for many accounts (shared market load + disk cache)."""
    if not account_names:
        return {}

    market_fp = compute_market_fingerprint()
    ctx = get_market_context(market_fp)
    cache = _load_user_cache(username)

    if cache.get("market_fp") != market_fp:
        cache = {"market_fp": market_fp, "accounts": {}}
    elif "accounts" not in cache:
        cache["accounts"] = {}

    if trades_by_account is None:
        import db_manager as db
        trades_by_account = db.get_all_trades_for_user(username)

    results: dict[str, AccountSnapshot] = {}
    dirty = False

    for acc_name in account_names:
        trades_df = trades_by_account.get(acc_name, pd.DataFrame())
        start = get_acc_start_date(username, acc_name, ctx.global_min_date)
        t_hash = trades_fingerprint(trades_df)
        cache_key = f"{acc_name}|{start.isoformat()}|{t_hash}|{ENGINE_VERSION}"

        cached = cache["accounts"].get(acc_name)
        if cached and cached.get("cache_key") == cache_key:
            results[acc_name] = AccountSnapshot(**{k: cached[k] for k in AccountSnapshot.__dataclass_fields__})
            continue

        snap = compute_account_snapshot(username, acc_name, trades_df, market_ctx=ctx, account_start_date=start)
        results[acc_name] = snap
        cache["accounts"][acc_name] = {**asdict(snap), "cache_key": cache_key}
        dirty = True

    stale = set(cache["accounts"]) - set(account_names)
    if stale:
        for acc in stale:
            del cache["accounts"][acc]
        dirty = True

    if dirty:
        cache["market_fp"] = market_fp
        _save_user_cache(username, cache)

    return results
