import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import APIRouter, Depends, HTTPException

import db_manager as db
from app.deps import get_current_user
from app.schemas.auth import MessageResponse
from app.schemas.trades import TradesPayload

router = APIRouter(prefix="/accounts/{account_name}/trades", tags=["trades"])

COLS = ["日期", "操作类型", "标的", "数量(股)", "成交单价(¥)", "实际结算总金额(¥)"]


@router.get("")
def get_trades(account_name: str, user: str = Depends(get_current_user)):
    if not db.get_account_id(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    df = db.get_trades(user, account_name)
    if df.empty:
        return {"trades": []}
    df = df.copy()
    df["日期"] = pd.to_datetime(df["日期"]).dt.strftime("%Y-%m-%d")
    return {"trades": df.replace({float("nan"): None}).to_dict(orient="records")}


@router.put("", response_model=MessageResponse)
def save_trades(account_name: str, body: TradesPayload, user: str = Depends(get_current_user)):
    if not db.get_account_id(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    df = pd.DataFrame(body.trades)
    for col in COLS:
        if col not in df.columns:
            df[col] = None
    df = df[COLS]
    db.save_trades(user, account_name, df)
    return MessageResponse(message="saved")
