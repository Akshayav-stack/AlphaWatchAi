"""
AlphaWatch AI — Portfolio Subsystem & Accounting Tests
ASTRAQUANT X 2026

Verifies:
  - Holding dataclass validation:
      * Quantity must be a positive whole integer (>0)
      * Buy price must be strictly positive (>0)
      * Portfolio duplicate symbol rejection
  - Two-stock portfolio for weights and profit or loss (hand-calculated).
  - Concentration alert boundary:
      * Stock at exactly 30.0% -> NO alert
      * Stock at 31.0% -> Concentration alert triggered
  - Missing file handling: raises FileNotFoundError, never fakes data.
  - run_analysis execution:
      * Returns symbol, probability_up, signal, risk_label, reason, model_version
      * Reason string contains only computed values (5d return, 20d return, RSI, volatility)
  - DEMO_PORTFOLIOS constant:
      * Contains 3 distinct demo portfolios with validated Holding items.
"""

from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from src.features import FEATURE_COLUMNS
from src.portfolio import (
    DEMO_PORTFOLIOS,
    Holding,
    concentration_alert,
    get_portfolio_valuation,
    portfolio_pnl,
    portfolio_value,
    portfolio_weights,
    run_analysis,
    validate_portfolio,
)


def test_holding_validation():
    """Verify input validation on Holding dataclass."""
    # Valid holding
    h = Holding(symbol="tcs", quantity=10, buy_price=3500.0)
    assert h.symbol == "TCS"
    assert h.quantity == 10
    assert h.buy_price == 3500.0

    # Non-integer / non-positive quantity rejected
    with pytest.raises(ValueError, match="Quantity must be a whole positive integer"):
        Holding(symbol="INFY", quantity=0, buy_price=1500.0)

    with pytest.raises(ValueError, match="Quantity must be a whole positive integer"):
        Holding(symbol="INFY", quantity=-5, buy_price=1500.0)

    with pytest.raises(ValueError, match="Quantity must be a whole positive integer"):
        Holding(symbol="INFY", quantity=10.5, buy_price=1500.0)  # type: ignore

    # Non-positive buy price rejected
    with pytest.raises(ValueError, match="Buy price must be strictly positive"):
        Holding(symbol="INFY", quantity=10, buy_price=0.0)

    with pytest.raises(ValueError, match="Buy price must be strictly positive"):
        Holding(symbol="INFY", quantity=10, buy_price=-100.0)

    # Empty symbol rejected
    with pytest.raises(ValueError, match="Symbol must be a non-empty string"):
        Holding(symbol="", quantity=10, buy_price=100.0)


def test_portfolio_duplicate_rejection():
    """Duplicate symbols in a portfolio must raise ValueError."""
    h1 = Holding(symbol="RELIANCE", quantity=10, buy_price=2500.0)
    h2 = Holding(symbol="TCS", quantity=5, buy_price=3500.0)
    h3 = Holding(symbol="RELIANCE", quantity=15, buy_price=2600.0)

    with pytest.raises(ValueError, match="Duplicate symbol detected"):
        validate_portfolio([h1, h2, h3])


