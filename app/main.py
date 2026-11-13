"""
AlphaWatch AI — Main FastAPI Application
ASTRAQUANT X 2026

Self-contained, offline-first algorithmic trading intelligence workstation:
  - 100% offline-capable: Zero external network calls to NSE or Screener.in
  - Zero external CDN dependencies: Local Plotly.js & CSS in app/static/
  - Strict user data isolation: All queries filtered by logged-in user ID
  - Section 6 Security Checklist: Argon2id, CSRF HMAC, SlowAPI rate limiting, lockout tracking
  - Custom 404 & 500 exception handlers
"""

import os
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.db import Base, engine
from app.limiter import limiter
from app.routes import api, auth, dashboard, onboarding, public
from app.security import get_request_csrf_token

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Ensure all database tables exist on startup
Base.metadata.create_all(bind=engine)

ENVIRONMENT = (os.getenv("ENVIRONMENT") or os.getenv("APP_ENV", "development")).lower()

app = FastAPI(
    title="AlphaWatch AI — ASTRAQUANT X 2026",
    description="Offline Algorithmic Trading Intelligence Workstation for the Indian Stock Market",
    version="1.0.0",
    docs_url=None,     # Disabled in offline air-gapped mode for security
    redoc_url=None,
    openapi_url=None if ENVIRONMENT == "production" else "/openapi.json",
)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals["current_year"] = datetime.now().year
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
def build_security_headers() -> list[tuple[bytes, bytes]]:
    """Builds mandatory OWASP security headers list."""
    sec_headers = [
        (b"x-frame-options", b"DENY"),
        (b"x-content-type-options", b"nosniff"),
        (b"x-xss-protection", b"1; mode=block"),
        (b"referrer-policy", b"strict-origin-when-cross-origin"),
        (b"permissions-policy", b"camera=(), microphone=(), geolocation=(), payment=()"),
    ]
    if os.getenv("COOKIE_SECURE", "False").lower() in ("true", "1", "t"):
        sec_headers.append((b"strict-transport-security", b"max-age=31536000; includeSubDomains; preload"))
    sec_headers.append((
        b"content-security-policy",
        b"default-src 'self'; "
        b"script-src 'self' 'unsafe-inline'; "
        b"style-src 'self' 'unsafe-inline'; "
        b"img-src 'self' data:; "
        b"font-src 'self' data:; "
        b"connect-src 'self';"
    ))
    return sec_headers


class SecurityHeadersMiddleware:
    """Pure ASGI middleware adding robust security headers without BaseHTTPMiddleware deadlocks."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(build_security_headers())
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SlowAPIMiddleware)


# Include Route Handlers
app.include_router(public.router)
app.include_router(auth.router)
app.include_router(onboarding.router)
app.include_router(dashboard.router)
app.include_router(api.router)


# Custom 404 Exception Handler
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: HTTPException):
    csrf_token, _ = get_request_csrf_token(request)
    return templates.TemplateResponse(
        request=request,
        name="public/404.html",
        context={
            "current_user": None,
            "csrf_token": csrf_token,
            "active_page": "",
        },
        status_code=404,
    )


# Custom 500 Exception Handler
@app.exception_handler(500)
async def custom_500_handler(request: Request, exc: Exception):
    csrf_token, _ = get_request_csrf_token(request)
    return templates.TemplateResponse(
        request=request,
        name="public/500.html",
        context={
            "current_user": None,
            "csrf_token": csrf_token,
            "active_page": "",
        },
        status_code=500,
    )
