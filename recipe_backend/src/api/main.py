from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.db import get_db_session


# PUBLIC_INTERFACE
def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    openapi_tags = [
        {"name": "health", "description": "Service and dependency health checks."},
    ]

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Recipe Hub backend API. Provides endpoints for authentication, recipes, favorites, "
            "comments, ratings, and user profiles."
        ),
        openapi_tags=openapi_tags,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get(
        "/health",
        tags=["health"],
        summary="Health check",
        description="Returns API liveness and basic database connectivity information.",
        operation_id="health_check",
    )
    async def health_check(db: AsyncSession = Depends(get_db_session)):
        """Health check endpoint.

        Performs a lightweight `SELECT 1` against the database to validate wiring.

        Returns:
            JSON object with service status and db status.
        """
        db_ok = True
        try:
            await db.execute(text("SELECT 1"))
        except Exception:
            db_ok = False

        return {"status": "ok", "db": "ok" if db_ok else "error"}

    # Backward compatibility with old "/" health check
    @app.get(
        "/",
        tags=["health"],
        summary="Legacy health check",
        description="Legacy health endpoint (kept for compatibility). Prefer /health.",
        operation_id="legacy_health_check",
    )
    async def legacy_health_check():
        """Legacy health check endpoint."""
        return {"message": "Healthy"}

    return app


app = create_app()
