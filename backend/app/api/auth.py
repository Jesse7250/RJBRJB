"""用户认证 API

提供：
- POST /api/auth/register  用户注册
- POST /api/auth/login     用户登录（OAuth2 Password Bearer）
"""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.services.auth import create_access_token, get_password_hash, verify_password
from app.services.database import create_user, get_user

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest):
    """用户注册"""
    if not payload.username or not payload.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名和密码不能为空",
        )
    if len(payload.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少 6 位",
        )

    existing = get_user(payload.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    hashed = get_password_hash(payload.password)
    create_user(payload.username, hashed)

    access_token = create_access_token(
        data={"sub": payload.username},
        expires_delta=timedelta(hours=24),
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        username=payload.username,
    )


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录"""
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(hours=24),
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        username=user["username"],
    )
