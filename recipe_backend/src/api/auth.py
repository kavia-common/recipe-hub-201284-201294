from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    normalize_email,
    verify_password,
)
from src.core.config import get_settings
from src.core.db import get_db_session
from src.domain.users.models import User
from src.domain.users.schemas import LoginRequest, RefreshRequest, TokenPair, UserRead, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with a unique (case-insensitive) email and password.",
    operation_id="auth_register",
)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db_session)) -> UserRead:
    """Register endpoint."""
    email = normalize_email(payload.email)

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    user = User(
        id=str(uuid.uuid4()),
        email=email,
        username=payload.username.strip() if payload.username else None,
        hashed_password=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserRead(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Login and get token pair",
    description="Validate credentials and return an access+refresh token pair.",
    operation_id="auth_login",
)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db_session)) -> TokenPair:
    """Login endpoint."""
    settings = get_settings()
    email = normalize_email(payload.email)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_access_token(
        subject=user.id,
        email=user.email,
        expires_minutes=settings.access_token_expire_minutes,
    )
    refresh_token = create_refresh_token(
        subject=user.id,
        email=user.email,
        expires_minutes=settings.refresh_token_expire_minutes,
    )

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=int(timedelta(minutes=settings.access_token_expire_minutes).total_seconds()),
    )


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Refresh token pair",
    description="Validate refresh token and issue a new access+refresh token pair.",
    operation_id="auth_refresh",
)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db_session)) -> TokenPair:
    """Refresh endpoint."""
    from jose import JWTError  # local import to keep core/auth.py minimal
    from src.core.auth import decode_refresh_token

    settings = get_settings()

    try:
        token_payload = decode_refresh_token(payload.refresh_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = token_payload.get("sub")
    email = token_payload.get("email")
    if not user_id or not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == str(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    access_token = create_access_token(
        subject=user.id,
        email=user.email,
        expires_minutes=settings.access_token_expire_minutes,
    )
    refresh_token = create_refresh_token(
        subject=user.id,
        email=user.email,
        expires_minutes=settings.refresh_token_expire_minutes,
    )

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=int(timedelta(minutes=settings.access_token_expire_minutes).total_seconds()),
    )


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user",
    description="Return the current authenticated user derived from the Bearer access token.",
    operation_id="auth_me",
)
async def me(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserRead:
    """Return current user."""
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return UserRead(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
