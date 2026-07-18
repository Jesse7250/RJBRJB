"""用户认证 API"""
from datetime import timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from app.services.auth import (
    blacklist_token,
    create_access_token,
    get_current_payload,
    get_current_user,
    get_password_hash,
    is_token_blacklisted,
    oauth2_scheme,
    require_user,
    verify_password,
)
from app.services.database import create_user, get_user

router = APIRouter()

RoleType = Literal["student", "teacher", "admin"]


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: RoleType = Field(default="student")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: RoleType


class MeResponse(BaseModel):
    username: str
    role: RoleType


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest):
    if not payload.username or not payload.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名和密码不能为空")
    if len(payload.password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码长度至少 6 位")
    if payload.role not in ("student", "teacher", "admin"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色无效")

    existing = get_user(payload.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

    create_user(payload.username, get_password_hash(payload.password), payload.role)
    access_token = create_access_token(
        data={"sub": payload.username, "role": payload.role},
        expires_delta=timedelta(hours=24),
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        username=payload.username,
        role=payload.role,
    )


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = user.get("role") or "student"
    access_token = create_access_token(
        data={"sub": user["username"], "role": role},
        expires_delta=timedelta(hours=24),
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        username=user["username"],
        role=role,
    )


@router.get("/me", response_model=MeResponse)
async def me(payload: dict = Depends(get_current_payload)):
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    return MeResponse(
        username=payload.get("sub", ""),
        role=payload.get("role") or "student",
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: str = Depends(get_current_user), payload: dict = Depends(get_current_payload)):
    if not current_user or not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    role = payload.get("role") or "student"
    access_token = create_access_token(
        data={"sub": current_user, "role": role},
        expires_delta=timedelta(hours=24),
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        username=current_user,
        role=role,
    )


@router.post("/logout")
async def logout(token: Optional[str] = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供 Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if is_token_blacklisted(token):
        return {"success": True, "message": "Token 已登出"}
    blacklist_token(token)
    return {"success": True, "message": "登出成功"}

