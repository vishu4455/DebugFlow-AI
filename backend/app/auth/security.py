"""
auth/security.py — JWT creation/validation, password hashing, API key support.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── Roles ────────────────────────────────────────────────────────────────────

ROLES = {
    settings.ADMIN_USERNAME: "admin",
    settings.DEMO_USERNAME:  "user",
}

# In-memory user store (replace with DB table in real production)
USERS: dict[str, dict] = {
    settings.ADMIN_USERNAME: {
        "username": settings.ADMIN_USERNAME,
        "hashed_password": pwd_context.hash(settings.ADMIN_PASSWORD.encode("utf-8")[:72].decode("utf-8", "ignore")),
        "role": "admin",
        "disabled": False,
    },
    settings.DEMO_USERNAME: {
        "username": settings.DEMO_USERNAME,
        "hashed_password": pwd_context.hash(settings.DEMO_PASSWORD),
        "role": "user",
        "disabled": False,
    },
}

# Valid API keys set
_API_KEY_SET: set[str] = set(
    k.strip() for k in settings.API_KEYS.split(",") if k.strip()
)


# ─── Password helpers ─────────────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_user(username: str) -> Optional[dict]:
    return USERS.get(username)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = get_user(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


# ─── JWT ─────────────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """Raises JWTError on invalid/expired token."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ─── API Key ──────────────────────────────────────────────────────────────────

def validate_api_key(key: str) -> bool:
    return key in _API_KEY_SET


def api_key_to_user(key: str) -> dict:
    """Return a synthetic user dict for an API key caller."""
    return {
        "username": f"apikey:{hashlib.sha256(key.encode()).hexdigest()[:8]}",
        "role": "user",
        "disabled": False,
    }
