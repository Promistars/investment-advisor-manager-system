"""
IAMS 个股行情抓取（项目内统一入口，供 auto_fetch / 看板添股共用）。
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

import akshare as ak
import baostock as bs
import pandas as pd

from iams_network import apply_project_network_env, eastmoney_kline_available

apply_project_network_env()

DATA_DIR = "financial_data"
DIVIDEND_DIR = "dividend_data"
CONFIG_FILE = "stock_config.json"


def _bs_code_to_sina_symbol(bs_code: str) -> str:
    return bs_code.replace(".", "")


def _fetch_stock_via_sina_daily(bs_code: str, fetch_start: str, fetch_end: str):
    symbol = _bs_code_to_sina_symbol(bs_code)
    start_s = fetch_start.replace("-", "")
    end_s = fetch_end.replace("-", "")
    df_qfq = ak.stock_zh_a_daily(symbol=symbol, start_date=start_s, end_date=end_s, adjust="qfq")
    df_raw = ak.stock_zh_a_daily(symbol=symbol, start_date=start_s, end_date=end_s, adjust="")
    if df_qfq.empty:
        return pd.DataFrame(), pd.DataFrame()
    df_adj = df_qfq.rename(
        columns={
            "date": "date",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
            "amount": "amount",
        }
    ).copy()
    df_adj["date"] = pd.to_datetime(df_adj["date"]).dt.strftime("%Y-%m-%d")
    if "turnover" in df_qfq.columns:
        df_adj["turn"] = (df_qfq["turnover"] * 100).round(4)
    else:
        df_adj["turn"] = ""
    df_adj["pctChg"] = df_adj["close"].pct_change().mul(100).round(4)
    df_adj.loc[df_adj.index[0], "pctChg"] = 0.0
    df_adj["peTTM"] = ""
    df_adj["pbMRQ"] = ""
    df_raw_bs = pd.DataFrame()
    if not df_raw.empty:
        df_raw_bs = df_raw[["date", "close"]].rename(columns={"date": "date", "close": "raw_close"})
        df_raw_bs["date"] = pd.to_datetime(df_raw_bs["date"]).dt.strftime("%Y-%m-%d")
    return df_adj, df_raw_bs


def name_to_bs_code(stock_name: str) -> str | None:
    df = ak.stock_info_a_code_name()
    match = df[df["name"] == stock_name]
    if match.empty:
        return None
    if "code" in match.columns:
        raw_code = str(match.iloc[0]["code"])
    elif "symbol" in match.columns:
        raw_code = str(match.iloc[0]["symbol"])
    else:
        raw_code = str(match.iloc[0].values[0])
    if raw_code.startswith("6"):
        return f"sh.{raw_code}"
    if raw_code.startswith(("0", "3")):
        return f"sz.{raw_code}"
    if raw_code.startswith(("8", "4", "9")):
        return f"bj.{raw_code}"
    return f"sh.{raw_code}"


def _try_baostock(bs_code: str, fetch_start: str, fetch_end: str):
    lg = bs.login()
    if lg.error_code != "0":
        bs.logout()
        return pd.DataFrame(), pd.DataFrame()
    try:
        rs_adj = bs.query_history_k_data_plus(
            bs_code,
            "date,open,high,low,close,volume,amount,turn,pctChg,peTTM,pbMRQ",
            start_date=fetch_start,
            end_date=fetch_end,
            frequency="d",
            adjustflag="2",
        )
        data_adj = []
        while (rs_adj.error_code == "0") & rs_adj.next():
            data_adj.append(rs_adj.get_row_data())
        df_adj = pd.DataFrame(data_adj, columns=rs_adj.fields) if data_adj else pd.DataFrame()

        rs_raw = bs.query_history_k_data_plus(
            bs_code, "date,close", start_date=fetch_start, end_date=fetch_end, frequency="d", adjustflag="3"
        )
        data_raw = []
        while (rs_raw.error_code == "0") & rs_raw.next():
            data_raw.append(rs_raw.get_row_data())
        df_raw = pd.DataFrame(data_raw, columns=["date", "raw_close"]) if data_raw else pd.DataFrame()
        return df_adj, df_raw
    finally:
        bs.logout()


def _try_eastmoney_hist(pure_code: str, fetch_start: str, fetch_end: str):
    if not eastmoney_kline_available():
        return pd.DataFrame(), pd.DataFrame()
    fetch_start_ak = fetch_start.replace("-", "")
    fetch_end_ak = fetch_end.replace("-", "")
    df_ak_qfq = ak.stock_zh_a_hist(
        symbol=pure_code, period="daily", start_date=fetch_start_ak, end_date=fetch_end_ak, adjust="qfq"
    )
    df_ak_raw = ak.stock_zh_a_hist(
        symbol=pure_code, period="daily", start_date=fetch_start_ak, end_date=fetch_end_ak, adjust=""
    )
    if df_ak_qfq.empty:
        return pd.DataFrame(), pd.DataFrame()
    df_adj = df_ak_qfq.rename(
        columns={
            "日期": "date",
            "收盘": "close",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "换手率": "turn",
            "涨跌幅": "pctChg",
        }
    )
    df_adj["date"] = df_adj["date"].astype(str)
    df_adj["peTTM"] = ""
    df_adj["pbMRQ"] = ""
    df_raw = pd.DataFrame()
    if not df_ak_raw.empty:
        df_raw = df_ak_raw[["日期", "收盘"]].rename(columns={"日期": "date", "收盘": "raw_close"})
        df_raw["date"] = df_raw["date"].astype(str)
    return df_adj, df_raw


def fetch_stock_kline(bs_code: str, fetch_start: str, fetch_end: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """返回 (df_adj, df_raw, channel_name)。"""
    # 1. 新浪（本服务器可用，优先）
    try:
        df_adj, df_raw = _fetch_stock_via_sina_daily(bs_code, fetch_start, fetch_end)
        if not df_adj.empty:
            return df_adj, df_raw, "新浪日线"
    except Exception:
        pass

    # 2. 东财 K 线（push2his 在部分机房被墙，探测后再试）
    try:
        pure_code = bs_code.split(".")[1]
        df_adj, df_raw = _try_eastmoney_hist(pure_code, fetch_start, fetch_end)
        if not df_adj.empty:
            return df_adj, df_raw, "东财"
    except Exception:
        pass

    # 3. BaoStock
    try:
        df_adj, df_raw = _try_baostock(bs_code, fetch_start, fetch_end)
        if not df_adj.empty:
            return df_adj, df_raw, "BaoStock"
    except Exception:
        pass

    return pd.DataFrame(), pd.DataFrame(), ""


def _merge_to_csv_df(df_adj: pd.DataFrame, df_raw_bs: pd.DataFrame, name: str) -> pd.DataFrame:
    if df_raw_bs.empty:
        df_k = df_adj.copy()
        df_k["raw_close"] = df_k["close"]
    else:
        df_k = pd.merge(df_adj, df_raw_bs, on="date", how="left")
    df_k.rename(
        columns={
            "date": "日期",
            "close": f"{name}收盘价",
            "open": "开盘价",
            "high": "最高价",
            "low": "最低价",
            "volume": "成交量",
            "amount": "成交额",
            "turn": "换手率",
            "pctChg": "单日涨跌幅(%)",
            "peTTM": "市盈率(PE)",
            "pbMRQ": "市净率(PB)",
            "raw_close": f"{name}不复权收盘价",
        },
        inplace=True,
    )
    df_k["日期"] = pd.to_datetime(df_k["日期"]).dt.strftime("%Y-%m-%d")
    for col in df_k.columns:
        if col != "日期":
            df_k[col] = pd.to_numeric(df_k[col], errors="coerce")
    return df_k


def save_dividend(name: str, bs_code: str) -> None:
    os.makedirs(DIVIDEND_DIR, exist_ok=True)
    pure_code = bs_code.split(".")[1]
    try:
        df_div = ak.stock_fhps_detail_em(symbol=pure_code)
    except Exception:
        return
    if df_div.empty:
        return

    def find_col(keywords):
        for col in df_div.columns:
            if any(k in col for k in keywords):
                return col
        return None

    c_date = find_col(["除权", "除息", "分红日", "派息日"])
    c_cash = find_col(["派息", "现金", "分红", "派现"])
    c_send = find_col(["送股", "送红股"])
    c_trans = find_col(["转增", "转股"])
    if not c_date:
        return
    df_div[c_date] = pd.to_datetime(df_div[c_date], errors="coerce")
    df_div = df_div.dropna(subset=[c_date])
    std_div = pd.DataFrame()
    std_div["日期"] = df_div[c_date].dt.strftime("%Y-%m-%d")

    def deep_clean(series):
        if series is None:
            return 0.0
        return pd.to_numeric(series.astype(str).str.extract(r"(\d+\.?\d*)")[0], errors="coerce").fillna(0.0)

    std_div["每10股派息"] = deep_clean(df_div[c_cash])
    std_div["每10股送股"] = deep_clean(df_div[c_send])
    std_div["每10股转增"] = deep_clean(df_div[c_trans])
    std_div = std_div[std_div["日期"] >= "2023-01-01"]
    std_div = std_div[
        (std_div["每10股派息"] > 0) | (std_div["每10股送股"] > 0) | (std_div["每10股转增"] > 0)
    ]
    if not std_div.empty:
        std_div.to_csv(os.path.join(DIVIDEND_DIR, f"{name}_分红.csv"), index=False, encoding="utf-8-sig")


def update_stock_config(bs_code: str, name: str) -> None:
    stock_dict = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding="utf-8") as f:
            stock_dict = json.load(f)
    stock_dict[bs_code] = name
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(stock_dict, f, ensure_ascii=False, indent=4)


def ingest_new_stock(stock_name: str, start_date: str = "2023-01-01") -> tuple[bool, str]:
    """
    新添标的：立即抓取并入库。返回 (成功与否, 说明信息)。
    """
    bs_code = name_to_bs_code(stock_name)
    if not bs_code:
        return False, f"未找到 A 股「{stock_name}」，请检查简称。"

    fetch_end = datetime.now().strftime("%Y-%m-%d")
    df_adj, df_raw, channel = fetch_stock_kline(bs_code, start_date, fetch_end)
    if df_adj.empty:
        hint = (
            "所有渠道均无数据。"
            if not eastmoney_kline_available()
            else "请检查网络。"
        )
        if not eastmoney_kline_available():
            hint += "（本机东财 push2his K 线接口不可达，已自动走新浪日线）"
        return False, hint

    df_k = _merge_to_csv_df(df_adj, df_raw, stock_name)
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{stock_name}.csv")
    df_k.to_csv(path, index=False, encoding="utf-8-sig")
    update_stock_config(bs_code, stock_name)
    save_dividend(stock_name, bs_code)
    last_date = df_k["日期"].iloc[-1]
    return True, f"已通过【{channel}】抓取 {len(df_k)} 行，最新交易日 {last_date}。"
