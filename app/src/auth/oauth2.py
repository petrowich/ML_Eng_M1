import services.repository.user
from datetime import datetime, timedelta, timezone
from typing import Optional, cast
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datasource.config import get_settings
from datasource.database import get_session
from models.user import User


settings = get_settings()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = settings.SECRET_KEY or ''
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(login: str, expires_delta: timedelta = None) -> str:
   expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
   payload = {"login": login, "exp": expire.timestamp()}
   return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_token_from_cookie(request: Request) -> str | None:
    raw = request.cookies.get(settings.auth_token_cookie_name())
    if not raw:
        return None
    if raw.startswith("Bearer "):
        return raw.split("Bearer ", 1)[1].strip()
    return raw.strip()

def get_current_user(request: Request, session: Session = Depends(get_session)) -> User:
    token = get_token_from_cookie(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login: Optional[str] = payload.get("login")
        if not login:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = services.repository.user.get_user_by_login(login, session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user

def verify_access_token(token: str) -> dict:
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        expire = cast(float, data.get("exp"))
        if expire is None:
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access token supplied"
            )
        if datetime.now(timezone.utc) > datetime.fromtimestamp(expire, timezone.utc):
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token expired!"
            )
        return data
    except JWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")
