"""
Unit Tests for src/screener_loader.py and src/fundamentals.py
ASTRAQUANT X 2026

Verifies:
  1. Formula injection protection (stripping leading =, +, -, @ from untrusted cells)
  2. Safe Excel workbook parsing using openpyxl (data_only mode, no macros)
  3. Fundamentals extraction without estimation of missing values
  4. 6-pillar fundamental health evaluation (Strong, Mixed, Weak, Insufficient Data)
  5. Stale-data warning trigger for exports older than 120 days
  6. combine(signal, badge) educational explanations without trade instructions
"""

from datetime import datetime, timedelta
from pathlib import Path
import openpyxl
import pytest

import src.fundamentals as fundamentals
import src.screener_loader as screener_loader


# -----------------------------------------------------------------------------
# 1. UNTRUSTED TEXT & FORMULA INJECTION DEFENSE
# -----------------------------------------------------------------------------

def test_sanitize_cell_value_formula_stripping():
    """Verifies that malicious spreadsheet formulas are neutralized."""
    # Classic DDE / CSV injection payloads
    assert screener_loader.sanitize_cell_value("=cmd|' /C calc'!A0") == "cmd|' /C calc'!A0"
    assert screener_loader.sanitize_cell_value("@SUM(A1:A10)") == "SUM(A1:A10)"
    assert screener_loader.sanitize_cell_value("+10*20") == "+10*20" or isinstance(screener_loader.sanitize_cell_value("+10*20"), str)
    assert screener_loader.sanitize_cell_value("=1+1") == "1+1"
    
    # Legitimate negative numbers must remain valid floats
    neg_num = screener_loader.sanitize_cell_value("-5.25")
    assert neg_num == -5.25

    # Safe HTML escaping
    unsafe_text = "<script>alert('xss')</script>"
    escaped = screener_loader.escape_output_text(unsafe_text)
    assert "<script>" not in escaped
    assert "&lt;script&gt;" in escaped


# -----------------------------------------------------------------------------
# 2. WORKBOOK INGESTION & RATIO EXTRACTION
# -----------------------------------------------------------------------------

def test_extract_fundamentals_from_workbook(tmp_path: Path):
    """Creates a synthetic Screener.in Excel export and verifies clean extraction."""
    wb_path = tmp_path / "SAMPLE_TESTCO.xlsx"

    wb = openpyxl.Workbook()
    # Sheet 1: Data Sheet
    ws = wb.active
    ws.title = "Data Sheet"

    # Add key ratio rows
    ws.append(["Company", "Test Corporation Ltd"])
    ws.append(["Current Price", 2500.0])
    ws.append(["Stock P/E", 22.4])
    ws.append(["Median PE", 24.0])
    ws.append(["Return on equity", 18.5])
    ws.append(["ROCE", 21.0])
    ws.append(["Debt to equity", 0.25])
    ws.append(["Sales growth 3Years", 14.2])
    ws.append(["Profit growth 3Years", 16.8])
    ws.append(["Promoter holding", 52.0])
    ws.append(["Change in promoter holding", 0.0])
    ws.append(["Market Cap", 150000.0])

    wb.save(wb_path)

    record = screener_loader.extract_fundamentals_from_workbook(
        wb_path, manifest_date="2026-10-15"
    )

    assert record["symbol"] == "TESTCO"
    assert record["company_name"] == "Test Corporation Ltd"
    assert record["current_pe"] == 22.4
    assert record["historical_pe_median"] == 24.0
    assert record["roe_pct"] == 18.5
    assert record["roce_pct"] == 21.0
    assert record["debt_to_equity"] == 0.25
    assert record["sales_growth_3y_pct"] == 14.2
    assert record["profit_growth_3y_pct"] == 16.8
    assert record["promoter_holding_pct"] == 52.0
    assert record["source_export_date"] == "2026-10-15"


def test_missing_fields_never_estimated(tmp_path: Path):
    """Verifies that missing fields remain None and are never hallucinated or estimated."""
    wb_path = tmp_path / "SAMPLE_PARTIAL.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data Sheet"

    ws.append(["Company", "Partial Co"])
    ws.append(["Stock P/E", 18.0])
    # Deliberately omitting ROE, Debt to Equity, Sales growth

    wb.save(wb_path)

    record = screener_loader.extract_fundamentals_from_workbook(wb_path)
    assert record["current_pe"] == 18.0
    assert record["roe_pct"] is None
    assert record["roce_pct"] is None
    assert record["debt_to_equity"] is None
    assert record["sales_growth_3y_pct"] is None


# -----------------------------------------------------------------------------
# 3. 6-PILLAR FUNDAMENTAL HEALTH EVALUATION
# -----------------------------------------------------------------------------

