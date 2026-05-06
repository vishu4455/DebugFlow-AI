"""
routers/auth.py — Login, token refresh, current user endpoints.
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.auth.security import authenticate_user, create_access_token
from app.auth.dependencies import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    role: str
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=Token)
async def login(form: LoginRequest):
    """
    Exchange username + password for a JWT access token.
    Also accepts OAuth2 form-encoded (for Swagger UI).
    """
    user = authenticate_user(form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=expire_minutes),
    )
    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=expire_minutes * 60,
        role=user["role"],
        username=user["username"],
    )


@router.post("/login/form", response_model=Token, include_in_schema=False)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 password form — used by Swagger /docs Authorize button."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user["role"],
        username=user["username"],
    )


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "role": current_user.get("role", "user"),
    }
