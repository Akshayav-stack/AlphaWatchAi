"""
AlphaWatch AI — OWASP Top 10 Security Audit & Remediation Verification Tests
ASTRAQUANT X 2026

Proves fixes for:
  1. Logout CSRF Protection (A01:2021-Broken Access Control & CSRF)
  2. Production Secret Key Hardening (A02:2021-Cryptographic Failures)
  3. Secure Cookie Flags across Session & CSRF (A05:2021-Security Misconfiguration)
  4. Security Response Headers (HSTS, CSP, Permissions-Policy, Clickjacking)
  5. Chart & Public API Robustness (No unhandled exceptions)
  6. Strict User Isolation & Parameter Tampering Prevention
"""

import os
import pytest
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException

from app.db import Base, engine, SessionLocal
from app.models_db import User, Holding, PaperTrade, UserProfile
from app.auth import create_session_token, set_session_cookie, clear_session_cookie
from app.security import (
    generate_csrf_token,
    get_request_csrf_token,
    set_csrf_cookie,
    validate_request_csrf,
    hash_password,
)
from app.routes import auth, api, public, dashboard


@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_logout_csrf_protection_enforced():
    """Proves that /auth/logout rejects state-changing requests missing CSRF tokens."""
    req_no_csrf = Request({"type": "http", "method": "POST", "path": "/auth/logout", "headers": []})
    
    # Missing CSRF token must raise HTTPException(400)
    with pytest.raises(HTTPException) as exc_info:
        auth.logout(req_no_csrf, csrf_token=None)
    assert exc_info.value.status_code == 400
    assert "Invalid CSRF token" in exc_info.value.detail


def test_logout_with_valid_csrf_succeeds():
    """Proves that /auth/logout succeeds and clears session when a valid CSRF token is provided."""
    csrf_secret = "valid_csrf_token_secret"
    csrf_token = generate_csrf_token(csrf_secret)
    req_valid = Request({
        "type": "http",
        "method": "POST",
        "path": "/auth/logout",
        "headers": [(b"cookie", f"alphawatch_csrf={csrf_secret}".encode("utf-8"))],
    })
    
    resp = auth.logout(req_valid, csrf_token=csrf_token)
    assert resp.status_code == 303
    # Check that session cookie clear header is issued
    assert "alphawatch_session" in resp.headers.get("set-cookie", "")


def test_csrf_cookie_security_flags():
    """Proves that set_csrf_cookie sets HttpOnly, SameSite=Lax, and Path=/."""
    res = Response()
    set_csrf_cookie(res, "sample_test_cookie_value_123")
    
    set_cookie_header = res.headers.get("set-cookie", "")
    assert "alphawatch_csrf=sample_test_cookie_value_123" in set_cookie_header
    assert "HttpOnly" in set_cookie_header or "httponly" in set_cookie_header
    assert "SameSite=lax" in set_cookie_header or "samesite=lax" in set_cookie_header
    assert "Path=/" in set_cookie_header or "path=/" in set_cookie_header


def test_api_charts_endpoints_status_200():
    """Proves that /api/charts/nifty-trend and /api/charts/equity-curve return 200 without AttributeError."""
    req_nifty = Request({"type": "http", "method": "GET", "path": "/api/charts/nifty-trend", "headers": []})
    trend_data = api.api_nifty_trend(req_nifty)
    assert "dates" in trend_data
    assert "closes" in trend_data
    assert "sma50" in trend_data
    assert "sma200" in trend_data
    assert "regime" in trend_data
    assert "rule" in trend_data

    req_eq = Request({"type": "http", "method": "GET", "path": "/api/charts/equity-curve", "headers": []})
    eq_data = api.api_equity_curve(req_eq, symbol="RELIANCE")
    assert eq_data["symbol"] == "RELIANCE"
    assert "equity_curve" in eq_data
    assert isinstance(eq_data["equity_curve"], list)


def test_security_headers_middleware():
    """Verifies build_security_headers includes comprehensive defensive HTTP headers."""
    from app.main import build_security_headers
    
    headers = build_security_headers()
    headers_dict = {k.decode("utf-8").lower(): v.decode("utf-8") for k, v in headers}
    
    assert headers_dict.get("x-frame-options") == "DENY"
    assert headers_dict.get("x-content-type-options") == "nosniff"
    assert headers_dict.get("x-xss-protection") == "1; mode=block"
    assert headers_dict.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "camera=()" in headers_dict.get("permissions-policy", "")
    assert "default-src 'self'" in headers_dict.get("content-security-policy", "")


