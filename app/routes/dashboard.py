"""
AlphaWatch AI — Dashboard Workstation Route Handlers
ASTRAQUANT X 2026

Security & Architecture:
  - Enforces strict user isolation: EVERY database query filters by current_user.id
  - 100% offline calculation from saved CSV & Excel files
  - Zero external CDN dependencies
  - Mandatory educational research disclaimers on every view
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import get_current_user, login_required
from app.db import get_db
from app.limiter import limiter
from app.models_db import Holding, PaperTrade, User, UserProfile
from app.security import get_request_csrf_token, set_csrf_cookie, validate_request_csrf

from src.auditor import run_claim_audit
from src.backtest import run_backtest
from src.benchmark import compare_with_nifty
from src.data_loader import load_nifty50, load_prices, load_vix
from src.market_trends import breadth, delivery_trend, index_trend, movers, vix_regime
from src.optimize import optimize_portfolio
from src.paper_trading import compute_paper_portfolio, validate_paper_order
from src.portfolio import SECTOR_MAP, evaluate_portfolio
from src.ripple import simulate_ripple_scenario
from src.risk import compute_portfolio_risk
from src.signals import get_or_train_prediction, get_ranked_buy_candidates

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

SUPPORTED_SYMBOLS = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "SBIN", "BHARTIARTL", "ITC", "LT", "HINDUNILVR",
    "BAJFINANCE", "MARUTI",
]


@router.get("", response_class=HTMLResponse)
def dashboard_overview(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    if not user.is_onboarded:
        return RedirectResponse(url="/onboarding", status_code=303)

    # STRICT USER ISOLATION: query holdings strictly by user.id
    user_holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()

    holdings_dicts = [
        {"symbol": h.symbol, "quantity": h.quantity, "buy_price": h.buy_price}
        for h in user_holdings
    ]

    port_eval = evaluate_portfolio(holdings_dicts)
    risk_report = compute_portfolio_risk(holdings_dicts)

    # Top-right risk counter card (Low, Medium, High risk)
    risk_counts = {"low": 0, "medium": 0, "high": 0}
    for asset in risk_report.asset_profiles:
        tier = asset.risk_label.lower()
        if tier in risk_counts:
            risk_counts[tier] += 1
        else:
            risk_counts["medium"] += 1

    # Attach risk tier to evaluated holdings
    risk_tier_map = {a.symbol: a.risk_label for a in risk_report.asset_profiles}
    for h in port_eval.holdings:
        h.risk_tier = risk_tier_map.get(h.symbol, "Medium")

    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="dashboard/overview.html",
        context={
            "current_user": user,
            "user_profile": user_profile,
            "portfolio_data": port_eval,
            "risk_counts": risk_counts,
            "csrf_token": csrf_token,
            "active_page": "overview",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.get("/predictions", response_class=HTMLResponse)
def dashboard_predictions(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    user_holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    profile_type = user_profile.suggested_profile if user_profile else "Moderate"

    predictions = []
    as_of = "N/A"

    for h in user_holdings:
        card = get_or_train_prediction(h.symbol, investor_profile=profile_type)
        as_of = card.as_of_date
        f = card.fundamentals

        diag_details = []
        pillars = getattr(f, "pillar_evaluations", getattr(f, "pillars", []))
        for p in pillars:
            p_name = getattr(p, "pillar_name", getattr(p, "pillar", "Pillar"))
            val = getattr(p, "input_value", getattr(p, "value", "N/A"))
            val_disp = f"{val:.2f}" if isinstance(val, (int, float)) else str(val or "N/A")
            status_val = getattr(p, "status", "Neutral")
            is_passed = status_val == "Pass"
            rule_text = getattr(p, "rule_description", getattr(p, "rule_fired", ""))
            diag_details.append({
                "pillar": p_name,
                "metric_name": p_name,
                "value": val_disp,
                "threshold": rule_text,
                "passed": is_passed,
                "status": status_val,
                "rule_fired": rule_text,
            })

        export_date = getattr(f, "source_export_date", getattr(f, "export_date", "N/A"))
        is_stale = getattr(f, "is_stale", False)

        predictions.append({
            "symbol": card.symbol,
            "current_price": card.current_price,
            "signal": card.signal,
            "probability_pct": card.probability_up_pct,
            "risk_label": card.risk_label,
            "reason": card.model_reason,
            "fundamentals_badge": getattr(f, "badge", "Mixed"),
            "fundamentals_export_date": export_date,
            "is_stale": is_stale,
            "combined_explanation": card.combined_explanation,
            "diagnostic_details": diag_details,
        })

    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="dashboard/predictions.html",
        context={
            "current_user": user,
            "predictions": predictions,
            "as_of_date": as_of,
            "csrf_token": csrf_token,
            "active_page": "predictions",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.get("/buy-candidates", response_class=HTMLResponse)
def dashboard_buy_candidates(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    user_profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    profile_type = user_profile.suggested_profile if user_profile else "Moderate"

    candidates_cards = get_ranked_buy_candidates(
        investor_profile=profile_type,
        supported_symbols=SUPPORTED_SYMBOLS,
    )

    candidates = []
    as_of = "N/A"
    for c in candidates_cards:
        as_of = c.as_of_date
        fit_score = 90 if c.signal == "BUY" and c.fundamentals.badge == "Strong" else (75 if c.signal == "BUY" else 55)
        candidates.append({
            "symbol": c.symbol,
            "sector": SECTOR_MAP.get(c.symbol, "Equities"),
            "current_price": c.current_price,
            "signal": c.signal,
            "probability_pct": c.probability_up_pct,
            "risk_label": c.risk_label,
            "fundamentals_badge": c.fundamentals.badge,
            "profile_fit_score": fit_score,
            "reason": c.combined_explanation,
        })

    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="dashboard/buy_candidates.html",
        context={
            "current_user": user,
            "user_profile": user_profile,
            "candidates": candidates,
            "as_of_date": as_of,
            "csrf_token": csrf_token,
            "active_page": "buy_candidates",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.get("/market-trends", response_class=HTMLResponse)
def dashboard_market_trends(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    nifty_df = load_nifty50()
    vix_df = load_vix()

    nifty_rep = index_trend(nifty_df)
    vix_rep = vix_regime(vix_df)
    breadth_rep = breadth()
    movers_rep = movers(SUPPORTED_SYMBOLS)
    delivery_rep = delivery_trend("RELIANCE")

    dates = []
    closes = []
    sma_50_series = []
    sma_200_series = []
    if not nifty_df.empty and "Date" in nifty_df.columns:
        nifty_sorted = nifty_df.sort_values("Date").tail(250)
        dates = [d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d) for d in nifty_sorted["Date"]]
        closes = [float(x) for x in nifty_sorted["Close"].round(2)]
        sma_50_series = [float(x) for x in nifty_sorted["Close"].rolling(50, min_periods=1).mean().round(2)]
        sma_200_series = [float(x) for x in nifty_sorted["Close"].rolling(200, min_periods=1).mean().round(2)]

    nifty_dict = {
        "current_close": nifty_rep.close,
        "close": nifty_rep.close,
        "sma_50": nifty_rep.sma50 or 0.0,
        "sma_200": nifty_rep.sma200 or 0.0,
        "dist_sma_50_pct": f"{nifty_rep.diff_sma50_pct:+.2f}" if nifty_rep.diff_sma50_pct is not None else "0.00",
        "dist_sma_200_pct": f"{nifty_rep.diff_sma200_pct:+.2f}" if nifty_rep.diff_sma200_pct is not None else "0.00",
        "regime_label": nifty_rep.regime_label,
        "regime_rule": nifty_rep.rule_explanation,
        "source_report": nifty_rep.source_report,
        "as_of_date": nifty_rep.as_of_date,
        "dates": dates,
        "closes": closes,
        "sma_50_series": sma_50_series,
        "sma_200_series": sma_200_series,
    }

    vix_dict = {
        "current_vix": round(vix_rep.vix_level, 2),
        "historical_percentile": round(vix_rep.vix_percentile, 1),
        "regime_label": vix_rep.regime_label,
        "regime_rule": vix_rep.description,
        "source_report": vix_rep.source_report,
        "as_of_date": vix_rep.as_of_date,
    }

    latest_b = breadth_rep[0] if (breadth_rep and len(breadth_rep) > 0) else None
    breadth_dict = {
        "advances": latest_b.advances if latest_b else 0,
        "declines": latest_b.declines if latest_b else 0,
        "unchanged": latest_b.unchanged if latest_b else 0,
        "ad_ratio": round(latest_b.ad_ratio, 2) if latest_b else 1.0,
        "breadth_status": latest_b.breadth_label if latest_b else "Neutral",
        "source_report": latest_b.source_report if latest_b else "NSE CM-UDiFF Bhavcopy",
        "as_of_date": latest_b.as_of_date if latest_b else "N/A",
    }

    top_gainers = [
        {"symbol": m.symbol, "change_pct": f"{m.ret_1d_pct:+.2f}", "close": m.close}
        for m in movers_rep.top_gainers_1d
    ]
    top_losers = [
        {"symbol": m.symbol, "change_pct": f"{m.ret_1d_pct:+.2f}", "close": m.close}
        for m in movers_rep.top_losers_1d
    ]
    movers_dict = {
        "top_gainers_1d": top_gainers,
        "top_losers_1d": top_losers,
        "source_report": movers_rep.source_report,
        "as_of_date": movers_rep.as_of_date,
    }

    delivery_dict = {
        "symbol": delivery_rep.symbol,
        "current_delivery_pct": round(delivery_rep.latest_delivery_pct, 1),
        "sma_delivery_20_pct": round(delivery_rep.avg_delivery_pct_20d or 0.0, 1),
        "delivery_ratio_20": round(delivery_rep.delivery_ratio_20d or 1.0, 2),
        "delivery_trend_label": delivery_rep.trend_label,
        "source_report": delivery_rep.source_report,
        "as_of_date": delivery_rep.as_of_date,
    }

    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="dashboard/market_trends.html",
        context={
            "current_user": user,
            "nifty_trend": nifty_dict,
            "vix_report": vix_dict,
            "breadth_report": breadth_dict,
            "movers_report": movers_dict,
            "delivery_report": delivery_dict,
            "csrf_token": csrf_token,
            "active_page": "market_trends",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.get("/risk", response_class=HTMLResponse)
def dashboard_risk(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    user_holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
    holdings_dicts = [
        {"symbol": h.symbol, "quantity": h.quantity, "buy_price": h.buy_price}
        for h in user_holdings
    ]

    risk_rep = compute_portfolio_risk(holdings_dicts)

    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="dashboard/risk.html",
        context={
            "current_user": user,
            "risk_report": risk_rep,
            "csrf_token": csrf_token,
            "active_page": "risk",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.get("/backtest", response_class=HTMLResponse)
def dashboard_backtest(
    request: Request,
    response: Response,
    symbol: str = Query("RELIANCE"),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    clean_sym = symbol.strip().upper()
    if clean_sym not in SUPPORTED_SYMBOLS:
        clean_sym = "RELIANCE"

    res_stock = load_prices(clean_sym)
    df_stock = res_stock[0] if isinstance(res_stock, tuple) else res_stock

    bt_result = run_backtest(df_stock, symbol=clean_sym)

    # Optimization using user holdings or supported universe
    user_holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
    cur_weights = {h.symbol: float(h.quantity * h.buy_price) for h in user_holdings} if user_holdings else None
    opt_symbols = [h.symbol for h in user_holdings] if user_holdings and len(user_holdings) >= 2 else SUPPORTED_SYMBOLS[:5]

    opt_res = optimize_portfolio(opt_symbols, current_weights=cur_weights)

    import dataclasses
    def to_dict_safe(obj):
        if obj is None:
            return None
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return obj

    opt_dict = {
        "symbols": opt_res.symbols,
        "current_portfolio": to_dict_safe(opt_res.current_portfolio),
        "equal_weight": to_dict_safe(opt_res.equal_weight),
        "min_variance": to_dict_safe(opt_res.min_variance),
        "max_sharpe": to_dict_safe(opt_res.max_sharpe),
        "risk_parity": to_dict_safe(opt_res.risk_parity),
        "efficient_frontier": opt_res.efficient_frontier,
    }

    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="dashboard/backtest.html",
        context={
            "current_user": user,
            "selected_symbol": clean_sym,
            "supported_symbols": SUPPORTED_SYMBOLS,
            "backtest_result": bt_result,
            "opt_result": opt_dict,
            "csrf_token": csrf_token,
            "active_page": "backtest",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.get("/model-performance", response_class=HTMLResponse)
def dashboard_model_performance(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    # Load empirical metrics from saved walk-forward modeling artifacts
    models_dir = PROJECT_ROOT / "models" / "saved"
    metrics_files = sorted(list(models_dir.glob("*_metrics.json")))

    has_models = False
    test_metrics = None
    cv_folds = []
    feature_importances = []
    selected_symbol = "N/A"

    if metrics_files:
        try:
            import json
            first_metrics_path = metrics_files[0]
            with open(first_metrics_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            selected_symbol = data.get("symbol", first_metrics_path.stem.replace("_metrics", ""))
            raw_test = data.get("test_metrics", {})

            class EmpiricalMetrics:
                accuracy = float(raw_test.get("accuracy", 0.0))
                precision = float(raw_test.get("precision", 0.0))
                recall = float(raw_test.get("recall", 0.0))
                f1 = float(raw_test.get("f1", 0.0))
                roc_auc = float(raw_test.get("roc_auc", 0.0))
                brier_score = float(raw_test.get("brier_score", 0.0))

            test_metrics = EmpiricalMetrics()
            cv_folds = data.get("walk_forward_cv", [])
            feature_importances = data.get("top_features", [])
            has_models = True
        except Exception:
            has_models = False

    csrf_token, new_cookie = get_request_csrf_token(request)

    # Load system benchmark latency report if available
    latency_file = PROJECT_ROOT / "reports" / "latency.json"
    latency_data = None
    if latency_file.exists():
        try:
            import json
            with open(latency_file, "r", encoding="utf-8") as lf:
                latency_data = json.load(lf)
        except Exception:
            latency_data = None

    resp = templates.TemplateResponse(
        request=request,
        name="dashboard/model_performance.html",
        context={
            "current_user": user,
            "has_models": has_models,
            "selected_symbol": selected_symbol,
            "test_metrics": test_metrics,
            "cv_folds": cv_folds,
            "feature_importances": feature_importances,
            "latency_data": latency_data,
            "csrf_token": csrf_token,
            "active_page": "models",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.get("/paper-trading", response_class=HTMLResponse)
def dashboard_paper_trading(
    request: Request,
    response: Response,
    error_msg: Optional[str] = Query(None),
    success_msg: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    # STRICT USER ISOLATION: filter paper trades strictly by user.id
    user_trades = db.query(PaperTrade).filter(PaperTrade.user_id == user.id).all()
    paper_summary = compute_paper_portfolio(user_trades)

    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="dashboard/paper_trading.html",
        context={
            "current_user": user,
            "paper_summary": paper_summary,
            "supported_symbols": SUPPORTED_SYMBOLS,
            "error_msg": error_msg,
            "success_msg": success_msg,
            "csrf_token": csrf_token,
            "active_page": "paper_trading",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.post("/paper-trading/order")
@limiter.limit("20/minute")
def dashboard_paper_trade_order(
    request: Request,
    symbol: str = Form(...),
    action: str = Form(...),
    quantity: int = Form(...),
    notes: Optional[str] = Form(None),
    csrf_token: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    if not validate_request_csrf(request, csrf_token):
        raise HTTPException(status_code=400, detail="Security validation failed")

    clean_sym = symbol.strip().upper()
    clean_act = action.strip().upper()

    # Symbol Whitelist Enforcement (prevents injection / unauthorized paper orders)
    if clean_sym not in SUPPORTED_SYMBOLS:
        return RedirectResponse(
            url=f"/dashboard/paper-trading?error_msg=Unsupported+equity+symbol:+{clean_sym}",
            status_code=303,
        )

    # Fetch latest saved close price for execution
    res_stock = load_prices(clean_sym)
    df_stock = res_stock[0] if isinstance(res_stock, tuple) else res_stock
    if df_stock.empty or "Close" not in df_stock.columns:
        return RedirectResponse(
            url=f"/dashboard/paper-trading?error_msg=Price+data+unavailable+for+{clean_sym}",
            status_code=303,
        )

    exec_price = float(df_stock["Close"].iloc[-1])
    trade_date = str(df_stock["Date"].iloc[-1])

    # Compute current user paper state
    user_trades = db.query(PaperTrade).filter(PaperTrade.user_id == user.id).all()
    paper_summary = compute_paper_portfolio(user_trades)

    current_holding_qty = 0
    for pos in paper_summary.open_positions:
        if pos.symbol == clean_sym:
            current_holding_qty = pos.quantity
            break

    is_valid, msg, friction = validate_paper_order(
        action=clean_act,
        symbol=clean_sym,
        quantity=quantity,
        price=exec_price,
        current_cash=paper_summary.available_cash,
        current_holding_qty=current_holding_qty,
    )

    if not is_valid:
        return RedirectResponse(
            url=f"/dashboard/paper-trading?error_msg={msg.replace(' ', '+')}",
            status_code=303,
        )

    net_amt = (quantity * exec_price) + (friction if clean_act == "BUY" else -friction)

    # Persist simulated order strictly for user.id
    new_trade = PaperTrade(
        user_id=user.id,
        symbol=clean_sym,
        action=clean_act,
        quantity=quantity,
        price=exec_price,
        brokerage_stt=friction,
        net_amount=net_amt,
        trade_date=trade_date,
        notes=notes.strip() if notes else None,
    )
    db.add(new_trade)
    db.commit()

    return RedirectResponse(
        url=f"/dashboard/paper-trading?success_msg=Simulated+{clean_act}+order+executed+for+{quantity}+shares+of+{clean_sym}+at+INR+{exec_price:.2f}",
        status_code=303,
    )


@router.get("/auditor", response_class=HTMLResponse)
def dashboard_auditor(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    audit_summary = run_claim_audit(symbols=SUPPORTED_SYMBOLS, max_records=60)

    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="dashboard/auditor.html",
        context={
            "current_user": user,
            "audit_summary": audit_summary,
            "csrf_token": csrf_token,
            "active_page": "auditor",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.get("/ripple", response_class=HTMLResponse)
def dashboard_ripple(
    request: Request,
    response: Response,
    scenario: str = Query("crude_oil_spike"),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    user_holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
    sim_result = simulate_ripple_scenario(scenario, user_holdings)

    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="dashboard/ripple.html",
        context={
            "current_user": user,
            "selected_scenario": scenario,
            "sim_result": sim_result,
            "csrf_token": csrf_token,
            "active_page": "ripple",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.get("/profile", response_class=HTMLResponse)
def dashboard_profile(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    user_profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()

    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="dashboard/profile.html",
        context={
            "current_user": user,
            "user_profile": user_profile,
            "csrf_token": csrf_token,
            "active_page": "profile",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp


@router.get("/settings", response_class=HTMLResponse)
def dashboard_settings(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    user_profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()

    csrf_token, new_cookie = get_request_csrf_token(request)
    resp = templates.TemplateResponse(
        request=request,
        name="dashboard/settings.html",
        context={
            "current_user": user,
            "user_profile": user_profile,
            "csrf_token": csrf_token,
            "error_msg": None,
            "success_msg": None,
            "active_page": "settings",
        },
    )
    if new_cookie:
        set_csrf_cookie(resp, new_cookie)
    return resp
