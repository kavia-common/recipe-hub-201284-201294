from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRead(BaseModel):
    """Public user representation."""

    id: str = Field(..., description="User identifier (UUID string).")
    email: EmailStr = Field(..., description="User email address.")
    username: str | None = Field(default=None, description="Optional public username.")
    is_active: bool = Field(..., description="Whether the user is active.")
    created_at: datetime = Field(..., description="Timestamp when the user was created.")
    updated_at: datetime = Field(..., description="Timestamp when the user was last updated.")


class RegisterRequest(BaseModel):
    """Registration payload."""

    email: EmailStr = Field(..., description="User email address.")
    password: str = Field(..., min_length=8, description="User password (min 8 characters).")
    username: str | None = Field(default=None, max_length=50, description="Optional username.")


class LoginRequest(BaseModel):
    """Login payload."""

    email: EmailStr = Field(..., description="User email address.")
    password: str = Field(..., description="User password.")


class TokenPair(BaseModel):
    """Access + refresh token pair."""

    access_token: str = Field(..., description="Short-lived access token (JWT).")
    refresh_token: str = Field(..., description="Long-lived refresh token (JWT).")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer').")
    expires_in: int = Field(..., description="Access token lifetime in seconds.")


class RefreshRequest(BaseModel):
    """Refresh payload."""

    refresh_token: str = Field(..., description="Refresh token (JWT).")
