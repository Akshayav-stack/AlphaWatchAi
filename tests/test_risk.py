"""
AlphaWatch AI — Quantitative Risk Subsystem Tests
ASTRAQUANT X 2026

Verifies:
  - Positive-loss convention across all risk measures (losses reported as positive numbers).
  - 5-point price series for returns and maximum drawdown (hand-calculated).
  - 20-point returns list for annualized volatility (hand-calculated with ddof=1 and sqrt(252)).
  - 100-point returns list for 1-day 95% VaR and CVaR (hand-calculated).
  - Portfolio risk aggregation from weighted returns.
  - Risk labelling:
      * Fewer-than-three stocks: fixed thresholds (vol < 20% Low, < 30% Medium, else High)
        and thresholds metadata returned for UI display.
      * Three or more stocks: tercile ranking split across average ranks.
"""

import math
import numpy as np
import pandas as pd
import pytest

from src.risk import (
    FIXED_VOLATILITY_THRESHOLDS,
    cvar_95_1d,
    label_risk,
    max_drawdown_1y,
    portfolio_risk,
    var_95_1d,
    volatility_20d,
)


def test_5_point_price_series_returns_and_drawdown():
    """
    Hand-calculated 5-point price series:
      Prices: P = [100.0, 105.0, 95.0, 110.0, 88.0]

    Returns calculation:
      r_01 = (105.0 - 100.0) / 100.0 = +5.0 / 100.0 = +0.05 (+5.0%)
      r_12 = (95.0 - 105.0)  / 105.0 = -10.0 / 105.0 = -2/21 = -0.095238... (-9.52%)
      r_23 = (110.0 - 95.0)  / 95.0  = +15.0 / 95.0  = +3/19 = +0.157895... (+15.79%)
      r_34 = (88.0 - 110.0)  / 110.0 = -22.0 / 110.0 = -0.20 (-20.0%)

    Drawdown progression (Positive-loss convention: dd >= 0.0):
      Step 0: Price = 100.0, Peak = 100.0, dd = (100 - 100) / 100 = 0.0
      Step 1: Price = 105.0, Peak = 105.0, dd = (105 - 105) / 105 = 0.0
      Step 2: Price = 95.0,  Peak = 105.0, dd = (105 - 95)  / 105 = 10/105 = 0.095238...
      Step 3: Price = 110.0, Peak = 110.0, dd = (110 - 110) / 110 = 0.0
      Step 4: Price = 88.0,  Peak = 110.0, dd = (110 - 88)  / 110 = 22/110 = 0.20 (20.0%)

    Expected Maximum Drawdown = 0.20 (20.0%).
    """
    prices = [100.0, 105.0, 95.0, 110.0, 88.0]

    # Verify manual return math
    rets = [
        (prices[1] - prices[0]) / prices[0],
        (prices[2] - prices[1]) / prices[1],
        (prices[3] - prices[2]) / prices[2],
        (prices[4] - prices[3]) / prices[3],
    ]
    assert pytest.approx(rets[0], rel=1e-5) == 0.05
    assert pytest.approx(rets[1], rel=1e-5) == -10.0 / 105.0
    assert pytest.approx(rets[2], rel=1e-5) == 15.0 / 95.0
    assert pytest.approx(rets[3], rel=1e-5) == -0.20

    # Test max_drawdown_1y
    mdd = max_drawdown_1y(prices)
    assert pytest.approx(mdd, rel=1e-5) == 0.20


def test_20_point_returns_list_volatility():
    """
    Hand-calculated 20-point returns list:
      R = [0.01, -0.01] repeated 10 times (10 gains of +1%, 10 losses of -1%).

    Mean return:
      mean = (10 * 0.01 + 10 * (-0.01)) / 20 = 0.0 / 20 = 0.0

    Sum of squared deviations:
      SS = 10 * (0.01 - 0.0)^2 + 10 * (-0.01 - 0.0)^2
         = 10 * 0.0001 + 10 * 0.0001
         = 0.001 + 0.001 = 0.002

    Sample variance (ddof=1):
      s^2 = SS / (N - 1) = 0.002 / (20 - 1) = 0.002 / 19 = 0.00010526315789...

    Sample standard deviation:
      s = sqrt(0.002 / 19) = 0.01025978352085...

    Annualized volatility (TRADING_DAYS = 252):
      vol = s * sqrt(252)
          = 0.01025978352085 * 15.874507866387544
          = 0.1628688434... (approx 16.29%)
    """
    rets_20 = [0.01, -0.01] * 10
    assert len(rets_20) == 20

    expected_s = math.sqrt(0.002 / 19.0)
    expected_ann_vol = expected_s * math.sqrt(252.0)

    computed_vol = volatility_20d(rets_20)
    assert pytest.approx(computed_vol, rel=1e-5) == expected_ann_vol
    assert pytest.approx(computed_vol, rel=1e-5) == 0.16286884


