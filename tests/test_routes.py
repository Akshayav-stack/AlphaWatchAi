"""
AlphaWatch AI — End-to-End Route, Security & User Isolation Tests
ASTRAQUANT X 2026

Tests:
  - Public routes & disclosures (How It Works, Limitations, Terms, Health API)
  - Security protections (Password Policy, Blacklist, CSRF)
  - Auth, Profile & Holdings Integration
  - Complete Dashboard Suite (Overview, Predictions, Buy Candidates, Market Trends,
    Risk, Backtest, Model Performance, Paper Trading, Claim Auditor, Ripple Effect, Profile, Settings)
  - Strict User Separation: Users cannot access or see each other's data
  - Cascading Account Deletion (Right to Erasure)
"""

import pytest
from starlette.requests import Request
from starlette.responses import Response

from app.db import Base, engine, SessionLocal
from app.models_db import Holding, PaperTrade, User, UserProfile
from app.auth import create_session_token
from app.security import hash_password, validate_password_strength, get_request_csrf_token
from app.routes import public, api, auth, dashboard


@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        # Clean state for test module
        session.query(PaperTrade).delete()
        session.query(Holding).delete()
        session.query(UserProfile).delete()
        session.query(User).delete()
        session.commit()
        yield session
    finally:
        session.close()


def test_public_pages(db_session):
    scope = {"type": "http", "method": "GET", "path": "/", "headers": [], "query_string": b""}
    req = Request(scope)
    res = Response()

    # Home
    h_resp = public.home(req, res, db_session)
    assert h_resp.status_code == 200
    assert b"AlphaWatch" in h_resp.body

    # How It Works
    how_resp = public.how_it_works(req, res, db_session)
    assert how_resp.status_code == 200
    assert b"Data Sources" in how_resp.body
    assert b"National Stock Exchange" in how_resp.body
    assert b"Screener.in" in how_resp.body

    # Limitations & Disclaimer
    lim_resp = public.limitations(req, res, db_session)
    assert lim_resp.status_code == 200
    assert b"No Broker Integration" in lim_resp.body
    assert b"No Email Verification" in lim_resp.body
    assert b"No Admin Area" in lim_resp.body

    # Terms & Privacy
    term_resp = public.terms(req, res, db_session)
    assert term_resp.status_code == 200
    assert b"Right to Erasure" in term_resp.body
    assert b"Privacy Policy" in term_resp.body

    # Health API
    health = api.healthcheck()
    assert health["status"] == "operational"
    assert health["runtime_external_calls"] == 0
    assert health["supported_equities_count"] == 12


def test_password_policy_and_security():
    # 1. Reject short (< 10 chars)
    is_valid, msg = validate_password_strength("short")
    assert not is_valid
    assert "at least 10" in msg

    # 2. Reject common password
    is_valid, msg = validate_password_strength("password123")
    assert not is_valid
    assert "easily guessed" in msg

    # 3. Accept strong passphrase
    is_valid, msg = validate_password_strength("AstraquantSafePass2026!")
    assert is_valid
    assert msg is None


