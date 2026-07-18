"""认证与授权服务（AuthN / AuthZ）"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

_blacklisted_tokens: set[str] = set()


def blacklist_token(token: str) -> None:
    _blacklisted_tokens.add(token)


def is_token_blacklisted(token: str) -> bool:
    return token in _blacklisted_tokens


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=24))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> Optional[dict]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        return None


async def get_current_payload(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[dict]:
    if token is None or is_token_blacklisted(token):
        return None
    return decode_access_token(token)


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    payload = await get_current_payload(token)
    if not payload:
        return None
    return payload.get("sub")


async def get_current_role(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    payload = await get_current_payload(token)
    if not payload:
        return None
    return payload.get("role")


async def require_user(token: Optional[str] = Depends(oauth2_scheme)) -> str:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已登出",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已过期或 token 无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 无效")
    return username


def require_roles(*allowed_roles: str):
    async def dependency(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="请先登录",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 已登出",
                headers={"WWW-Authenticate": "Bearer"},
            )
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="登录已过期或 token 无效",
                headers={"WWW-Authenticate": "Bearer"},
            )
        role = payload.get("role")
        if role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")
        return payload

    return dependency