def test_two_stock_portfolio_weights_and_pnl(tmp_path):
    """
    Hand-calculated two-stock portfolio:
      Holding A (STOCKA): 10 shares, buy price = 100.0, latest close = 120.0
      Holding B (STOCKB): 20 shares, buy price = 50.0,  latest close = 40.0

    Hand calculations:
      Cost Basis A = 10 * 100.0 = 1000.0
      Current Value A = 10 * 120.0 = 1200.0
      Unrealized P&L A = 1200.0 - 1000.0 = +200.0 (+20.0%)

      Cost Basis B = 20 * 50.0 = 1000.0
      Current Value B = 20 * 40.0 = 800.0
      Unrealized P&L B = 800.0 - 1000.0 = -200.0 (-20.0%)

      Total Cost Basis = 1000.0 + 1000.0 = 2000.0
      Total Current Value = 1200.0 + 800.0 = 2000.0
      Total Unrealized P&L = 2000.0 - 2000.0 = 0.0 (0.0%)

      Portfolio Weight A = 1200.0 / 2000.0 = 0.60 (60.0%)
      Portfolio Weight B = 800.0 / 2000.0  = 0.40 (40.0%)
    """
    # Create test CSV price files with required columns for data_loader
    df_a = pd.DataFrame({
        "Date": pd.date_range("2026-01-01", periods=5),
        "Open": [100.0, 105.0, 110.0, 115.0, 120.0],
        "High": [102.0, 107.0, 112.0, 117.0, 122.0],
        "Low": [98.0, 103.0, 108.0, 113.0, 118.0],
        "Close": [100.0, 105.0, 110.0, 115.0, 120.0],
        "Volume": [1000] * 5,
    })
    df_a.to_csv(tmp_path / "STOCKA.csv", index=False)

    df_b = pd.DataFrame({
        "Date": pd.date_range("2026-01-01", periods=5),
        "Open": [50.0, 48.0, 45.0, 42.0, 40.0],
        "High": [52.0, 50.0, 47.0, 44.0, 42.0],
        "Low": [48.0, 46.0, 43.0, 40.0, 38.0],
        "Close": [50.0, 48.0, 45.0, 42.0, 40.0],
        "Volume": [1000] * 5,
    })
    df_b.to_csv(tmp_path / "STOCKB.csv", index=False)

    portfolio = [
        Holding(symbol="STOCKA", quantity=10, buy_price=100.0),
        Holding(symbol="STOCKB", quantity=20, buy_price=50.0),
    ]

    val = get_portfolio_valuation(portfolio, processed_dir=tmp_path)

    # Assert exact hand-calculated figures
    assert val["total_cost"] == 2000.0
    assert val["total_value"] == 2000.0
    assert val["unrealized_pnl"] == 0.0
    assert val["unrealized_pnl_pct"] == 0.0

    # Weights
    assert val["weights"]["STOCKA"] == 0.60
    assert val["weights"]["STOCKB"] == 0.40

    # Individual holdings PnL
    assert val["holding_pnl"]["STOCKA"]["pnl"] == 200.0
    assert val["holding_pnl"]["STOCKA"]["pnl_pct"] == 20.0
    assert val["holding_pnl"]["STOCKB"]["pnl"] == -200.0
    assert val["holding_pnl"]["STOCKB"]["pnl_pct"] == -20.0

    # Helper functions
    assert portfolio_value(portfolio, processed_dir=tmp_path) == 2000.0
    assert portfolio_weights(portfolio, processed_dir=tmp_path)["STOCKA"] == 0.60
    assert portfolio_pnl(portfolio, processed_dir=tmp_path)["unrealized_pnl"] == 0.0


def test_concentration_alert_30_vs_31_percent(tmp_path):
    """
    Hand-calculated concentration alert test:
      Portfolio total value = 10,000.

      Case 1: Stock at exactly 30.0% of total value:
        Stock A = 3,000 (30.0%), Stock B = 7,000 (70.0%)
        Prudential rule: alert strictly when weight > 30.0%.
        Stock A (30.0%) must NOT trigger an alert for Stock A.

      Case 2: Stock at 31.0% of total value:
        Stock A = 3,100 (31.0%), Stock B = 6,900 (69.0%)
        Stock A (31.0% > 30.0%) MUST trigger an alert.
    """
    # 1. Exactly 30.0% for Stock A
    # Stock A: 30 shares @ 100 = 3,000 (30.0%)
    # Stock B: 70 shares @ 100 = 7,000 (70.0%)
    df_a = pd.DataFrame({
        "Date": ["2026-11-13"],
        "Open": [100.0],
        "High": [100.0],
        "Low": [100.0],
        "Close": [100.0],
        "Volume": [1000],
    })
    df_a.to_csv(tmp_path / "STKA.csv", index=False)
    df_b = pd.DataFrame({
        "Date": ["2026-11-13"],
        "Open": [100.0],
        "High": [100.0],
        "Low": [100.0],
        "Close": [100.0],
        "Volume": [1000],
    })
    df_b.to_csv(tmp_path / "STKB.csv", index=False)

    port_30 = [
        Holding(symbol="STKA", quantity=30, buy_price=100.0),
        Holding(symbol="STKB", quantity=70, buy_price=100.0),
    ]
    alerts_30 = concentration_alert(port_30, processed_dir=tmp_path)
    alert_symbols_30 = [a["symbol"] for a in alerts_30]
    # STKA is at exactly 30.0%, so no alert for STKA
    assert "STKA" not in alert_symbols_30
    # STKB is at 70.0% > 30%, so STKB triggers
    assert "STKB" in alert_symbols_30

    # 2. Exactly 31.0% for Stock A
    # Stock A: 31 shares @ 100 = 3,100 (31.0%)
    # Stock B: 69 shares @ 100 = 6,900 (69.0%)
    port_31 = [
        Holding(symbol="STKA", quantity=31, buy_price=100.0),
        Holding(symbol="STKB", quantity=69, buy_price=100.0),
    ]
    alerts_31 = concentration_alert(port_31, processed_dir=tmp_path)
    alert_symbols_31 = [a["symbol"] for a in alerts_31]
    # STKA is at 31.0% > 30.0%, so STKA triggers alert!
    assert "STKA" in alert_symbols_31
    assert any("STKA" in a["message"] for a in alerts_31)


