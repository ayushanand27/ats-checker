"""Authentication endpoints — register, login, current user."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, status

from api import db
from api.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    public_user,
    verify_password,
)
from api.schemas import AuthResponse, LoginRequest, PublicUser, RegisterRequest

router = APIRouter()

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest) -> AuthResponse:
    email = body.email.lower().strip()
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Enter a valid email address.")
    if db.get_user_by_email(email):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = db.create_user(email, hash_password(body.password), (body.name or "").strip() or None)
    token = create_access_token(user["id"])
    return AuthResponse(access_token=token, user=PublicUser(**public_user(user)))


@router.post("/auth/login", response_model=AuthResponse)
async def login(body: LoginRequest) -> AuthResponse:
    user = db.get_user_by_email(body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    token = create_access_token(user["id"])
    return AuthResponse(access_token=token, user=PublicUser(**public_user(user)))


@router.get("/auth/me", response_model=PublicUser)
async def me(user: dict = Depends(get_current_user)) -> PublicUser:
    return PublicUser(**public_user(user))
