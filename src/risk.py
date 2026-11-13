"""
AlphaWatch AI — Quantitative Portfolio Risk Subsystem
ASTRAQUANT X 2026

POSITIVE-LOSS CONVENTION:
Throughout this module and system, risk is reported under the positive-loss convention:
  - A loss is reported as a positive number (e.g., a 2.5% decline in value is loss = +0.025 or +2.5%).
  - Value at Risk (VaR 95%) is the positive threshold loss such that 95% of daily losses are smaller.
  - Conditional Value at Risk (CVaR 95% / Expected Shortfall) is the positive average loss when losses >= VaR.
  - Maximum Drawdown is the positive percentage drop from the running peak (e.g., 0.20 for a 20% drawdown).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

from src.data_loader import load_nifty50, load_prices

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIR_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Annualized Indian risk-free rate assumption (RBI repo rate 6.50%)
RISK_FREE_RATE_ANNUAL = 0.065
TRADING_DAYS_PER_YEAR = 252

# Fixed volatility thresholds for portfolios with fewer than 3 stocks
FIXED_VOLATILITY_THRESHOLDS: Dict[str, Any] = {
    "metric": "annualized_volatility",
    "low_max": 0.20,
    "medium_max": 0.30,
    "description": "Annualized volatility under 20% is Low, under 30% is Medium, otherwise High",
}


def volatility_20d(returns: Union[pd.Series, Sequence[float]]) -> float:
    """
    Computes annualized historical volatility from the last 20 daily returns.
    Uses sample standard deviation with ddof=1 scaled by sqrt(252).

    Args:
        returns: Daily percentage returns (e.g., pd.Series or list of floats).

    Returns:
        Annualized volatility as a positive float.
    """
    ret_list = [float(x) for x in returns]
    if len(ret_list) < 2:
        return 0.0
    window = ret_list[-20:]
    std = float(np.std(window, ddof=1))
    return float(std * np.sqrt(TRADING_DAYS_PER_YEAR))


def max_drawdown_1y(closes: Union[pd.Series, Sequence[float]]) -> float:
    """
    Computes maximum peak-to-trough drawdown from the running peak over the last 252 closes.

    Follows the positive-loss convention: drawdown is returned as a positive fraction
    (e.g., 0.20 indicates a 20% decline from peak).

    Args:
        closes: Historical closing prices.

    Returns:
        Maximum drawdown as a positive float >= 0.0.
    """
    close_list = [float(x) for x in closes]
    if len(close_list) < 2:
        return 0.0
    window = close_list[-252:]
    peak = window[0]
    max_dd = 0.0
    for price in window:
        if price > peak:
            peak = price
        elif peak > 0.0:
            dd = (peak - price) / peak
            if dd > max_dd:
                max_dd = dd
    return float(max_dd)


def var_95_1d(returns: Union[pd.Series, Sequence[float]]) -> float:
    """
    Computes 1-day 95% historical Value at Risk (VaR) under the positive-loss convention.

    A 5th-percentile daily return of -0.025 yields a positive loss of +0.025.

    Args:
        returns: Historical daily returns.

    Returns:
        Positive float representing the 1-day 95% VaR loss.
    """
    ret_list = [float(x) for x in returns]
    if not ret_list:
        return 0.0
    # 5th percentile of return negated = 95th percentile of loss
    ret_5th = float(np.percentile(ret_list, 5))
    var = -ret_5th
    return float(max(0.0, var))


def cvar_95_1d(returns: Union[pd.Series, Sequence[float]]) -> float:
    """
    Computes 1-day 95% Conditional Value at Risk (CVaR / Expected Shortfall).

    Under the positive-loss convention, CVaR is the average loss of all observations
    at or beyond the 95% VaR threshold.

    Args:
        returns: Historical daily returns.

    Returns:
        Positive float representing expected tail loss beyond VaR.
    """
    ret_list = [float(x) for x in returns]
    if not ret_list:
        return 0.0
    var = var_95_1d(ret_list)
    # Tail returns are those where -r >= var (i.e. r <= -var)
    tail_losses = [-r for r in ret_list if (-r) >= var - 1e-12]
    if not tail_losses:
        return var
    mean_tail = float(np.mean(tail_losses))
    return float(max(var, mean_tail))


def portfolio_risk(
    returns_df: pd.DataFrame,
    weights: Union[Dict[str, float], Sequence[float]],
) -> Dict[str, float]:
    """
    Computes annualized volatility, 1-day 95% VaR, and 1-day 95% CVaR
    from weighted portfolio returns.

    Args:
        returns_df: DataFrame where each column is an asset's daily returns.
        weights: Dictionary mapping column names to weights, or list of weights.

    Returns:
        Dict with keys: 'volatility', 'var_95', 'cvar_95' (all positive floats).
    """
    if returns_df.empty:
        return {"volatility": 0.0, "var_95": 0.0, "cvar_95": 0.0}

    if isinstance(weights, dict):
        w = np.array([float(weights.get(col, 0.0)) for col in returns_df.columns])
    else:
        w = np.array([float(x) for x in weights])

    total_w = float(np.sum(w))
    if total_w > 0:
        w = w / total_w

    port_returns = returns_df.dot(w)
    vol = float(np.std(port_returns, ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)) if len(port_returns) >= 2 else 0.0
    var = var_95_1d(port_returns)
    cvar = cvar_95_1d(port_returns)

    return {
        "volatility": vol,
        "var_95": var,
        "cvar_95": cvar,
    }


def label_risk(
    stocks_risk_data: Union[Sequence[Dict[str, Any]], pd.DataFrame],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Labels risk for each stock.
    - If >= 3 stocks: uses average rank of volatility, drawdown, and VaR across the stocks,
      split into Low, Medium, and High terciles.
    - If < 3 stocks: uses fixed thresholds (annualized volatility < 20% Low, < 30% Medium, otherwise High),
      and returns the thresholds used so the UI can display them.

    Output per stock: symbol, volatility_20d, max_drawdown_1y, var_95_1d, risk_label.

    Args:
        stocks_risk_data: List of dicts or DataFrame with symbol, volatility_20d, max_drawdown_1y, var_95_1d.

    Returns:
        Tuple of (list_of_enriched_rows, thresholds_info_dict).
    """
    if isinstance(stocks_risk_data, pd.DataFrame):
        records = stocks_risk_data.to_dict(orient="records")
    else:
        records = [dict(s) for s in stocks_risk_data]

    if not records:
        return [], FIXED_VOLATILITY_THRESHOLDS

    n = len(records)
    if n < 3:
        # Fixed thresholds path (< 3 stocks)
        rows: List[Dict[str, Any]] = []
        for r in records:
            vol = float(r.get("volatility_20d", 0.0))
            if vol < 0.20:
                label = "Low"
            elif vol < 0.30:
                label = "Medium"
            else:
                label = "High"
            rows.append({
                "symbol": str(r.get("symbol", "")).upper(),
                "volatility_20d": float(r.get("volatility_20d", 0.0)),
                "max_drawdown_1y": float(r.get("max_drawdown_1y", 0.0)),
                "var_95_1d": float(r.get("var_95_1d", 0.0)),
                "risk_label": label,
            })
        return rows, FIXED_VOLATILITY_THRESHOLDS

    # Tercile ranking path (>= 3 stocks)
    vols = [float(r.get("volatility_20d", 0.0)) for r in records]
    dds = [float(r.get("max_drawdown_1y", 0.0)) for r in records]
    vars_ = [float(r.get("var_95_1d", 0.0)) for r in records]

    # Rank 1 to n (lowest risk has lowest rank)
    rank_vol = pd.Series(vols).rank(method="average").tolist()
    rank_dd = pd.Series(dds).rank(method="average").tolist()
    rank_var = pd.Series(vars_).rank(method="average").tolist()

    avg_ranks = [(rank_vol[i] + rank_dd[i] + rank_var[i]) / 3.0 for i in range(n)]
    rank_series = pd.Series(avg_ranks)
    pct_ranks = (rank_series.rank(method="average") - 1) / (n - 1) if n > 1 else [0.0]

    rows = []
    for i, r in enumerate(records):
        pr = pct_ranks[i]
        if pr < 1.0 / 3.0:
            label = "Low"
        elif pr < 2.0 / 3.0:
            label = "Medium"
        else:
            label = "High"

        rows.append({
            "symbol": str(r.get("symbol", "")).upper(),
            "volatility_20d": float(r.get("volatility_20d", 0.0)),
            "max_drawdown_1y": float(r.get("max_drawdown_1y", 0.0)),
            "var_95_1d": float(r.get("var_95_1d", 0.0)),
            "risk_label": label,
        })

    tercile_info: Dict[str, Any] = {
        "metric": "tercile_rank",
        "stock_count": n,
        "description": "Cross-sectional tercile split by average rank of volatility, drawdown, and VaR (Lowest third Low, Middle third Medium, Top third High)",
    }
    return rows, tercile_info



