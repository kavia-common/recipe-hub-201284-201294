from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserRead(BaseModel):
    """Public user representation."""

    id: str = Field(..., description="User identifier (UUID string).")
    email: str = Field(..., description="User email address.")
    created_at: datetime = Field(..., description="Timestamp when the user was created.")
    updated_at: datetime = Field(..., description="Timestamp when the user was last updated.")


class UserCreate(BaseModel):
    """User creation payload (scaffolding)."""

    id: str = Field(..., description="User identifier (UUID string).")
    email: str = Field(..., description="User email address.")
