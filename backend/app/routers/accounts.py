import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import APIRouter, Depends, HTTPException, status

import db_manager as db
import portfolio_engine as pe
from app.deps import get_current_user
from app.schemas.accounts import AccountCreateRequest, AccountSummary, FeeTotalResponse, StartDateUpdate
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/accounts", tags=["accounts"])

import pandas as pd

FEE_TYPES = {"提取管理费(内扣)", "结账重置(外付)"}


def _fees_from_trades(trades: pd.DataFrame | list | None) -> float:
    if trades is None:
        return 0.0
    if isinstance(trades, pd.DataFrame):
        if trades.empty or "操作类型" not in trades.columns:
            return 0.0
        col = "实际结算总金额(¥)"
        mask = trades["操作类型"].isin(FEE_TYPES)
        total = float(trades.loc[mask, col].fillna(0).astype(float).sum()) if col in trades.columns else 0.0
        return round(total, 2)
    total = 0.0
    for row in trades:
        if not isinstance(row, dict):
            continue
        if row.get("操作类型") in FEE_TYPES:
            amt = row.get("实际结算总金额(¥)")
            if amt is not None:
                try:
                    total += float(amt)
                except (TypeError, ValueError):
                    pass
    return round(total, 2)


@router.get("", response_model=list[AccountSummary])
def list_accounts(user: str = Depends(get_current_user)):
    accounts = db.get_user_accounts(user)
    if not accounts:
        return []
    names = [a["name"] for a in accounts]
    snaps = pe.batch_account_snapshots(user, names)
    out: list[AccountSummary] = []
    for acc in accounts:
        snap = snaps.get(acc["name"])
        fees = _fees_from_trades(db.get_trades(user, acc["name"]))
        if snap:
            out.append(
                AccountSummary(
                    name=acc["name"],
                    last_accessed=acc.get("last_accessed"),
                    principal=snap.principal,
                    pnl=snap.pnl,
                    pnl_pct=snap.pnl_pct,
                    total_asset=snap.total_asset,
                    as_of_date=snap.as_of_date,
                    fees_collected=fees,
                )
            )
        else:
            out.append(AccountSummary(name=acc["name"], last_accessed=acc.get("last_accessed"), fees_collected=fees))
    return out


@router.get("/fee-total", response_model=FeeTotalResponse)
def total_management_fees(user: str = Depends(get_current_user)):
    """Sum all internal/external fee settlements across the user's accounts."""
    accounts = db.get_user_accounts(user)
    total = 0.0
    for acc in accounts:
        total += _fees_from_trades(db.get_trades(user, acc["name"]))
    return FeeTotalResponse(total_fees=round(total, 2), account_count=len(accounts))


@router.post("", response_model=MessageResponse)
def create_account(body: AccountCreateRequest, user: str = Depends(get_current_user)):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Empty account name")
    if not db.create_account(user, name):
        raise HTTPException(status_code=400, detail="Account already exists")
    db.update_account_access(user, name)
    return MessageResponse(message="created")


@router.delete("/{account_name}", response_model=MessageResponse)
def delete_account(account_name: str, user: str = Depends(get_current_user)):
    if not db.delete_account(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    return MessageResponse(message="deleted")


@router.post("/{account_name}/touch", response_model=MessageResponse)
def touch_account(account_name: str, user: str = Depends(get_current_user)):
    if not db.get_account_id(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    db.update_account_access(user, account_name)
    return MessageResponse(message="ok")


@router.get("/{account_name}/start-date")
def get_start_date(account_name: str, user: str = Depends(get_current_user)):
    fp = pe.compute_market_fingerprint()
    ctx = pe.get_market_context(fp)
    start = pe.get_acc_start_date(user, account_name, ctx.global_min_date)
    return {
        "start_date": start.isoformat(),
        "global_min_date": ctx.global_min_date.isoformat(),
        "global_max_date": ctx.global_max_date.isoformat(),
    }


@router.put("/{account_name}/start-date", response_model=MessageResponse)
def set_start_date(account_name: str, body: StartDateUpdate, user: str = Depends(get_current_user)):
    if not db.get_account_id(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    from datetime import date

    pe.save_acc_start_date(user, account_name, date.fromisoformat(body.start_date))
    pe.invalidate_user_snapshots(user)
    return MessageResponse(message="updated")
