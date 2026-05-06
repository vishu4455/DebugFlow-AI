"""
auth/dependencies.py — FastAPI dependency functions for route protection.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from jose import JWTError

from app.auth.security import decode_token, validate_api_key, api_key_to_user, get_user

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    bearer: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    api_key: str | None = Security(api_key_header),
) -> dict:
    """
    Accepts EITHER a Bearer JWT OR an X-API-Key header.
    Raises 401 if neither is present or valid.
    """
    # ── API Key path ──────────────────────────────────────────────────────────
    if api_key:
        if validate_api_key(api_key):
            return api_key_to_user(api_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # ── JWT Bearer path ───────────────────────────────────────────────────────
    if bearer is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated — provide Bearer token or X-API-Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(bearer.credentials)
        username: str = payload.get("sub", "")
        if not username:
            raise ValueError("empty sub")
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user(username)
    if user is None or user.get("disabled"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )
    return user


def require_role(*roles: str):
    """Factory: returns a dependency that enforces one of the given roles."""
    async def _check(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {' | '.join(roles)}",
            )
        return current_user
    return _check


# Convenience pre-built deps
require_user  = Depends(get_current_user)
require_admin = Depends(require_role("admin"))