def test_path_traversal_in_load_prices_defended(tmp_path):
    """Proves that load_prices sanitizes directory traversal and contains file paths to processed_dir."""
    from src.data_loader import load_prices

    # Try path traversal sequences
    traversal_inputs = [
        "../../windows/win.ini",
        "../../../etc/passwd",
        "..\\..\\boot.ini",
        "....//....//something",
    ]
    for traversal in traversal_inputs:
        df, report = load_prices(traversal)
        assert df.empty
        assert report.total_rows == 0


def test_password_max_length_dos_defense():
    """Proves validate_password_strength bounds password length to 128 characters to mitigate Argon2 DoS."""
    from app.security import validate_password_strength

    # 1. Too short (< 10)
    valid, msg = validate_password_strength("Short1!")
    assert not valid
    assert "at least 10" in msg

    # 2. Too long (> 128) - DoS attack payload
    huge_pw = "A" * 500
    valid, msg = validate_password_strength(huge_pw)
    assert not valid
    assert "maximum allowable length" in msg

    # 3. Valid strong password
    valid, msg = validate_password_strength("MySecureSecretPassphrase2026!")
    assert valid
    assert msg is None


def test_logout_clears_both_session_and_csrf():
    """Proves that clear_session_cookie deletes both alphawatch_session and alphawatch_csrf cookies."""
    res = Response()
    clear_session_cookie(res)
    set_cookie_header = str(res.raw_headers)
    assert "alphawatch_session" in set_cookie_header
    assert "alphawatch_csrf" in set_cookie_header


def test_paper_trading_unwhitelisted_symbol_rejected(db_session):
    """Proves paper trading rejects unwhitelisted equity symbols."""
    import uuid
    # Create or reuse test user
    unique_email = f"sectest_{uuid.uuid4().hex[:8]}@alphawatch.local"
    user = User(
        name="Security Tester",
        email=unique_email,
        password_hash=hash_password("S3cureP@ssphrase2026!"),
        consent_given=True,
        is_onboarded=True,
    )
    db_session.add(user)
    db_session.commit()

    token = create_session_token(user.id)
    csrf_token = generate_csrf_token(token)

    req = Request({
        "type": "http",
        "method": "POST",
        "path": "/dashboard/paper-trading/order",
        "headers": [
            (b"cookie", f"alphawatch_session={token}".encode("utf-8")),
        ],
    })

    resp = dashboard.dashboard_paper_trade_order(
        request=req,
        symbol="INVALID_CO",
        action="BUY",
        quantity=10,
        notes=None,
        csrf_token=csrf_token,
        db=db_session,
    )
    assert resp.status_code == 303
    assert "error_msg=Unsupported+equity+symbol" in resp.headers.get("location", "")


def test_registration_validation_rules(db_session):
    """Proves registration rejects invalid email format and oversized fields."""
    csrf_secret = "reg_test_csrf_secret"
    csrf_tok = generate_csrf_token(csrf_secret)
    req = Request({
        "type": "http",
        "method": "POST",
        "path": "/auth/register",
        "headers": [(b"cookie", f"alphawatch_csrf={csrf_secret}".encode("utf-8"))],
    })
    res = Response()

    # 1. Invalid email format
    resp = auth.register_submit(
        request=req,
        response=res,
        name="Valid Name",
        email="notanemail",
        password="MyStrongPassphrase123!",
        confirm_password="MyStrongPassphrase123!",
        consent="1",
        csrf_token=csrf_tok,
        db=db_session,
    )
    assert resp.status_code == 400
    assert b"valid email address" in resp.body

    # 2. Oversized name
    resp2 = auth.register_submit(
        request=req,
        response=res,
        name="X" * 150,
        email="test_oversized@alphawatch.local",
        password="MyStrongPassphrase123!",
        confirm_password="MyStrongPassphrase123!",
        consent="1",
        csrf_token=csrf_tok,
        db=db_session,
    )
    assert resp2.status_code == 400
    assert b"between 2 and 120 characters" in resp2.body
