"""Auth helpers — stdlib PBKDF2 password hashing + JWT tokens.

No compiled deps (avoids bcrypt build issues on Windows). PyJWT is pure Python.
Set JWT_SECRET in the environment for production.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api import db

_PBKDF2_ROUNDS = 200_000
_ALGO = "HS256"
_TOKEN_TTL_HOURS = 24 * 14  # 2 weeks


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "").strip()
    if secret:
        return secret
    # Dev fallback — stable per process so tokens survive reloads in one session.
    return "dev-insecure-secret-change-me"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split("$", 1)
        salt = bytes.fromhex(salt_hex)
    except (ValueError, AttributeError):
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS)
    return hmac.compare_digest(dk.hex(), dk_hex)


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=_TOKEN_TTL_HOURS)).timestamp()),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=_ALGO)


def _decode_token(token: str) -> int:
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[_ALGO])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session — please sign in again.",
        ) from exc


_bearer = HTTPBearer(auto_error=True)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict[str, Any]:
    user_id = _decode_token(creds.credentials)
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found.",
        )
    return user


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    """Strip sensitive fields before returning to the client."""
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user.get("name"),
        "created_at": user.get("created_at"),
    }
