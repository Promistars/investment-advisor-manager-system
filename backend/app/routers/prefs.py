from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import get_current_user, get_optional_user
from app.services import prefs_service

router = APIRouter(prefix="/prefs", tags=["prefs"])


class PrefsPayload(BaseModel):
    prefs: dict[str, Any]


@router.get("")
def read_prefs(user: str | None = Depends(get_optional_user)):
    return prefs_service.get_user_prefs(user)


@router.put("")
def write_prefs(body: PrefsPayload, user: str = Depends(get_current_user)):
    prefs_service.save_user_prefs(user, body.prefs)
    return prefs_service.get_user_prefs(user)


@router.post("/reset")
def reset_prefs(user: str = Depends(get_current_user)):
    prefs_service.reset_user_prefs(user)
    return prefs_service.get_user_prefs(user)
