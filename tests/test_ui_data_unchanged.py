"""
AlphaWatch AI — UI Baseline & Data Immutability Verification Test
ASTRAQUANT X 2026

Ensures visual reskins and styling changes preserve:
  - Exact computed text in table cells, stat cards, badges, signal rows, and risk labels
  - All form field name attributes, input types, and form actions/methods
  - All navigation and footer link targets
  - As-of dates, provenance disclosures, and data-source statements
"""

import json
import re
from pathlib import Path
from html.parser import HTMLParser
import pytest
from starlette.requests import Request
from starlette.responses import Response

from app.db import Base, engine, SessionLocal
from app.models_db import Holding, PaperTrade, User, UserProfile
from app.auth import create_session_token
from app.security import hash_password
from app.routes import public, auth, onboarding, dashboard

BASELINE_PATH = Path(__file__).resolve().parent / "ui_baseline.json"


class UIDataExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tag_stack = []
        
        self.table_cells = []
        self.stat_cards = []
        self.badges = []
        self.signal_rows = []
        self.risk_labels = []
        self.form_values = []
        self.form_fields = []
        self.link_targets = []
        self.as_of_and_data_sources = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        classes = attr_dict.get("class", "").split()
        self.tag_stack.append((tag, attr_dict, classes, []))

        # Form fields & values
        if tag == "form":
            self.form_fields.append({
                "tag": "form",
                "action": attr_dict.get("action", ""),
                "method": attr_dict.get("method", "get").upper()
            })
        elif tag == "input":
            name = attr_dict.get("name")
            val = attr_dict.get("value", "")
            itype = attr_dict.get("type", "text")
            if name:
                self.form_fields.append({"tag": "input", "name": name, "type": itype})
            # Skip dynamic CSRF tokens from comparison baseline
            if val and name != "csrf_token":
                self.form_values.append({"name": name, "value": val, "type": itype})
        elif tag == "select":
            name = attr_dict.get("name")
            if name:
                self.form_fields.append({"tag": "select", "name": name})
        elif tag == "option":
            if "selected" in attr_dict:
                self.form_values.append({"tag": "option", "value": attr_dict.get("value", "")})
        elif tag == "textarea":
            name = attr_dict.get("name")
            if name:
                self.form_fields.append({"tag": "textarea", "name": name})
        elif tag == "a":
            href = attr_dict.get("href")
            if href:
                self.link_targets.append(href)

    def handle_data(self, data):
        txt = data.strip()
        if txt:
            for item in self.tag_stack:
                item[3].append(txt)
            low = txt.lower()
            if any(k in low for k in ["as-of", "as of", "data source", "offline data", "reference date", "provenance"]):
                norm = re.sub(r"\s+", " ", txt)
                if norm not in self.as_of_and_data_sources:
                    self.as_of_and_data_sources.append(norm)

    def handle_endtag(self, tag):
        if not self.tag_stack:
            return
        cur_tag, cur_attrs, cur_classes, text_list = self.tag_stack.pop()
        full_text = " ".join(text_list).strip()
        full_text = re.sub(r"\s+", " ", full_text)
        if not full_text:
            return

        class_str = " ".join(cur_classes).lower()

        # Table cells
        if cur_tag in ("th", "td"):
            self.table_cells.append(full_text)

        # Stat cards
        if any(c in class_str for c in ["stat-card", "metric-card", "summary-card", "card-lead", "overview-number", "stat-val", "metric-value"]):
            self.stat_cards.append(full_text)

        # Badges
        if any(c in class_str for c in ["badge", "pill", "tag"]):
            self.badges.append(full_text)

        # Signal rows
        if any(c in class_str for c in ["signal-row", "signal-item", "signal-card"]):
            self.signal_rows.append(full_text)

        # Risk labels
        if any(c in class_str for c in ["risk-label", "risk-badge", "risk-pill", "risk-low", "risk-med", "risk-high", "badge-risk"]):
            self.risk_labels.append(full_text)


def extract_page_data(html_text: str):
    parser = UIDataExtractor()
    parser.feed(html_text)
    return {
        "table_cells": parser.table_cells,
        "stat_cards": parser.stat_cards,
        "badges": parser.badges,
        "signal_rows": parser.signal_rows,
        "risk_labels": parser.risk_labels,
        "form_values": parser.form_values,
        "form_fields": parser.form_fields,
        "link_targets": parser.link_targets,
        "as_of_and_data_sources": parser.as_of_and_data_sources,
    }


