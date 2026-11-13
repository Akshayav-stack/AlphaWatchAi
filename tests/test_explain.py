"""
Unit tests for AlphaWatch AI Decision Intelligence (Explainable AI / SHAP engine).
"""
import pytest
from src.explain import explain_trade_decision

def test_explain_trade_decision_structure():
    """Verify that explain_trade_decision returns a complete, schema-compliant dictionary."""
    res = explain_trade_decision("RELIANCE")
    assert res is not None
    assert res.get("status") == "success"
    assert res.get("symbol") == "RELIANCE"
    assert res.get("signal") in ["BUY", "HOLD", "SELL"]
    assert 0.0 <= res.get("probability_up") <= 1.0
    assert 0.0 <= res.get("current_price") > 0
    assert "as_of_date" in res
    
    # Check probability meter
    meter = res.get("probability_meter", {})
    assert meter.get("tier") in ["Higher", "Moderate", "Lower"]
    assert 0 <= meter.get("probability_pct") <= 100
    assert "disclaimer" in meter

    # Check top features (SHAP)
    top_features = res.get("top_features", [])
    assert len(top_features) > 0
    for feat in top_features:
        assert "feature" in feat
        assert "label" in feat
        assert "shap_value" in feat
        assert "direction" in feat
        assert feat["direction"] in ["Positive", "Negative"]
        assert "raw_value" in feat
        assert "explanation" in feat

    # Check factors
    assert "positive_factors" in res
    assert "negative_factors" in res
    assert isinstance(res["positive_factors"], list)
    assert isinstance(res["negative_factors"], list)

    # Check risk warnings and AI summary
    assert "risk_warnings" in res
    assert isinstance(res["risk_warnings"], list)
    assert "dynamic_explanation" in res
    assert "final_summary" in res

def test_explain_trade_decision_different_symbols():
    """Verify distinct model signals and explanations for different stocks."""
    res_rel = explain_trade_decision("RELIANCE")
    res_tcs = explain_trade_decision("TCS")
    
    assert res_rel["symbol"] == "RELIANCE"
    assert res_tcs["symbol"] == "TCS"
    # Prices and features should differ
    assert res_rel.get("current_price") != res_tcs.get("current_price")

def test_explain_trade_decision_fallback():
    """Verify graceful handling for unsupported tickers with missing data."""
    res = explain_trade_decision("UNKNOWN_SYM")
    assert res["status"] == "error"
    assert res["symbol"] == "UNKNOWN_SYM"
    assert "Insufficient price history" in res["message"]

