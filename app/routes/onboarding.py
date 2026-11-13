"""
AlphaWatch AI — Onboarding & Investor Profiler Route Handlers
ASTRAQUANT X 2026

Manages:
  - User initial holdings entry & verification
  - 7 fixed psychometric and behavioral question responses
  - Invokes src/profiler.py adaptive rule engine
  - Records deterministic 'Why this profile' derivations
"""

import json
import math
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import get_current_user, login_required
from app.db import get_db
from app.models_db import Holding, User, UserProfile
from app.security import get_request_csrf_token, set_csrf_cookie, validate_request_csrf
from src.portfolio import evaluate_portfolio
from src.profiler import evaluate_investor_profile

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

SUPPORTED_SYMBOLS = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "SBIN", "BHARTIARTL", "ITC", "LT", "HINDUNILVR",
    "BAJFINANCE", "MARUTI",
]


@router.get("", response_class=HTMLResponse)
def onboarding_form(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    # Strictly filter holdings by logged-in user's id
    user_holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()

    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="onboarding/index.html",
        context={
            "current_user": user,
            "current_holdings": user_holdings,
            "profile": user_profile,
            "supported_symbols": SUPPORTED_SYMBOLS,
            "csrf_token": csrf_token,
            "error_msg": None,
            "active_page": "onboarding",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.post("")
async def onboarding_submit(
    request: Request,
    goal: str = Form("Wealth Creation"),
    horizon: str = Form("3-5 Years"),
    experience: str = Form("Intermediate (1-3 Years)"),
    trading_frequency: str = Form("Monthly"),
    fall_reaction: str = Form("Hold and observe"),
    savings_share: str = Form("10-25%"),
    preferred_sectors: str = Form("Technology, Financials"),
    csrf_token: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    # 1. CSRF Verification
    if not validate_request_csrf(request, csrf_token):
        raise HTTPException(status_code=400, detail="Security validation failed")

    # 2. Parse multi-row form holdings safely
    form_data = await request.form()
    symbols = form_data.getlist("symbol[]")
    quantities = form_data.getlist("quantity[]")
    buy_prices = form_data.getlist("buy_price[]")

    # Purge prior holdings for this user before saving updated positions
    db.query(Holding).filter(Holding.user_id == user.id).delete()

    holdings_dicts = []
    max_rows = min(len(symbols), 50)  # Bound to max 50 holdings to prevent DoS
    for i in range(max_rows):
        sym = str(symbols[i]).strip().upper()
        if sym not in SUPPORTED_SYMBOLS:
            continue

        try:
            qty = int(quantities[i])
            px = float(buy_prices[i])
        except (ValueError, IndexError):
            continue

        if math.isnan(px) or math.isinf(px):
            continue

        if 0 < qty <= 1_000_000 and 0.0 < px <= 10_000_000.0:
            new_h = Holding(
                user_id=user.id,
                symbol=sym,
                quantity=qty,
                buy_price=px,
            )
            db.add(new_h)
            holdings_dicts.append({"symbol": sym, "quantity": qty, "buy_price": px})

    db.flush()

    # 3. Evaluate Portfolio composition to feed into profiler
    port_eval = evaluate_portfolio(holdings_dicts)
    holdings_summary = {
        "holdings": [
            {
                "symbol": h.symbol,
                "weight_pct": h.weight_pct,
                "unrealized_pnl_pct": h.unrealized_pnl_pct,
            }
            for h in port_eval.holdings
        ],
        "sector_weights": port_eval.sector_weights,
    }

    # 4. Invoke Adaptive Profiler Engine
    answers = {
        "goal": goal,
        "horizon": horizon,
        "experience": experience,
        "trading_frequency": trading_frequency,
        "fall_reaction": fall_reaction,
        "savings_share": savings_share,
        "preferred_sectors": preferred_sectors,
    }

    eval_result = evaluate_investor_profile(answers, holdings_summary)

    # 5. Persist User Profile
    prof = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not prof:
        prof = UserProfile(user_id=user.id)
        db.add(prof)

    prof.goal = goal
    prof.horizon = horizon
    prof.experience = experience
    prof.trading_frequency = trading_frequency
    prof.fall_reaction = fall_reaction
    prof.savings_share = savings_share
    prof.preferred_sectors = preferred_sectors
    prof.risk_score = eval_result.risk_score
    prof.suggested_profile = eval_result.suggested_profile
    prof.diversification_score = eval_result.diversification_score
    prof.concentration_status = eval_result.concentration_status
    prof.holding_style = eval_result.holding_style
    prof.why_this_profile = eval_result.why_this_profile
    prof.answers_json = json.dumps(answers)

    user.is_onboarded = True
    db.commit()

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
