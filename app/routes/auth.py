"""
AlphaWatch AI — Authentication & Identity Route Handlers
ASTRAQUANT X 2026

Security Compliance:
  - Argon2id password hashing
  - Minimum password length 10 + common password blacklist
  - Signed HttpOnly SameSite=Lax session cookies
  - Account lockout tracking (locks after 5 failures)
  - Generic authentication errors to prevent user enumeration
  - Mandatory consent acknowledgment
  - Right to Erasure / Cascading account deletion
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import clear_session_cookie, get_current_user, set_session_cookie
from app.db import get_db
from app.limiter import limiter
from app.models_db import User
from app.security import (
    compute_next_lockout,
    get_request_csrf_token,
    hash_password,
    is_account_locked,
    set_csrf_cookie,
    validate_password_strength,
    validate_request_csrf,
    verify_password,
)

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request, response: Response, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse(url="/dashboard" if user.is_onboarded else "/onboarding", status_code=303)

    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="auth/register.html",
        context={
            "current_user": None,
            "csrf_token": csrf_token,
            "error_msg": None,
            "active_page": "register",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.post("/register")
@limiter.limit("3/minute")
def register_submit(
    request: Request,
    response: Response,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    consent: Optional[str] = Form(None),
    csrf_token: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    # 1. CSRF Verification
    if not validate_request_csrf(request, csrf_token):
        csrf_tok, new_cookie = get_request_csrf_token(request)
        resp = templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={
                "current_user": None,
                "csrf_token": csrf_tok,
                "error_msg": "Security validation failed. Please refresh and try again.",
                "active_page": "register",
            },
            status_code=400,
        )
        if new_cookie:
            set_csrf_cookie(resp, new_cookie)
        return resp

    # 2. Mandatory Consent Check
    if not consent:
        csrf_tok, _ = get_request_csrf_token(request)
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={
                "current_user": None,
                "csrf_token": csrf_tok,
                "error_msg": "You must acknowledge that AlphaWatch AI is an educational research platform.",
                "active_page": "register",
            },
            status_code=400,
        )

    # 3. Input Validation: Name and Email sanitization
    clean_name = name.strip()
    clean_email = email.strip().lower()

    if len(clean_name) < 2 or len(clean_name) > 120:
        csrf_tok, _ = get_request_csrf_token(request)
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={
                "current_user": None,
                "csrf_token": csrf_tok,
                "error_msg": "Full name must be between 2 and 120 characters.",
                "active_page": "register",
            },
            status_code=400,
        )

    if len(clean_email) > 255 or "@" not in clean_email or "." not in clean_email.split("@")[-1]:
        csrf_tok, _ = get_request_csrf_token(request)
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={
                "current_user": None,
                "csrf_token": csrf_tok,
                "error_msg": "Please provide a valid email address.",
                "active_page": "register",
            },
            status_code=400,
        )

    # 4. Password Confirmation
    if password != confirm_password:
        csrf_tok, _ = get_request_csrf_token(request)
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={
                "current_user": None,
                "csrf_token": csrf_tok,
                "error_msg": "Passwords do not match.",
                "active_page": "register",
            },
            status_code=400,
        )

    # 5. Password Policy (Min length 10, Max length 128, Blacklist)
    is_valid, err = validate_password_strength(password)
    if not is_valid:
        csrf_tok, _ = get_request_csrf_token(request)
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={
                "current_user": None,
                "csrf_token": csrf_tok,
                "error_msg": err,
                "active_page": "register",
            },
            status_code=400,
        )

    # 6. Unique Email Check
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        csrf_tok, _ = get_request_csrf_token(request)
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={
                "current_user": None,
                "csrf_token": csrf_tok,
                "error_msg": "An account with this email address already exists. Please sign in.",
                "active_page": "register",
            },
            status_code=400,
        )

    # 7. Create User with Argon2id Hash
    pw_hash = hash_password(password)
    new_user = User(
        name=clean_name,
        email=clean_email,
        password_hash=pw_hash,
        consent_given=True,
        is_onboarded=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 7. Establish Session & Route to Onboarding
    redirect_resp = RedirectResponse(url="/onboarding", status_code=status.HTTP_303_SEE_OTHER)
    set_session_cookie(redirect_resp, new_user.id)
    return redirect_resp


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request, response: Response, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse(url="/dashboard" if user.is_onboarded else "/onboarding", status_code=303)

    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={
            "current_user": None,
            "csrf_token": csrf_token,
            "error_msg": None,
            "active_page": "login",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.post("/login")
@limiter.limit("5/minute")
def login_submit(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    csrf_token: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    # 1. CSRF Verification
    if not validate_request_csrf(request, csrf_token):
        csrf_tok, _ = get_request_csrf_token(request)
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={
                "current_user": None,
                "csrf_token": csrf_tok,
                "error_msg": "Security validation failed. Please refresh and try again.",
                "active_page": "login",
            },
            status_code=400,
        )

    clean_email = email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()

    # 2. Account Lockout Check
    if user and user.locked_until:
        is_locked, lock_msg = is_account_locked(user.failed_login_attempts, user.locked_until)
        if is_locked:
            csrf_tok, _ = get_request_csrf_token(request)
            return templates.TemplateResponse(
                request=request,
                name="auth/login.html",
                context={
                    "current_user": None,
                    "csrf_token": csrf_tok,
                    "error_msg": lock_msg,
                    "active_page": "login",
                },
                status_code=403,
            )
        else:
            # Lockout expired
            user.locked_until = None
            user.failed_login_attempts = 0
            db.commit()

    # 3. Credential Verification
    if not user or not verify_password(password, user.password_hash):
        if user:
            new_failures, lock_until = compute_next_lockout(user.failed_login_attempts)
            user.failed_login_attempts = new_failures
            user.locked_until = lock_until
            db.commit()
            if lock_until:
                err_msg = "Too many failed attempts. Account locked for 15 minutes."
            else:
                err_msg = "Invalid email or password."
        else:
            err_msg = "Invalid email or password."

        csrf_tok, _ = get_request_csrf_token(request)
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={
                "current_user": None,
                "csrf_token": csrf_tok,
                "error_msg": err_msg,
                "active_page": "login",
            },
            status_code=401,
        )

    # 4. Successful Login: Reset Lockout Counters
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    # 5. Route to Onboarding on first login, otherwise Dashboard
    dest_url = "/dashboard" if user.is_onboarded else "/onboarding"
    redirect_resp = RedirectResponse(url=dest_url, status_code=status.HTTP_303_SEE_OTHER)
    set_session_cookie(redirect_resp, user.id)
    return redirect_resp


@router.post("/logout")
def logout(request: Request, csrf_token: Optional[str] = Form(None)):
    if not validate_request_csrf(request, csrf_token):
        raise HTTPException(status_code=400, detail="Security validation failed: Invalid CSRF token")
    redirect_resp = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    clear_session_cookie(redirect_resp)
    return redirect_resp


@router.post("/delete-account")
def delete_account(
    request: Request,
    csrf_token: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if not validate_request_csrf(request, csrf_token):
        raise HTTPException(status_code=400, detail="Invalid CSRF token")

    # Cascading permanent delete (Right to Erasure compliance)
    db.delete(user)
    db.commit()

    redirect_resp = RedirectResponse(url="/?deleted=1", status_code=status.HTTP_303_SEE_OTHER)
    clear_session_cookie(redirect_resp)
    return redirect_resp
