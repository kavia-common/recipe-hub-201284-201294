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

    # Auth (scaffolding; actual auth implementation will evolve)
    auth_jwt_secret: str = Field(
        default="dev-only-secret",
        description=(
            "JWT secret for signing tokens. Must be overridden in production. "
            "For now, used only as scaffolding."
        ),
        alias="AUTH_JWT_SECRET",
    )
    auth_jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm identifier.",
        alias="AUTH_JWT_ALGORITHM",
    )


# PUBLIC_INTERFACE
@lru_cache
def get_settings() -> Settings:
    """Get cached Settings instance."""
    return Settings()
