import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    token: str | None = Cookie(default=None, alias="iams_token"),
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    raw = token or (creds.credentials if creds else None)
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    username = decode_access_token(raw)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return username


def get_optional_user(
    token: str | None = Cookie(default=None, alias="iams_token"),
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str | None:
    raw = token or (creds.credentials if creds else None)
    if not raw:
        return None
    return decode_access_token(raw)
