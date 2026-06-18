import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import APIRouter, Depends, HTTPException, Response, status

import db_manager as db
from app.config import settings
from app.core.security import create_access_token
from app.deps import get_current_user
from app.schemas.auth import LoginRequest, MessageResponse, PasswordChangeRequest, RegisterRequest, UserResponse
from app.services import prefs_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path=settings.mount_path,
    )


@router.post("/login", response_model=UserResponse)
def login(body: LoginRequest, response: Response):
    if not db.verify_user(body.username, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    prefs_service.merge_on_login(body.username)
    token = create_access_token(body.username)
    _set_cookie(response, token)
    return UserResponse(username=body.username)


@router.post("/register", response_model=MessageResponse)
def register(body: RegisterRequest):
    ok, msg = db.register_user(body.username, body.password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return MessageResponse(message=msg)


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response):
    response.delete_cookie(settings.cookie_name, path=settings.mount_path)
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserResponse)
def me(user: str = Depends(get_current_user)):
    return UserResponse(username=user)


@router.put("/password", response_model=MessageResponse)
def change_password(body: PasswordChangeRequest, user: str = Depends(get_current_user)):
    if not db.update_password(user, body.old_password, body.new_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password change failed")
    return MessageResponse(message="Password updated")
