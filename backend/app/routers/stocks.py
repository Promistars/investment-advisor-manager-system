import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import db_manager as db
import portfolio_engine as pe
from app.deps import get_current_user
from app.schemas.auth import MessageResponse
from iams_network import apply_project_network_env, eastmoney_kline_available

apply_project_network_env()
from stock_fetch import ingest_new_stock

router = APIRouter(prefix="/stocks", tags=["stocks"])


class IngestRequest(BaseModel):
    name: str
    force: bool = False


@router.get("")
def list_stocks(user: str = Depends(get_current_user)):
    _, _, names = pe.discover_stock_info()
    return {"stocks": names, "eastmoney_kline": eastmoney_kline_available()}


@router.post("/ingest", response_model=MessageResponse)
def ingest_stock(body: IngestRequest, user: str = Depends(get_current_user)):
    import os

    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Empty name")
    csv_path = os.path.join(pe.DATA_DIR, f"{name}.csv")
    if os.path.exists(csv_path) and not body.force:
        raise HTTPException(status_code=400, detail=f"{name} already exists")
    ok, msg = ingest_new_stock(name)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    pe.invalidate_user_snapshots(user)
    return MessageResponse(message=msg)
