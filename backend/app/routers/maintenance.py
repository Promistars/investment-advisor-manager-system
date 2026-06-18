import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import APIRouter, Depends

import portfolio_engine as pe
from app.deps import get_current_user
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.post("/refresh-pnl", response_model=MessageResponse)
def refresh_pnl(user: str = Depends(get_current_user)):
    pe.invalidate_user_snapshots(user)
    accounts = __import__("db_manager").get_user_accounts(user)
    if accounts:
        pe.batch_account_snapshots(user, [a["name"] for a in accounts])
    return MessageResponse(message="PnL cache refreshed")


@router.post("/reset-prefs", response_model=MessageResponse)
def reset_prefs(user: str = Depends(get_current_user)):
    from app.services import prefs_service

    prefs_service.reset_user_prefs(user)
    return MessageResponse(message="Preferences reset")
