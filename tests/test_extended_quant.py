"""
Tests for Extended Quantitative Modules
ASTRAQUANT X 2026
"""

import pandas as pd
import pytest

from src.backtest import run_backtest
from src.optimize import optimize_portfolio
from src.benchmark import compare_with_nifty
from src.paper_trading import validate_paper_order, compute_paper_portfolio, PaperPortfolioSummary
from src.auditor import run_claim_audit
from src.ripple import simulate_ripple_scenario, SCENARIO_CONFIGS


def test_backtest_execution():
    # Synthetic test DataFrame with 50 bars
    dates = pd.date_range("2026-01-01", periods=60, freq="B").strftime("%Y-%m-%d")
    prices = [100.0 + i * 0.5 for i in range(60)]
    df = pd.DataFrame({
        "Date": dates,
        "Open": prices,
        "High": [p * 1.02 for p in prices],
        "Low": [p * 0.98 for p in prices],
        "Close": prices,
        "Volume": [100000] * 60,
    })
    # Add a signal column: Buy alternate 10 days
    df["Signal"] = [1 if (i // 10) % 2 == 0 else 0 for i in range(60)]

    result = run_backtest(df, symbol="TEST", initial_capital=100000.0)
    assert result.total_bars == 60
    assert result.initial_capital == 100000.0
    assert result.final_equity > 0
    assert len(result.equity_curve) == 60
    assert isinstance(result.total_return_pct, float)


def test_optimize_portfolio():
    result = optimize_portfolio(["RELIANCE", "TCS", "INFY"])
    assert len(result.symbols) >= 1
    assert result.equal_weight is not None
    assert result.min_variance is not None
    assert result.max_sharpe is not None
    assert isinstance(result.min_variance.sharpe_ratio, float)


def test_benchmark_comparison():
    res = compare_with_nifty(symbol="RELIANCE")
    assert res.symbol_or_portfolio == "RELIANCE"
    assert isinstance(res.beta, float)
    assert isinstance(res.alpha_pct, float)


def test_paper_trading_validation_and_computation():
    valid, msg, fee = validate_paper_order("BUY", "RELIANCE", 10, 2500.0, 50000.0, 0)
    assert valid is True
    assert fee > 0

    # Insufficient cash
    valid, msg, fee = validate_paper_order("BUY", "RELIANCE", 100, 2500.0, 5000.0, 0)
    assert valid is False

    # Mock trade objects
    class DummyTrade:
        def __init__(self, id, sym, act, qty, px, fee, date):
            self.id = id
            self.symbol = sym
            self.action = act
            self.quantity = qty
            self.price = px
            self.brokerage_stt = fee
            self.net_amount = qty * px
            self.trade_date = date
            self.notes = "test"

    trades = [
        DummyTrade(1, "RELIANCE", "BUY", 10, 2500.0, 37.5, "2026-02-01"),
        DummyTrade(2, "RELIANCE", "SELL", 5, 2600.0, 19.5, "2026-02-10"),
    ]
    summary = compute_paper_portfolio(trades)
    assert isinstance(summary, PaperPortfolioSummary)
    assert summary.total_trades_count == 2
    assert summary.realized_pnl > 0  # Sold 5 shares at 2600 bought at 2500
    assert len(summary.open_positions) == 1
    assert summary.open_positions[0].quantity == 5


def test_claim_auditor():
    res = run_claim_audit(symbols=["RELIANCE", "TCS"], max_records=20)
    assert res.total_audited_signals >= 0
    assert isinstance(res.brier_score, float)
    assert isinstance(res.buy_win_rate_pct, float)


def test_ripple_simulation():
    class DummyHolding:
        def __init__(self, sym, qty, px):
            self.symbol = sym
            self.quantity = qty
            self.buy_price = px

    holdings = [
        DummyHolding("RELIANCE", 10, 2500.0),
        DummyHolding("TCS", 5, 3800.0),
    ]
    res = simulate_ripple_scenario("crude_oil_spike", holdings)
    assert res.scenario_id == "crude_oil_spike"
    assert res.baseline_portfolio_value > 0
    assert len(res.holdings_impact) == 2
