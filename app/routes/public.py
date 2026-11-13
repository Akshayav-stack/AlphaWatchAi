"""
AlphaWatch AI — Public Route Handlers
ASTRAQUANT X 2026

Routes:
  - / (Home)
  - /how-it-works (Methodology & Data sources naming NSE and Screener.in with as-of dates)
  - /limitations (Scope limitations & academic disclaimer)
  - /terms (Privacy policy, data retention & right-to-erasure)
"""

from pathlib import Path
from fastapi import APIRouter, Depends, Request, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.security import get_request_csrf_token, set_csrf_cookie

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(tags=["Public"])


@router.get("/")
def home(request: Request, response: Response, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="public/home.html",
        context={
            "current_user": user,
            "csrf_token": csrf_token,
            "active_page": "home",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.get("/how-it-works")
def how_it_works(request: Request, response: Response, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="public/how_it_works.html",
        context={
            "current_user": user,
            "csrf_token": csrf_token,
            "active_page": "how_it_works",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.get("/limitations")
def limitations(request: Request, response: Response, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="public/limitations.html",
        context={
            "current_user": user,
            "csrf_token": csrf_token,
            "active_page": "limitations",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.get("/terms")
@router.get("/privacy-terms")
def terms(request: Request, response: Response, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="public/terms.html",
        context={
            "current_user": user,
            "csrf_token": csrf_token,
            "active_page": "terms",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp
