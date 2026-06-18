import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

import db_manager as db
from app.deps import get_current_user
from app.schemas.auth import MessageResponse
from app.services import account_config, admin_service, billing_service
from app.services.analytics_service import build_admin_df

router = APIRouter(prefix="/accounts/{account_name}/admin", tags=["admin"])


class AppendTradeBody(BaseModel):
    日期: str
    操作类型: str
    标的: str = ""
    数量股: float | None = None
    成交单价: float | None = None
    实际结算总金额: float


class BillingQuery(BaseModel):
    target_mode: str = "pct"
    target_pct: float = 20.0
    target_asset: float | None = None
    fee_ratio: float = 20.0


class BillingActionBody(BillingQuery):
    action: str  # internal | external | manual_internal | manual_external
    manual_date: str | None = None
    manual_fee: float | None = None


class RemoveTradesBody(BaseModel):
    indices: list[int]


@router.get("")
def get_admin_bundle(
    account_name: str,
    view: str = Query("monthly"),
    custom_start: str | None = None,
    custom_end: str | None = None,
    user: str = Depends(get_current_user),
):
    if not db.get_account_id(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    try:
        cs = date.fromisoformat(custom_start) if custom_start else None
        ce = date.fromisoformat(custom_end) if custom_end else None
        return admin_service.build_admin_bundle(user, account_name, view=view, custom_start=cs, custom_end=ce)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/suggested-price")
def get_suggested_price(
    account_name: str,
    asset: str = Query(""),
    on_date: str = Query(...),
    user: str = Depends(get_current_user),
):
    if not db.get_account_id(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    admin_df, _, _, _ = build_admin_df(user, account_name)
    d = date.fromisoformat(on_date)
    price = admin_service.suggested_price(admin_df, asset, d)
    return {"price": round(price, 4)}


@router.post("/trades/append", response_model=MessageResponse)
def append_trade(account_name: str, body: AppendTradeBody, user: str = Depends(get_current_user)):
    if not db.get_account_id(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    if body.实际结算总金额 <= 0:
        raise HTTPException(status_code=400, detail="Amount must be > 0")
    df = db.get_trades(user, account_name)
    row = {
        "日期": body.日期,
        "操作类型": body.操作类型,
        "标的": body.标的 or None,
        "数量(股)": body.数量股,
        "成交单价(¥)": body.成交单价,
        "实际结算总金额(¥)": body.实际结算总金额,
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    db.save_trades(user, account_name, df)
    account_config.save_last_type(user, account_name, body.操作类型)
    return MessageResponse(message="saved")


@router.post("/trades/remove-indices", response_model=MessageResponse)
def remove_trade_indices(account_name: str, body: RemoveTradesBody, user: str = Depends(get_current_user)):
    if not db.get_account_id(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    df = db.get_trades(user, account_name)
    if df.empty or not body.indices:
        return MessageResponse(message="nothing to remove")
    keep = [i for i in range(len(df)) if i not in set(body.indices)]
    df = df.iloc[keep].reset_index(drop=True)
    db.save_trades(user, account_name, df)
    return MessageResponse(message="removed")


@router.post("/billing/preview")
def billing_preview(account_name: str, body: BillingQuery, user: str = Depends(get_current_user)):
    if not db.get_account_id(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    admin_df, start, _, _ = build_admin_df(user, account_name)
    trades = db.get_trades(user, account_name)
    mode = "pct" if body.target_mode != "asset" else "asset"
    return billing_service.compute_billing_state(
        trades,
        admin_df,
        start,
        target_mode=mode,
        target_pct=body.target_pct,
        target_asset=body.target_asset,
        fee_ratio=body.fee_ratio,
    )


@router.post("/billing/historical-preview")
def billing_historical_preview(
    account_name: str,
    body: BillingActionBody,
    user: str = Depends(get_current_user),
):
    if not db.get_account_id(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    if not body.manual_date:
        raise HTTPException(status_code=400, detail="manual_date required")
    admin_df, start, _, _ = build_admin_df(user, account_name)
    trades = db.get_trades(user, account_name)
    mode = "pct" if body.target_mode != "asset" else "asset"
    return billing_service.compute_historical_billing(
        trades,
        admin_df,
        start,
        date.fromisoformat(body.manual_date),
        target_mode=mode,
        target_pct=body.target_pct,
        target_asset=body.target_asset,
        fee_ratio=body.fee_ratio,
    )


@router.post("/billing/execute", response_model=MessageResponse)
def billing_execute(account_name: str, body: BillingActionBody, user: str = Depends(get_current_user)):
    if not db.get_account_id(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    admin_df, start, global_max, _ = build_admin_df(user, account_name)
    trades = db.get_trades(user, account_name)
    mode = "pct" if body.target_mode != "asset" else "asset"
    state = billing_service.compute_billing_state(
        trades,
        admin_df,
        start,
        target_mode=mode,
        target_pct=body.target_pct,
        target_asset=body.target_asset,
        fee_ratio=body.fee_ratio,
    )

    if body.action in ("internal", "external"):
        if not state["reached"]:
            raise HTTPException(status_code=400, detail="Target not reached")
        txn_date = global_max
        fee = state["fee_amount"]
        watermark = state["target_asset"] - fee if body.action == "internal" else state["target_asset"]
        txn_type = "提取管理费(内扣)" if body.action == "internal" else "结账重置(外付)"
    elif body.action in ("manual_internal", "manual_external"):
        if not body.manual_date or body.manual_fee is None:
            raise HTTPException(status_code=400, detail="manual_date and manual_fee required")
        hist = billing_service.compute_historical_billing(
            trades,
            admin_df,
            start,
            date.fromisoformat(body.manual_date),
            target_mode=mode,
            target_pct=body.target_pct,
            target_asset=body.target_asset,
            fee_ratio=body.fee_ratio,
        )
        if not hist.get("ok"):
            raise HTTPException(status_code=400, detail="Historical preview failed")
        txn_date = date.fromisoformat(body.manual_date)
        fee = body.manual_fee
        watermark = hist["target_hist_watermark"] - fee if body.action == "manual_internal" else hist["target_hist_watermark"]
        txn_type = "提取管理费(内扣)" if body.action == "manual_internal" else "结账重置(外付)"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    updated = billing_service.append_billing_trade(
        trades, txn_date=txn_date, txn_type=txn_type, watermark=watermark, fee_amount=fee
    )
    db.save_trades(user, account_name, updated)
    return MessageResponse(message="billing saved")
