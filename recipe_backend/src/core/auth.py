from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.db import get_db_session
from src.domain.users.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    scheme_name="JWT",
    description="OAuth2 password flow using a JWT access token. Use: `Authorization: Bearer <access_token>`.",
)


@dataclass(frozen=True)
class CurrentUser:
    """Represents the authenticated user extracted from the request."""

    id: str
    email: Optional[str] = None


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(*, subject: str, email: str, expires_minutes: int) -> str:
    """Create a signed JWT access token."""
    settings = get_settings()
    expire = _utcnow() + timedelta(minutes=expires_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "email": email,
        "type": "access",
        "exp": expire,
        "iat": _utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.algorithm)


def create_refresh_token(*, subject: str, email: str, expires_minutes: int) -> str:
    """Create a signed JWT refresh token."""
    settings = get_settings()
    expire = _utcnow() + timedelta(minutes=expires_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "email": email,
        "type": "refresh",
        "exp": expire,
        "iat": _utcnow(),
    }
    return jwt.encode(payload, settings.jwt_refresh_secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an access token."""
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.algorithm])


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decode and validate a refresh token."""
    settings = get_settings()
    return jwt.decode(token, settings.jwt_refresh_secret_key, algorithms=[settings.algorithm])


# PUBLIC_INTERFACE
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> CurrentUser:
    """Resolve the current user from a Bearer access token.

    Args:
        token: Access token from the Authorization header.
        db: Database session.

    Returns:
        CurrentUser containing the authenticated user's id and email.

    Raises:
        HTTPException: 401 if token is missing/invalid/expired, or user not found/inactive.
    """
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == str(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return CurrentUser(id=user.id, email=user.email)


# PUBLIC_INTERFACE
def normalize_email(email: str) -> str:
    """Normalize email for case-insensitive auth."""
    return _normalize_email(email)