@pytest.fixture(scope="module")
def setup_demo_user():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == "vikram@astraquant.edu").first()
        if not user:
            user = User(
                name="Dr. Vikram Sarabhai",
                email="vikram@astraquant.edu",
                password_hash=hash_password("AstraquantSafePass2026!"),
                consent_given=True,
                is_onboarded=True,
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        h1 = session.query(Holding).filter(Holding.user_id == user.id, Holding.symbol == "RELIANCE").first()
        if not h1:
            session.add(Holding(user_id=user.id, symbol="RELIANCE", quantity=10, buy_price=2500.0))
        h2 = session.query(Holding).filter(Holding.user_id == user.id, Holding.symbol == "TCS").first()
        if not h2:
            session.add(Holding(user_id=user.id, symbol="TCS", quantity=5, buy_price=3800.0))
        prof = session.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if not prof:
            session.add(UserProfile(
                user_id=user.id,
                risk_score=55.0,
                suggested_profile="Moderate",
                holding_style="Balanced Growth & Core Stability",
                why_this_profile="Balanced investor profile derived from questionnaire responses.",
                diversification_score=70.0,
                concentration_status="Balanced",
            ))
        session.commit()
        yield user, session
    finally:
        session.close()


def collect_current_ui_snapshot(user, session):
    token = create_session_token(user.id)
    auth_headers = [(b"cookie", f"alphawatch_session={token}".encode("utf-8"))]
    anon_headers = []

    pages = [
        ("home", public.home, anon_headers, {}),
        ("how_it_works", public.how_it_works, anon_headers, {}),
        ("limitations", public.limitations, anon_headers, {}),
        ("terms", public.terms, anon_headers, {}),
        ("login", auth.login_form, anon_headers, {}),
        ("register", auth.register_form, anon_headers, {}),
        ("onboarding", onboarding.onboarding_form, auth_headers, {}),
        ("overview", dashboard.dashboard_overview, auth_headers, {}),
        ("predictions", dashboard.dashboard_predictions, auth_headers, {}),
        ("buy_candidates", dashboard.dashboard_buy_candidates, auth_headers, {}),
        ("market_trends", dashboard.dashboard_market_trends, auth_headers, {}),
        ("risk", dashboard.dashboard_risk, auth_headers, {}),
        ("backtest", dashboard.dashboard_backtest, auth_headers, {"symbol": "RELIANCE"}),
        ("model_performance", dashboard.dashboard_model_performance, auth_headers, {}),
        ("paper_trading", dashboard.dashboard_paper_trading, auth_headers, {}),
        ("auditor", dashboard.dashboard_auditor, auth_headers, {}),
        ("ripple", dashboard.dashboard_ripple, auth_headers, {"scenario": "crude_oil_spike"}),
        ("profile", dashboard.dashboard_profile, auth_headers, {}),
        ("settings", dashboard.dashboard_settings, auth_headers, {}),
    ]

    snapshot = {}
    for name, func, headers, kwargs in pages:
        scope = {"type": "http", "method": "GET", "path": f"/{name}", "headers": headers, "query_string": b""}
        req = Request(scope)
        res = Response()
        resp = func(req, res, db=session, **kwargs) if "db" not in kwargs else func(req, res, **kwargs)
        html = resp.body.decode("utf-8")
        snapshot[name] = extract_page_data(html)

    return snapshot


def test_ui_data_unchanged(setup_demo_user):
    user, session = setup_demo_user
    current_snapshot = collect_current_ui_snapshot(user, session)

    if not BASELINE_PATH.exists():
        with open(BASELINE_PATH, "w", encoding="utf-8") as f:
            json.dump(current_snapshot, f, indent=2, ensure_ascii=False)
        pytest.skip(f"Baseline generated at {BASELINE_PATH}. Re-run test to verify.")

    with open(BASELINE_PATH, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    # Validate all pages match
    differences = []
    for page_name, expected_data in baseline.items():
        assert page_name in current_snapshot, f"Page {page_name} missing from current UI snapshot"
        actual_data = current_snapshot[page_name]

        for section in ["table_cells", "stat_cards", "badges", "signal_rows", "risk_labels", "form_values", "form_fields", "link_targets", "as_of_and_data_sources"]:
            exp_val = expected_data.get(section, [])
            act_val = actual_data.get(section, [])
            if exp_val != act_val:
                differences.append(
                    f"[{page_name} -> {section}]\nExpected ({len(exp_val)} items): {exp_val[:5]}...\nActual ({len(act_val)} items): {act_val[:5]}..."
                )

    if differences:
        diff_str = "\n".join(differences)
        pytest.fail(f"UI data modified! Violates D1-SAFE presentation-only rules:\n{diff_str}")
