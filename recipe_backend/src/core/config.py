from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Notes:
    - Do not hardcode secrets/config in code.
    - The orchestrator/user must provide required env vars (e.g., DATABASE_URL) in `.env`.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(default="Recipe Hub API", description="Human-friendly application name.")
    app_version: str = Field(default="0.1.0", description="Application version string.")

    # PUBLIC_INTERFACE
    database_url: str = Field(
        ...,
        description=(
            "PostgreSQL connection URL. Must be provided via env var DATABASE_URL "
            "(e.g., postgresql+asyncpg://user:pass@host:5432/dbname)."
        ),
        alias="DATABASE_URL",
    )

    # CORS
    cors_allow_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        description="List of allowed CORS origins.",
    )

    # Auth / JWT
    jwt_secret_key: str = Field(
        ...,
        description="Secret key for signing ACCESS tokens (JWT).",
        alias="JWT_SECRET_KEY",
    )
    jwt_refresh_secret_key: str = Field(
        ...,
        description="Secret key for signing REFRESH tokens (JWT).",
        alias="JWT_REFRESH_SECRET_KEY",
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm (e.g., HS256).",
        alias="ALGORITHM",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes.",
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_minutes: int = Field(
        default=60 * 24 * 7,
        description="Refresh token expiration in minutes.",
        alias="REFRESH_TOKEN_EXPIRE_MINUTES",
    )


# PUBLIC_INTERFACE
@lru_cache
def get_settings() -> Settings:
    """Get cached Settings instance."""
    return Settings()