def test_100_point_returns_var_and_cvar():
    """
    Hand-calculated 100-point returns list for 95% 1-day VaR and CVaR.

    Returns setup:
      Indices 0 to 5 (6 points):
        r[0] = -0.09 (loss +0.09)
        r[1] = -0.08 (loss +0.08)
        r[2] = -0.07 (loss +0.07)
        r[3] = -0.06 (loss +0.06)
        r[4] = -0.05 (loss +0.05)
        r[5] = -0.05 (loss +0.05)
      Indices 6 to 99 (94 points):
        r[6..99] = +0.01 (gain +0.01, loss -0.01)

    Positive-Loss Convention:
      losses = [-r for r in rets]
      Lowest returns correspond to largest positive losses.

    VaR 95% Calculation:
      With N=100, 5th percentile return with r[4]=-0.05 and r[5]=-0.05 is exactly -0.05.
      Under positive-loss convention:
        VaR_95 = -(-0.05) = +0.05 (5.0% loss).

    CVaR 95% Calculation:
      Tail losses are all losses >= VaR_95 (+0.05):
        Tail losses: [0.09, 0.08, 0.07, 0.06, 0.05, 0.05] (6 points)
        Sum of tail losses = 0.09 + 0.08 + 0.07 + 0.06 + 0.05 + 0.05 = 0.40
        Mean tail loss = 0.40 / 6 = 0.06666667... (approx 6.67% loss).
    """
    tail = [-0.09, -0.08, -0.07, -0.06, -0.05, -0.05]
    rest = [0.01] * 94
    rets_100 = tail + rest
    assert len(rets_100) == 100

    var = var_95_1d(rets_100)
    assert pytest.approx(var, rel=1e-5) == 0.05

    cvar = cvar_95_1d(rets_100)
    expected_cvar = 0.40 / 6.0
    assert pytest.approx(cvar, rel=1e-5) == expected_cvar
    assert pytest.approx(cvar, rel=1e-5) == 0.06666667
    assert cvar >= var  # CVaR is always >= VaR


def test_portfolio_risk_aggregation():
    """Verify portfolio_risk computes weighted returns, volatility, VaR, and CVaR."""
    # Two identical assets with equal weight
    df_rets = pd.DataFrame({
        "A": [0.01, -0.01] * 10,
        "B": [0.01, -0.01] * 10,
    })
    weights = {"A": 0.5, "B": 0.5}

    res = portfolio_risk(df_rets, weights)
    assert "volatility" in res
    assert "var_95" in res
    assert "cvar_95" in res
    # Weighted returns are identical to individual returns
    assert pytest.approx(res["volatility"], rel=1e-4) == 0.16286884
    assert res["var_95"] > 0.0
    assert res["cvar_95"] >= res["var_95"]


def test_fewer_than_three_stocks_labelling():
    """
    If fewer than three stocks exist:
    Must use fixed thresholds (vol < 20% Low, < 30% Medium, else High)
    and return the thresholds used for UI display.
    """
    stocks_data = [
        {"symbol": "STOCK_LOW", "volatility_20d": 0.15, "max_drawdown_1y": 0.10, "var_95_1d": 0.02},
        {"symbol": "STOCK_MED", "volatility_20d": 0.25, "max_drawdown_1y": 0.20, "var_95_1d": 0.03},
    ]

    rows, thresholds = label_risk(stocks_data)

    assert len(rows) == 2
    assert rows[0]["symbol"] == "STOCK_LOW"
    assert rows[0]["risk_label"] == "Low"  # 0.15 < 0.20

    assert rows[1]["symbol"] == "STOCK_MED"
    assert rows[1]["risk_label"] == "Medium"  # 0.20 <= 0.25 < 0.30

    # High threshold verification
    high_stock = [{"symbol": "STOCK_HIGH", "volatility_20d": 0.35, "max_drawdown_1y": 0.30, "var_95_1d": 0.05}]
    high_rows, _ = label_risk(high_stock)
    assert high_rows[0]["risk_label"] == "High"  # >= 0.30

    # Verify thresholds dict is returned for UI presentation
    assert thresholds["metric"] == "annualized_volatility"
    assert thresholds["low_max"] == 0.20
    assert thresholds["medium_max"] == 0.30


def test_three_or_more_stocks_tercile_labelling():
    """
    If three or more stocks exist:
    Must use average rank across volatility, drawdown, and VaR to split into terciles.
    """
    stocks_data = [
        # Stock 1: clearly lowest risk across all 3 dimensions
        {"symbol": "STK1", "volatility_20d": 0.12, "max_drawdown_1y": 0.08, "var_95_1d": 0.015},
        # Stock 2: clearly medium risk
        {"symbol": "STK2", "volatility_20d": 0.22, "max_drawdown_1y": 0.18, "var_95_1d": 0.025},
        # Stock 3: clearly highest risk
        {"symbol": "STK3", "volatility_20d": 0.38, "max_drawdown_1y": 0.35, "var_95_1d": 0.050},
    ]

    rows, thresholds = label_risk(stocks_data)
    assert len(rows) == 3

    assert rows[0]["risk_label"] == "Low"
    assert rows[1]["risk_label"] == "Medium"
    assert rows[2]["risk_label"] == "High"

    assert thresholds["metric"] == "tercile_rank"
    assert thresholds["stock_count"] == 3