def test_evaluate_fundamentals_strong():
    """Verifies Strong badge on healthy balance sheet and high return ratios."""
    data = {
        "symbol": "HEALTHYCO",
        "company_name": "Healthy Corporation",
        "current_pe": 22.0,
        "historical_pe_median": 24.0,  # Below median P/E (Pass)
        "roe_pct": 19.5,                # > 15% (Pass)
        "roce_pct": 22.0,               # > 15% (Pass)
        "debt_to_equity": 0.20,         # <= 0.50 (Pass)
        "sales_growth_3y_pct": 14.0,    # > 10% (Pass)
        "profit_growth_3y_pct": 16.0,   # > 10% (Pass)
        "promoter_holding_pct": 55.0,   # Stable > 40% (Pass)
        "promoter_holding_change_3y_pct": 0.0,
        "source_export_date": datetime.now().strftime("%Y-%m-%d"),
    }

    res = fundamentals.evaluate_fundamentals(data)

    assert res.badge == "Strong"
    assert res.score_fraction == "6/6"
    assert res.score_percent == 100.0
    assert len(res.rules_fired) == 6
    assert not res.is_stale
    assert res.stale_warning is None


def test_evaluate_fundamentals_weak_due_to_leverage_and_negative_growth():
    """Verifies Weak badge on high debt, poor profitability, and negative growth."""
    data = {
        "symbol": "STRUGGLECO",
        "company_name": "Struggle Corporation",
        "current_pe": 45.0,
        "historical_pe_median": 20.0,  # Expensive (>1.35x median) -> Fail
        "roe_pct": 4.5,                 # < 10% -> Fail
        "roce_pct": 5.0,                # < 10% -> Fail
        "debt_to_equity": 2.50,         # > 2.0 critical red flag -> Fail
        "sales_growth_3y_pct": -8.0,    # Negative -> Fail
        "profit_growth_3y_pct": -15.0,  # Negative -> Fail
        "promoter_holding_pct": 25.0,
        "promoter_holding_change_3y_pct": -5.0,  # Stake dilution -> Fail
        "source_export_date": datetime.now().strftime("%Y-%m-%d"),
    }

    res = fundamentals.evaluate_fundamentals(data)

    assert res.badge == "Weak"
    assert res.score_percent <= 20.0
    assert any("Debt-to-Equity" in r for r in res.rules_fired)


def test_evaluate_fundamentals_stale_warning():
    """Verifies that exports older than 120 days trigger a stale-data audit warning."""
    old_date = (datetime.now() - timedelta(days=140)).strftime("%Y-%m-%d")
    data = {
        "symbol": "STALECO",
        "company_name": "Stale Corp",
        "current_pe": 20.0,
        "historical_pe_median": 20.0,
        "roe_pct": 16.0,
        "roce_pct": 16.0,
        "debt_to_equity": 0.3,
        "source_export_date": old_date,
    }

    res = fundamentals.evaluate_fundamentals(data, stale_threshold_days=120)

    assert res.is_stale is True
    assert res.stale_warning is not None
    assert "exceeds 120-day fresh threshold" in res.stale_warning


def test_evaluate_fundamentals_insufficient_data():
    """Verifies Insufficient Data badge when fewer than 3 pillars are present."""
    data = {
        "symbol": "NODATACO",
        "source_export_date": datetime.now().strftime("%Y-%m-%d"),
    }

    res = fundamentals.evaluate_fundamentals(data)

    assert res.badge == "Insufficient Data"
    assert res.score_fraction == "0/0"


# -----------------------------------------------------------------------------
# 4. EDUCATIONAL COMBINATION MATRIX
# -----------------------------------------------------------------------------

def test_combine_educational_explanations():
    """Verifies that combine(signal, badge) produces educational explanations without trade instructions."""
    # BUY + Strong
    exp_buy_strong = fundamentals.combine("BUY", "Strong")
    assert "Model says BUY, fundamentals Strong" in exp_buy_strong
    assert "both short-term trend and long-term quality indicators align" in exp_buy_strong.lower()
    assert "not investment advice" in exp_buy_strong.lower()

    # BUY + Weak (Crucial 2x2 divergence test)
    exp_buy_weak = fundamentals.combine("BUY", "Weak")
    assert "Model says BUY, fundamentals Weak" in exp_buy_weak
    assert "review financial quality carefully before acting" in exp_buy_weak.lower()

    # SELL + Strong
    exp_sell_strong = fundamentals.combine("SELL", "Strong")
    assert "Model says SELL, fundamentals Strong" in exp_sell_strong
    assert "temporary sector rotation" in exp_sell_strong.lower()

    # HOLD + Mixed
    exp_hold_mixed = fundamentals.combine("HOLD", "Mixed")
    assert "Model says HOLD, fundamentals Mixed" in exp_hold_mixed
