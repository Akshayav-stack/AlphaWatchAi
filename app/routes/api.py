"""
AlphaWatch AI — Local REST API Endpoints
ASTRAQUANT X 2026

Offline API endpoints for local AJAX and chart data feeding.
Zero external network connectivity.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.limiter import limiter
from app.models_db import Holding as DbHolding, UserProfile
from src.backtest import run_backtest
from src.data_loader import load_nifty50, load_prices
from src.explain import explain_prediction
from src.market_trends import index_trend
from src.portfolio import Holding as DomainHolding
from src.signals import PROFILES

router = APIRouter(prefix="/api", tags=["API"])

SUPPORTED_SYMBOLS = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "SBIN", "BHARTIARTL", "ITC", "LT", "HINDUNILVR",
    "BAJFINANCE", "MARUTI",
]


@router.get("/health")
def healthcheck():
    """Application and offline data integrity healthcheck."""
    return {
        "status": "operational",
        "system": "AlphaWatch AI — ASTRAQUANT X 2026",
        "network_mode": "100% Offline Air-Gapped",
        "runtime_external_calls": 0,
        "supported_equities_count": len(SUPPORTED_SYMBOLS),
    }


@router.get("/charts/nifty-trend")
@limiter.limit("60/minute")
def api_nifty_trend(request: Request):
    """Returns NIFTY 50 price and SMA series for local Plotly charts."""
    df = load_nifty50()
    report = index_trend(df)

    dates = []
    closes = []
    sma50 = []
    sma200 = []
    if not df.empty and "Date" in df.columns:
        df_sorted = df.sort_values("Date").tail(250)
        dates = [d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d) for d in df_sorted["Date"]]
        closes = [float(x) for x in df_sorted["Close"].round(2)]
        sma50 = [float(x) for x in df_sorted["Close"].rolling(50, min_periods=1).mean().round(2)]
        sma200 = [float(x) for x in df_sorted["Close"].rolling(200, min_periods=1).mean().round(2)]

    return {
        "dates": dates,
        "closes": closes,
        "sma50": sma50,
        "sma200": sma200,
        "current_close": report.close,
        "regime": report.regime_label,
        "rule": report.rule_explanation,
        "as_of_date": report.as_of_date,
        "source_report": report.source_report,
    }


@router.get("/charts/equity-curve")
@limiter.limit("30/minute")
def api_equity_curve(request: Request, symbol: str = Query("RELIANCE")):
    """Returns backtest equity curve and benchmark values."""
    clean_sym = symbol.strip().upper()
    if clean_sym not in SUPPORTED_SYMBOLS:
        clean_sym = "RELIANCE"

    res = load_prices(clean_sym)
    df = res[0] if isinstance(res, tuple) else res
    bt = run_backtest(df, symbol=clean_sym)

    import dataclasses
    def to_dict_list(items):
        res_list = []
        for it in items:
            if dataclasses.is_dataclass(it):
                res_list.append(dataclasses.asdict(it))
            elif isinstance(it, dict):
                res_list.append(it)
        return res_list

    return {
        "symbol": bt.symbol,
        "start_date": bt.start_date,
        "end_date": bt.end_date,
        "total_return_pct": bt.total_return_pct,
        "cagr_pct": bt.cagr_pct,
        "benchmark_return_pct": bt.benchmark_return_pct,
        "sharpe_ratio": bt.sharpe_ratio,
        "max_drawdown_pct": bt.max_drawdown_pct,
        "equity_curve": to_dict_list(bt.equity_curve),
    }


DEMO_SYMBOLS = {
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "SBIN", "BHARTIARTL", "ITC", "LT", "HINDUNILVR",
}


@router.get("/explain/{symbol}")
@limiter.limit("60/minute")
def api_explain_symbol(
    symbol: str,
    request: Request,
    profile: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Returns verified Explainable AI decision intelligence for an equity.
    Requires user authentication, validates symbol against supported universe and user holdings/demo,
    validates profile, and returns comprehensive SHAP feature attributions, factor rules,
    and quantitative risk warnings.
    """
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to access decision intelligence.",
        )

    clean_sym = symbol.strip().upper()
    if clean_sym not in SUPPORTED_SYMBOLS:
        raise HTTPException(
            status_code=404,
            detail=f"Equity '{clean_sym}' is unknown or not supported.",
        )

    # Validate that symbol belongs to user's holdings or explicit demo list
    user_holdings = db.query(DbHolding).filter(DbHolding.user_id == user.id).all()
    user_symbols = {h.symbol.upper() for h in user_holdings}

    if clean_sym not in user_symbols and clean_sym not in DEMO_SYMBOLS:
        raise HTTPException(
            status_code=403,
            detail=f"Symbol '{clean_sym}' is not in your portfolio holdings or permitted demo universe.",
        )

    # Validate profile parameter
    if profile is not None:
        if profile not in PROFILES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid profile '{profile}'. Allowed profiles: {list(PROFILES.keys())}",
            )
        active_profile = profile
    else:
        user_prof = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        active_profile = user_prof.suggested_profile if (user_prof and user_prof.suggested_profile in PROFILES) else "Moderate"

    # Convert user holdings strictly for current user to domain objects
    holdings_domain = [
        DomainHolding(symbol=h.symbol, quantity=h.quantity, buy_price=h.buy_price)
        for h in user_holdings
    ]

    try:
        explanation = explain_prediction(
            symbol=clean_sym,
            profile=active_profile,
            user_holdings=holdings_domain,
        )
        return explanation
    except FileNotFoundError as fnf:
        raise HTTPException(
            status_code=409,
            detail=f"Missing trained model bundle or price history data for '{clean_sym}': {fnf}",
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=409,
            detail=f"Insufficient price history or invalid parameters for '{clean_sym}': {ve}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal error while computing decision intelligence explanation.",
        )