def test_missing_price_csv_raises_error(tmp_path):
    """If a saved CSV is missing, raise FileNotFoundError. Never fake a result."""
    portfolio = [Holding(symbol="NONEXISTENT", quantity=10, buy_price=100.0)]
    with pytest.raises(FileNotFoundError, match="Missing saved price data"):
        get_portfolio_valuation(portfolio, processed_dir=tmp_path)


def test_demo_portfolios_constant():
    """Verify DEMO_PORTFOLIOS contains 3 distinct valid portfolios."""
    assert len(DEMO_PORTFOLIOS) == 3
    for name, port in DEMO_PORTFOLIOS.items():
        assert len(port) >= 2
        validate_portfolio(port)
        for h in port:
            assert isinstance(h, Holding)
            assert h.quantity > 0
            assert h.buy_price > 0.0


def test_run_analysis_and_reason_string(tmp_path):
    """
    Verify run_analysis executes end-to-end, returns all expected keys,
    builds the reason string strictly from computed values, and raises
    clear errors if files or models are missing.
    """
    models_dir = tmp_path / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    processed_dir = tmp_path / "data"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 1. Missing model raises FileNotFoundError (never fake results)
    sym = "TESTSYM"
    dates = pd.date_range("2025-01-01", periods=60)
    df_stock = pd.DataFrame({
        "Date": dates,
        "Open": np.linspace(100, 150, 60),
        "High": np.linspace(102, 152, 60),
        "Low": np.linspace(98, 148, 60),
        "Close": np.linspace(100, 150, 60),
        "Volume": [100000] * 60,
        "DeliveryQty": [50000] * 60,
    })
    df_stock.to_csv(processed_dir / f"{sym}.csv", index=False)

    port = [Holding(symbol=sym, quantity=20, buy_price=120.0)]

    # Missing model error test
    with pytest.raises(FileNotFoundError, match="Missing saved model"):
        run_analysis(port, profile="Moderate", processed_dir=processed_dir, models_dir=models_dir)

    # 2. Create minimal saved model bundle
    X_dummy = np.random.RandomState(42).randn(50, len(FEATURE_COLUMNS))
    y_dummy = np.random.RandomState(42).randint(0, 2, 50)
    X_df = pd.DataFrame(X_dummy, columns=FEATURE_COLUMNS)
    scaler = StandardScaler().fit(X_df)
    base_rf = RandomForestClassifier(n_estimators=5, random_state=42)
    cal_model = CalibratedClassifierCV(estimator=base_rf, cv=2)
    cal_model.fit(scaler.transform(X_df), y_dummy)

    bundle = {
        "calibrated_model": cal_model,
        "scaler": scaler,
        "feature_names": FEATURE_COLUMNS,
        "version": "1.0.0",
    }
    joblib.dump(bundle, models_dir / f"{sym}_rf.joblib")

    # Run analysis
    results = run_analysis(
        port,
        profile="Moderate",
        processed_dir=processed_dir,
        models_dir=models_dir,
    )

    assert len(results) == 1
    res = results[0]
    assert res["symbol"] == sym
    assert "probability_up" in res
    assert 0.0 <= res["probability_up"] <= 1.0
    assert res["signal"] in ("BUY", "HOLD", "SELL")
    assert res["risk_label"] in ("Low", "Medium", "High")
    assert res["model_version"] == "1.0.0"

    # Verify reason string is built strictly from computed values (5d return, 20d return, RSI, volatility)
    reason = res["reason"]
    assert "RSI(14)" in reason
    assert "5-day return" in reason
    assert "20-day return" in reason
    assert "20-day annualized volatility" in reason
