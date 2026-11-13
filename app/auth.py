"""
AlphaWatch AI — Session Management & Authentication Dependency
ASTRAQUANT X 2026

Manages signed, HttpOnly, SameSite=Lax session cookies via itsdangerous.
Provides get_current_user and login_required FastAPI dependencies.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models_db import User

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "alphawatch-default-insecure-secret-replace-me")
COOKIE_NAME = "alphawatch_session"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "False").lower() in ("true", "1", "t")
SESSION_MAX_AGE = int(os.getenv("SESSION_MAX_AGE_SECONDS", "86400"))
ENVIRONMENT = (os.getenv("ENVIRONMENT") or os.getenv("APP_ENV", "development")).lower()

INSECURE_DEFAULT_SECRETS = {
    "alphawatch-default-insecure-secret-replace-me",
    "alphawatch-super-secret-key-change-in-production-min-32-chars-hex",
}

if ENVIRONMENT == "production" and (SECRET_KEY in INSECURE_DEFAULT_SECRETS or len(SECRET_KEY) < 32):
    raise RuntimeError("CRITICAL SECURITY VIOLATION: SECRET_KEY must be changed from the default value in production mode (min 32 characters).")

serializer = URLSafeTimedSerializer(SECRET_KEY, salt="alphawatch_session_salt")


def create_session_token(user_id: int) -> str:
    """Creates a cryptographically signed session token containing user_id."""
    return serializer.dumps({"user_id": user_id})


def decode_session_token(token: str) -> Optional[int]:
    """Decodes and verifies a signed session token. Returns user_id if valid."""
    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
        return data.get("user_id")
    except (BadSignature, SignatureExpired):
        return None
    except Exception:
        return None


def set_session_cookie(response: Response, user_id: int) -> None:
    """Sets a signed, HttpOnly, SameSite=Lax cookie on the response."""
    token = create_session_token(user_id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    """Deletes both session and CSRF cookies from the browser to ensure clean logout."""
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )
    response.delete_cookie(
        key="alphawatch_csrf",
        path="/",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    FastAPI dependency that extracts and verifies the user from session cookie.
    Returns User instance or None if not logged in.
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None

    user_id = decode_session_token(token)
    if not user_id:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    return user


def login_required(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency that enforces authentication.
    Redirects unauthenticated browser requests to /auth/login.
    """
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/auth/login"},
            detail="Authentication required",
        )
    return user