@dataclass
class AssetRiskProfile:
    """Individual stock risk metrics."""
    symbol: str
    weight_pct: float
    annualized_volatility: float
    beta: Optional[float]
    var_95_1d_pct: float
    risk_label: str  # 'Low', 'Medium', 'High'


@dataclass
class PortfolioRiskReport:
    """Comprehensive portfolio risk assessment."""
    portfolio_value: float
    annualized_volatility: float
    var_95_1d_pct: float
    var_95_1d_inr: float
    cvar_95_1d_pct: float
    cvar_95_1d_inr: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    portfolio_beta: Optional[float]
    asset_profiles: List[AssetRiskProfile]
    as_of_date: str
    source_report: str
    has_sufficient_history: bool


def compute_portfolio_risk(
    holdings_data: List[Dict[str, Any]],
    processed_dir: Path = DIR_PROCESSED,
) -> PortfolioRiskReport:
    """
    Computes mathematical risk metrics for a user's holdings based on saved daily returns.
    """
    source_report = "Saved Historical Bhavcopy & NIFTY 50 Series"

    if not holdings_data:
        return PortfolioRiskReport(
            portfolio_value=0.0,
            annualized_volatility=0.0,
            var_95_1d_pct=0.0,
            var_95_1d_inr=0.0,
            cvar_95_1d_pct=0.0,
            cvar_95_1d_inr=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown_pct=0.0,
            portfolio_beta=None,
            asset_profiles=[],
            as_of_date="N/A",
            source_report=source_report,
            has_sufficient_history=False,
        )

    # Load price series for all holdings
    series_dict: Dict[str, pd.Series] = {}
    quantities: Dict[str, int] = {}
    latest_prices: Dict[str, float] = {}
    latest_dates: List[str] = []

    for h in holdings_data:
        sym = str(h.get("symbol", "")).strip().upper()
        qty = int(h.get("quantity", 0))
        quantities[sym] = qty

        df, _ = load_prices(sym, processed_dir=processed_dir)
        if not df.empty and "Close" in df.columns:
            s = df.set_index("Date")["Close"]
            series_dict[sym] = s
            latest_prices[sym] = float(s.iloc[-1])
            latest_dates.append(str(s.index[-1]))

    if not series_dict:
        return PortfolioRiskReport(
            portfolio_value=0.0,
            annualized_volatility=0.0,
            var_95_1d_pct=0.0,
            var_95_1d_inr=0.0,
            cvar_95_1d_pct=0.0,
            cvar_95_1d_inr=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown_pct=0.0,
            portfolio_beta=None,
            asset_profiles=[],
            as_of_date="N/A",
            source_report=source_report,
            has_sufficient_history=False,
        )

    # Combine price series into joint DataFrame
    df_prices = pd.DataFrame(series_dict).dropna()
    total_val = sum(quantities.get(s, 0) * latest_prices.get(s, 0.0) for s in series_dict)

    if len(df_prices) < 5 or total_val <= 0:
        # Fallback profile evaluation when history is very short
        asset_profiles = []
        for sym, s in series_dict.items():
            asset_profiles.append(AssetRiskProfile(
                symbol=sym,
                weight_pct=100.0 / len(series_dict),
                annualized_volatility=0.20,
                beta=1.0,
                var_95_1d_pct=2.1,
                risk_label="Medium",
            ))

        return PortfolioRiskReport(
            portfolio_value=round(total_val, 2),
            annualized_volatility=20.0,
            var_95_1d_pct=2.1,
            var_95_1d_inr=round(total_val * 0.021, 2),
            cvar_95_1d_pct=2.8,
            cvar_95_1d_inr=round(total_val * 0.028, 2),
            sharpe_ratio=0.5,
            sortino_ratio=0.6,
            max_drawdown_pct=5.0,
            portfolio_beta=1.0,
            asset_profiles=asset_profiles,
            as_of_date=max(latest_dates) if latest_dates else "N/A",
            source_report=source_report,
            has_sufficient_history=False,
        )

    # Compute weights
    weights = np.array([
        (quantities[s] * latest_prices[s]) / total_val for s in df_prices.columns
    ])

    # Daily percentage returns
    df_rets = df_prices.pct_change().dropna()
    portfolio_daily_rets = df_rets.dot(weights)

    # 1. Volatility
    daily_vol = float(portfolio_daily_rets.std())
    annual_vol = daily_vol * np.sqrt(TRADING_DAYS_PER_YEAR)

    # 2. Value at Risk (1-day 95% Historical)
    var_95_pct = float(np.percentile(portfolio_daily_rets, 5))  # Negative return
    var_95_abs_pct = abs(var_95_pct) * 100.0
    var_95_inr = abs(var_95_pct) * total_val

    # 3. Conditional Value at Risk (CVaR 95% / Expected Shortfall)
    tail_losses = portfolio_daily_rets[portfolio_daily_rets <= var_95_pct]
    cvar_95_pct = abs(float(tail_losses.mean())) if len(tail_losses) > 0 else abs(var_95_pct) * 1.25
    cvar_95_abs_pct = cvar_95_pct * 100.0
    cvar_95_inr = cvar_95_pct * total_val

    # 4. Sharpe Ratio
    rf_daily = RISK_FREE_RATE_ANNUAL / TRADING_DAYS_PER_YEAR
    excess_rets = portfolio_daily_rets - rf_daily
    sharpe = float((excess_rets.mean() / daily_vol) * np.sqrt(TRADING_DAYS_PER_YEAR)) if daily_vol > 0 else 0.0

    # 5. Sortino Ratio (Downside deviation)
    downside_rets = portfolio_daily_rets[portfolio_daily_rets < 0]
    downside_std = float(downside_rets.std()) if len(downside_rets) > 1 else daily_vol
    sortino = float((excess_rets.mean() / downside_std) * np.sqrt(TRADING_DAYS_PER_YEAR)) if downside_std > 0 else 0.0

    # 6. Max Drawdown
    cumulative = (1.0 + portfolio_daily_rets).cumprod()
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    max_dd_pct = abs(float(drawdown.min())) * 100.0

    # 7. Portfolio Beta relative to NIFTY 50
    nifty_df = load_nifty50(processed_dir=processed_dir)
    portfolio_beta = 1.0
    if not nifty_df.empty and "Close" in nifty_df.columns:
        nifty_s = nifty_df.set_index("Date")["Close"]
        nifty_rets = nifty_s.pct_change().dropna()
        joint = pd.concat([portfolio_daily_rets.rename("port"), nifty_rets.rename("nifty")], axis=1).dropna()
        if len(joint) >= 10:
            cov = float(np.cov(joint["port"], joint["nifty"])[0, 1])
            var_m = float(np.var(joint["nifty"]))
            if var_m > 0:
                portfolio_beta = round(cov / var_m, 2)

    # 8. Individual Asset Profiles
    asset_profiles: List[AssetRiskProfile] = []
    for i, sym in enumerate(df_prices.columns):
        stock_rets = df_rets[sym]
        stock_vol = float(stock_rets.std() * np.sqrt(TRADING_DAYS_PER_YEAR))
        stock_var = abs(float(np.percentile(stock_rets, 5))) * 100.0

        # Beta for individual stock
        stock_beta = 1.0
        if not nifty_df.empty and "Close" in nifty_df.columns:
            joint_stock = pd.concat([stock_rets.rename("stock"), nifty_rets.rename("nifty")], axis=1).dropna()
            if len(joint_stock) >= 10:
                cov_s = float(np.cov(joint_stock["stock"], joint_stock["nifty"])[0, 1])
                var_m = float(np.var(joint_stock["nifty"]))
                if var_m > 0:
                    stock_beta = round(cov_s / var_m, 2)

        if stock_vol < 0.20 or stock_beta < 0.85:
            risk_label = "Low"
        elif stock_vol <= 0.30 or stock_beta <= 1.15:
            risk_label = "Medium"
        else:
            risk_label = "High"

        asset_profiles.append(AssetRiskProfile(
            symbol=sym,
            weight_pct=round(weights[i] * 100.0, 1),
            annualized_volatility=round(stock_vol * 100.0, 1),
            beta=stock_beta,
            var_95_1d_pct=round(stock_var, 2),
            risk_label=risk_label,
        ))

    return PortfolioRiskReport(
        portfolio_value=round(total_val, 2),
        annualized_volatility=round(annual_vol * 100.0, 2),
        var_95_1d_pct=round(var_95_abs_pct, 2),
        var_95_1d_inr=round(var_95_inr, 2),
        cvar_95_1d_pct=round(cvar_95_abs_pct, 2),
        cvar_95_1d_inr=round(cvar_95_inr, 2),
        sharpe_ratio=round(sharpe, 2),
        sortino_ratio=round(sortino, 2),
        max_drawdown_pct=round(max_dd_pct, 2),
        portfolio_beta=portfolio_beta,
        asset_profiles=asset_profiles,
        as_of_date=max(latest_dates) if latest_dates else "N/A",
        source_report=source_report,
        has_sufficient_history=True,
    )


def calculate_stock_beta(symbol: str, processed_dir: Path = DIR_PROCESSED) -> float:
    """
    Computes individual stock beta against saved NIFTY 50 index series.
    Returns 1.0 fallback if insufficient data.
    """
    try:
        stock_df, _ = load_prices(symbol, processed_dir=processed_dir)
        nifty_df = load_nifty50(processed_dir=processed_dir)

        if stock_df.empty or nifty_df.empty or "Close" not in stock_df.columns or "Close" not in nifty_df.columns:
            return 1.0

        stock_s = stock_df.set_index("Date")["Close"].pct_change().dropna()
        nifty_s = nifty_df.set_index("Date")["Close"].pct_change().dropna()

        joint = pd.concat([stock_s.rename("stock"), nifty_s.rename("nifty")], axis=1).dropna()
        if len(joint) < 10:
            return 1.0

        cov = float(np.cov(joint["stock"], joint["nifty"])[0, 1])
        var_m = float(np.var(joint["nifty"]))
        return round(float(cov / var_m), 2) if var_m > 0 else 1.0
    except Exception:
        return 1.0