def test_user_flow_and_dashboard_subsystem(db_session):
    # Create User A
    user_a = User(
        name="Dr. Vikram Sarabhai",
        email="vikram@astraquant.edu",
        password_hash=hash_password("AstraquantSafePass2026!"),
        consent_given=True,
        is_onboarded=True,
    )
    db_session.add(user_a)
    db_session.commit()
    db_session.refresh(user_a)

    # Holdings for User A
    h1 = Holding(user_id=user_a.id, symbol="RELIANCE", quantity=10, buy_price=2500.0)
    h2 = Holding(user_id=user_a.id, symbol="TCS", quantity=5, buy_price=3800.0)
    prof_a = UserProfile(
        user_id=user_a.id,
        risk_score=55.0,
        suggested_profile="Moderate",
        holding_style="Balanced Growth & Core Stability",
        why_this_profile="Balanced investor profile derived from questionnaire responses.",
        diversification_score=70.0,
        concentration_status="Balanced",
    )
    db_session.add_all([h1, h2, prof_a])
    db_session.commit()

    token_a = create_session_token(user_a.id)
    auth_scope = {
        "type": "http",
        "method": "GET",
        "path": "/dashboard",
        "headers": [(b"cookie", f"alphawatch_session={token_a}".encode("utf-8"))],
        "query_string": b"",
    }
    req = Request(auth_scope)
    res = Response()

    # 1. Overview
    d_resp = dashboard.dashboard_overview(req, res, db_session)
    assert d_resp.status_code == 200
    assert b"LOW RISK" in d_resp.body
    assert b"MED RISK" in d_resp.body
    assert b"HIGH RISK" in d_resp.body

    # 2. Predictions
    pred_resp = dashboard.dashboard_predictions(req, res, db_session)
    assert pred_resp.status_code == 200
    assert b"Holdings Predictions" in pred_resp.body

    # 3. Buy Candidates
    buy_resp = dashboard.dashboard_buy_candidates(req, res, db_session)
    assert buy_resp.status_code == 200
    assert b"Buy Candidates" in buy_resp.body

    # 4. Market Trends
    mt_resp = dashboard.dashboard_market_trends(req, res, db_session)
    assert mt_resp.status_code == 200
    assert b"NIFTY 50" in mt_resp.body
    assert b"India VIX" in mt_resp.body

    # 5. Risk
    risk_resp = dashboard.dashboard_risk(req, res, db_session)
    assert risk_resp.status_code == 200
    assert b"Value at Risk" in risk_resp.body

    # 6. Backtest
    bt_resp = dashboard.dashboard_backtest(req, res, symbol="RELIANCE", db=db_session)
    assert bt_resp.status_code == 200
    assert b"Backtest" in bt_resp.body

    # 7. Model Performance
    mp_resp = dashboard.dashboard_model_performance(req, res, db=db_session)
    assert mp_resp.status_code == 200
    assert b"Walk-Forward" in mp_resp.body

    # 8. Paper Trading
    pt_resp = dashboard.dashboard_paper_trading(req, res, db=db_session)
    assert pt_resp.status_code == 200
    assert b"Paper Trading" in pt_resp.body

    # 9. Claim Auditor
    aud_resp = dashboard.dashboard_auditor(req, res, db=db_session)
    assert aud_resp.status_code == 200
    assert b"Claim Auditor" in aud_resp.body

    # 10. Ripple Effect
    rip_resp = dashboard.dashboard_ripple(req, res, scenario="crude_oil_spike", db=db_session)
    assert rip_resp.status_code == 200
    assert b"Ripple Effect" in rip_resp.body

    # 11. Profile
    prof_resp = dashboard.dashboard_profile(req, res, db=db_session)
    assert prof_resp.status_code == 200
    assert b"Why This Profile" in prof_resp.body

    # 12. Settings
    sett_resp = dashboard.dashboard_settings(req, res, db=db_session)
    assert sett_resp.status_code == 200
    assert b"Settings" in sett_resp.body


def test_user_data_isolation(db_session):
    # Create User B
    user_b = User(
        name="Dr. APJ Abdul Kalam",
        email="kalam@astraquant.edu",
        password_hash=hash_password("AstraquantSafePass2026!"),
        consent_given=True,
        is_onboarded=True,
    )
    db_session.add(user_b)
    db_session.commit()
    db_session.refresh(user_b)

    # Holding for User B is ITC only
    h_b = Holding(user_id=user_b.id, symbol="ITC", quantity=100, buy_price=420.0)
    prof_b = UserProfile(
        user_id=user_b.id,
        risk_score=25.0,
        suggested_profile="Conservative",
        holding_style="Conservative",
        why_this_profile="Low risk profile",
        diversification_score=40.0,
        concentration_status="Concentrated",
    )
    db_session.add_all([h_b, prof_b])
    db_session.commit()

    token_b = create_session_token(user_b.id)
    scope_b = {
        "type": "http",
        "method": "GET",
        "path": "/dashboard",
        "headers": [(b"cookie", f"alphawatch_session={token_b}".encode("utf-8"))],
        "query_string": b"",
    }
    req_b = Request(scope_b)
    res = Response()

    d_resp_b = dashboard.dashboard_overview(req_b, res, db_session)
    assert d_resp_b.status_code == 200
    assert b"ITC" in d_resp_b.body
    # User B must NOT see User A's RELIANCE or TCS
    assert b"RELIANCE" not in d_resp_b.body
    assert b"TCS" not in d_resp_b.body


def test_right_to_erasure_cascading_deletion(db_session):
    # Fetch User B
    user_b = db_session.query(User).filter(User.email == "kalam@astraquant.edu").first()
    assert user_b is not None
    user_b_id = user_b.id

    token_b = create_session_token(user_b_id)
    del_scope = {
        "type": "http",
        "method": "POST",
        "path": "/auth/delete-account",
        "headers": [(b"cookie", f"alphawatch_session={token_b}".encode("utf-8"))],
        "query_string": b"",
    }
    del_req = Request(del_scope)
    csrf_tok, _ = get_request_csrf_token(del_req)

    del_resp = auth.delete_account(del_req, csrf_token=csrf_tok, db=db_session)
    assert del_resp.status_code == 303
    assert "deleted=1" in del_resp.headers["Location"]

    # Verify cascading erasure
    assert db_session.query(User).filter(User.id == user_b_id).first() is None
    assert db_session.query(Holding).filter(Holding.user_id == user_b_id).count() == 0
    assert db_session.query(UserProfile).filter(UserProfile.user_id == user_b_id).count() == 0
