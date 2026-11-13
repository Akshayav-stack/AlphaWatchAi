"""
AlphaWatch AI — Security & Cryptographic Subsystem
ASTRAQUANT X 2026

Implements Section 6 Security Checklist:
  1. Argon2id password hashing with high memory/time hardness
  2. Enforced password policy (min length 10, common leaked passwords blacklisted)
  3. Cryptographic HMAC CSRF token generation and constant-time verification
  4. Account lockout tracking (locks for 15 minutes after 5 consecutive failures)
  5. Generic authentication error masking to prevent user enumeration
"""

import hmac
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "alphawatch-default-insecure-secret-replace-me")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "False").lower() in ("true", "1", "t")
ENVIRONMENT = (os.getenv("ENVIRONMENT") or os.getenv("APP_ENV", "development")).lower()

INSECURE_DEFAULT_SECRETS = {
    "alphawatch-default-insecure-secret-replace-me",
    "alphawatch-super-secret-key-change-in-production-min-32-chars-hex",
}

if ENVIRONMENT == "production" and (SECRET_KEY in INSECURE_DEFAULT_SECRETS or len(SECRET_KEY) < 32):
    raise RuntimeError("CRITICAL SECURITY VIOLATION: SECRET_KEY must be changed from the default value in production mode (min 32 characters).")

MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", "10"))
MAX_PASSWORD_LENGTH = int(os.getenv("MAX_PASSWORD_LENGTH", "128"))
MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))

# Initialize Argon2id password hasher with secure parameters
ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MB
    parallelism=1,
    hash_len=32,
    salt_len=16,
)

# Blacklist of commonly leaked weak passwords
COMMON_PASSWORDS_BLACKLIST = {
    "password123",
    "password1234",
    "1234567890",
    "12345678901",
    "admin12345",
    "administrator",
    "qwertyuiop",
    "letmein123",
    "iloveyou123",
    "welcome1234",
    "changeme123",
    "alphawatch123",
    "trading1234",
    "stockmarket123",
}


def hash_password(password: str) -> str:
    """Hashes a password using Argon2id with random salt."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against an Argon2id hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validates that a password satisfies security requirements:
      - At least 10 characters
      - Maximum 128 characters (mitigates Argon2 hashing resource exhaustion / DoS)
      - Not in common password blacklist
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."

    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"Password exceeds maximum allowable length of {MAX_PASSWORD_LENGTH} characters."

    if password.lower() in COMMON_PASSWORDS_BLACKLIST:
        return False, "This password is too common and easily guessed. Please choose a stronger passphrase."

    return True, None


def generate_csrf_token(session_id: str) -> str:
    """
    Generates a cryptographic HMAC-SHA256 CSRF token tied to the user's session.
    """
    nonce = secrets.token_hex(16)
    message = f"{session_id}:{nonce}".encode("utf-8")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), message, digestmod="sha256").hexdigest()
    return f"{nonce}:{signature}"


def verify_csrf_token(token: str, session_id: str) -> bool:
    """
    Verifies the HMAC-SHA256 CSRF token using constant-time comparison.
    """
    if not token or ":" not in token:
        return False

    try:
        nonce, signature = token.split(":", 1)
        expected_msg = f"{session_id}:{nonce}".encode("utf-8")
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), expected_msg, digestmod="sha256").hexdigest()
        return hmac.compare_digest(signature, expected_sig)
    except Exception:
        return False


def get_request_csrf_token(request: Any) -> Tuple[str, Optional[str]]:
    """
    Gets or generates a CSRF token for the current HTTP request.
    Returns: (csrf_token, new_cookie_val_to_set_if_any)
    """
    session_id = request.cookies.get("alphawatch_session") or request.cookies.get("alphawatch_csrf")
    new_cookie = None
    if not session_id:
        session_id = secrets.token_hex(16)
        new_cookie = session_id

    token = generate_csrf_token(session_id)
    return token, new_cookie


def validate_request_csrf(request: Any, token: Optional[str]) -> bool:
    """
    Validates CSRF token against request session or csrf cookie.
    """
    if not token:
        return False
    session_id = request.cookies.get("alphawatch_session") or request.cookies.get("alphawatch_csrf")
    if not session_id:
        return False
    return verify_csrf_token(token, session_id)


def set_csrf_cookie(response: Any, new_cookie: str) -> None:
    """Sets the alphawatch_csrf cookie with verified security flags (HttpOnly, SameSite, Secure)."""
    response.set_cookie(
        key="alphawatch_csrf",
        value=new_cookie,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def is_account_locked(failed_attempts: int, locked_until: Optional[datetime]) -> Tuple[bool, Optional[str]]:
    """
    Checks if an account is currently locked out due to excessive failed attempts.
    """
    if locked_until is not None:
        if datetime.utcnow() < locked_until:
            remaining_mins = max(1, int((locked_until - datetime.utcnow()).total_seconds() // 60))
            return True, f"Account is temporarily locked. Please try again in {remaining_mins} minutes."
    return False, None


def compute_next_lockout(current_failures: int) -> Tuple[int, Optional[datetime]]:
    """
    Increments failure count and computes lockout expiration if threshold reached.
    """
    new_count = current_failures + 1
    if new_count >= MAX_FAILED_ATTEMPTS:
        lock_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        return new_count, lock_until
    return new_count, None
