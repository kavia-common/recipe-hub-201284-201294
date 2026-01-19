from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Header, HTTPException, status


@dataclass(frozen=True)
class CurrentUser:
    """Represents the authenticated user extracted from the request.

    This is scaffolding to be replaced by a real JWT/session implementation.
    """

    id: str
    email: Optional[str] = None


# PUBLIC_INTERFACE
async def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    """Get the current user from an Authorization header.

    Currently supports a simple placeholder:
    - If Authorization is missing -> 401
    - If present, expects "Bearer <user_id>" and returns user_id as CurrentUser.id

    This is intentionally minimal scaffolding until real auth is implemented.
    """
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")

    user_id = parts[1].strip()
    return CurrentUser(id=user_id)
