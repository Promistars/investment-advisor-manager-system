import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import APIRouter, Depends, HTTPException, Query

import db_manager as db
from app.deps import get_current_user, get_optional_user
from app.services import analytics_service as svc

router = APIRouter(tags=["analytics"])


@router.get("/accounts/{account_name}/dashboard")
def account_dashboard(
    account_name: str,
    view: str = Query("monthly"),
    custom_start: str | None = None,
    custom_end: str | None = None,
    user: str = Depends(get_current_user),
):
    if not db.get_account_id(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    cs = date.fromisoformat(custom_start) if custom_start else None
    ce = date.fromisoformat(custom_end) if custom_end else None
    vm = view if view in ("monthly", "quarterly", "yearly", "custom") else "monthly"
    try:
        return svc.compute_dashboard(
            user,
            account_name,
            view=vm,  # type: ignore[arg-type]
            client_mode=False,
            custom_start=cs,
            custom_end=ce,
            include_admin=True,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/public/client/{username}/{account_name}/dashboard")
def public_client_dashboard(
    username: str,
    account_name: str,
    view: str = Query("monthly"),
    custom_start: str | None = None,
    custom_end: str | None = None,
):
    if not db.get_account_id(username, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    cs = date.fromisoformat(custom_start) if custom_start else None
    ce = date.fromisoformat(custom_end) if custom_end else None
    vm = view if view in ("monthly", "quarterly", "yearly", "custom") else "monthly"
    try:
        return svc.compute_dashboard(
            username,
            account_name,
            view=vm,  # type: ignore[arg-type]
            client_mode=True,
            custom_start=cs,
            custom_end=ce,
            include_admin=False,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
