"""
AlphaWatch AI — Portfolio Accounting & Concentration Analytics
ASTRAQUANT X 2026

Calculates:
  - Current portfolio market value from latest saved closing prices
  - Absolute and percentage Profit & Loss (P&L)
  - Holding portfolio weights
  - Sector allocations
  - Concentration alerts (> 30% in a single stock, or > 50% in a single sector)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import joblib
import pandas as pd

from src.data_loader import load_nifty50, load_prices, load_vix
from src.features import FEATURE_COLUMNS, build_features
from src.signals import PROFILES, generate_signal

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIR_PROCESSED = PROJECT_ROOT / "data" / "processed"
DIR_MODELS_SAVED = PROJECT_ROOT / "models" / "saved"


@dataclass
class Holding:
    """
    Representation of an equity holding in a user portfolio.

    Validates:
      - symbol: non-empty uppercase string.
      - quantity: strictly positive whole integer (no floats, non-positive rejected).
      - buy_price: strictly positive numeric value (> 0).
    """
    symbol: str
    quantity: int
    buy_price: float

    def __post_init__(self):
        if not isinstance(self.symbol, str) or not self.symbol.strip():
            raise ValueError(f"Symbol must be a non-empty string, got {self.symbol!r}")
        self.symbol = self.symbol.strip().upper()

        if isinstance(self.quantity, bool) or not isinstance(self.quantity, int):
            raise ValueError(
                f"Quantity must be a whole positive integer, got {self.quantity!r} ({type(self.quantity).__name__})"
            )
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be a whole positive integer, got {self.quantity}")

        if isinstance(self.buy_price, bool) or not isinstance(self.buy_price, (int, float)):
            raise ValueError(
                f"Buy price must be a numeric positive value, got {self.buy_price!r} ({type(self.buy_price).__name__})"
            )
        if self.buy_price <= 0.0:
            raise ValueError(f"Buy price must be strictly positive (> 0), got {self.buy_price}")
        self.buy_price = float(self.buy_price)


def validate_portfolio(holdings: Sequence[Holding]) -> None:
    """
    Validates a list of Holding items, ensuring valid types and no duplicate symbols.
    Raises ValueError on duplicates or invalid holding items.
    """
    if not holdings:
        return
    seen_symbols = set()
    for h in holdings:
        if not isinstance(h, Holding):
            raise TypeError(f"Expected Holding instance, got {type(h).__name__}")
        if h.symbol in seen_symbols:
            raise ValueError(f"Duplicate symbol detected in portfolio: '{h.symbol}'")
        seen_symbols.add(h.symbol)


# Three sample demo portfolios for onboarding, diagnostics, and testing
DEMO_PORTFOLIOS: Dict[str, List[Holding]] = {
    "Conservative Core": [
        Holding(symbol="HDFCBANK", quantity=50, buy_price=1500.0),
        Holding(symbol="TCS", quantity=25, buy_price=3600.0),
        Holding(symbol="HINDUNILVR", quantity=30, buy_price=2400.0),
    ],
    "Moderate Balanced": [
        Holding(symbol="RELIANCE", quantity=40, buy_price=2500.0),
        Holding(symbol="INFY", quantity=60, buy_price=1600.0),
        Holding(symbol="ICICIBANK", quantity=70, buy_price=1050.0),
    ],
    "Aggressive Alpha": [
        Holding(symbol="SBIN", quantity=100, buy_price=750.0),
        Holding(symbol="BHARTIARTL", quantity=80, buy_price=1200.0),
        Holding(symbol="LT", quantity=30, buy_price=3500.0),
    ],
}


def get_portfolio_valuation(
    holdings: Sequence[Holding],
    processed_dir: Path = DIR_PROCESSED,
) -> Dict[str, Any]:
    """
    Computes current market value, portfolio weights, and profit/loss (P&L)
    strictly from the latest saved closing price via data_loader.load_prices.

    If a saved CSV is missing or empty, raises FileNotFoundError. Never fakes data.
    """
    validate_portfolio(holdings)
    if not holdings:
        return {
            "total_cost": 0.0,
            "total_value": 0.0,
            "unrealized_pnl": 0.0,
            "unrealized_pnl_pct": 0.0,
            "weights": {},
            "holding_values": {},
            "holding_pnl": {},
        }

    total_cost = 0.0
    total_val = 0.0
    holding_values: Dict[str, float] = {}
    holding_costs: Dict[str, float] = {}
    holding_pnl: Dict[str, Dict[str, float]] = {}

    for h in holdings:
        cost = h.quantity * h.buy_price
        total_cost += cost
        holding_costs[h.symbol] = cost

        price_df, _ = load_prices(h.symbol, processed_dir=processed_dir)
        if price_df.empty or "Close" not in price_df.columns:
            raise FileNotFoundError(
                f"Missing saved price data for '{h.symbol}' in {processed_dir}. Never fake a result."
            )

        latest_close = float(price_df["Close"].iloc[-1])
        val = h.quantity * latest_close
        total_val += val
        holding_values[h.symbol] = val

        pnl_abs = val - cost
        pnl_pct = (pnl_abs / cost * 100.0) if cost > 0 else 0.0
        holding_pnl[h.symbol] = {
            "latest_close": latest_close,
            "current_value": val,
            "cost_basis": cost,
            "pnl": pnl_abs,
            "pnl_pct": pnl_pct,
        }

    weights: Dict[str, float] = {}
    for sym, val in holding_values.items():
        weights[sym] = (val / total_val) if total_val > 0 else 0.0

    total_pnl = total_val - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100.0) if total_cost > 0 else 0.0

    return {
        "total_cost": round(total_cost, 2),
        "total_value": round(total_val, 2),
        "unrealized_pnl": round(total_pnl, 2),
        "unrealized_pnl_pct": round(total_pnl_pct, 2),
        "weights": weights,
        "holding_values": holding_values,
        "holding_pnl": holding_pnl,
    }


def portfolio_value(holdings: Sequence[Holding], processed_dir: Path = DIR_PROCESSED) -> float:
    """Returns current total market value of the portfolio."""
    return float(get_portfolio_valuation(holdings, processed_dir=processed_dir)["total_value"])


def portfolio_weights(holdings: Sequence[Holding], processed_dir: Path = DIR_PROCESSED) -> Dict[str, float]:
    """Returns dictionary mapping symbol to weight fraction (0.0 to 1.0)."""
    return dict(get_portfolio_valuation(holdings, processed_dir=processed_dir)["weights"])


def portfolio_pnl(holdings: Sequence[Holding], processed_dir: Path = DIR_PROCESSED) -> Dict[str, float]:
    """Returns dictionary with 'unrealized_pnl' (INR) and 'unrealized_pnl_pct' (%)."""
    val = get_portfolio_valuation(holdings, processed_dir=processed_dir)
    return {
        "unrealized_pnl": val["unrealized_pnl"],
        "unrealized_pnl_pct": val["unrealized_pnl_pct"],
    }


def concentration_alert(
    holdings: Sequence[Holding],
    processed_dir: Path = DIR_PROCESSED,
) -> List[Dict[str, Any]]:
    """
    Checks if any individual stock represents strictly more than 30% of total portfolio value.
    A stock at exactly 30.0% generates no alert; at 31.0% triggers an alert.
    """
    val_data = get_portfolio_valuation(holdings, processed_dir=processed_dir)
    total_val = val_data["total_value"]
    if total_val <= 0:
        return []

    alerts: List[Dict[str, Any]] = []
    for h in holdings:
        val = val_data["holding_values"].get(h.symbol, 0.0)
        weight_pct = (val / total_val) * 100.0
        # Alert strictly when weight exceeds 30.0%
        if weight_pct > 30.0:
            alerts.append({
                "symbol": h.symbol,
                "weight_pct": round(weight_pct, 2),
                "message": f"{h.symbol} accounts for {weight_pct:.1f}% of total portfolio value (exceeds 30% guideline).",
            })
    return alerts


def run_analysis(
    portfolio: Sequence[Holding],
    profile: str = "Moderate",
    processed_dir: Path = DIR_PROCESSED,
    models_dir: Path = DIR_MODELS_SAVED,
) -> List[Dict[str, Any]]:
    """
    Runs multi-factor quant inference on a portfolio of holdings.
    Returns per holding: symbol, probability_up, signal, risk_label, reason, model_version.

    The reason string is built strictly from computed technical values
    (5-day return, 20-day return, RSI 14, 20-day annualized volatility).

    If a saved model or CSV is missing, raises FileNotFoundError. Never fakes results.
    """
    validate_portfolio(portfolio)
    if profile not in PROFILES:
        raise ValueError(f"Unknown investor profile: '{profile}'. Supported: {list(PROFILES.keys())}")

    results: List[Dict[str, Any]] = []

    for h in portfolio:
        price_df, _ = load_prices(h.symbol, processed_dir=processed_dir)
        if price_df.empty or "Close" not in price_df.columns:
            raise FileNotFoundError(
                f"Missing saved price data for '{h.symbol}' in {processed_dir}. Never fake a result."
            )

        model_path = models_dir / f"{h.symbol}_rf.joblib"
        if not model_path.exists():
            raise FileNotFoundError(
                f"Missing saved model for '{h.symbol}' at {model_path}. Train model before analysis. Never fake a result."
            )

        nifty_df = load_nifty50(processed_dir=processed_dir)
        vix_df = load_vix(processed_dir=processed_dir)
        df_feat = build_features(price_df, df_nifty=nifty_df, df_vix=vix_df)
        if df_feat.empty:
            raise ValueError(f"Insufficient history to compute features for '{h.symbol}'")

        latest_row = df_feat.iloc[-1]

        # Extract computed values for reason string
        ret_5d = float(latest_row.get("return_5d", 0.0)) * 100.0
        ret_20d = float(latest_row.get("return_20d", 0.0)) * 100.0
        rsi = float(latest_row.get("rsi_14", 50.0))
        vol_20d = float(latest_row.get("volatility_20d", 0.20))

        # Risk classification from computed volatility
        if vol_20d < 0.20:
            risk_label = "Low"
        elif vol_20d <= 0.30:
            risk_label = "Medium"
        else:
            risk_label = "High"

        # Reason string built ONLY from computed values
        reason = (
            f"RSI(14) at {rsi:.1f}, 5-day return of {ret_5d:+.2f}%, "
            f"20-day return of {ret_20d:+.2f}%, and 20-day annualized volatility of {vol_20d*100.0:.1f}%."
        )

        # Load calibrated model
        bundle = joblib.load(model_path)
        cal_model = bundle["calibrated_model"]
        scaler = bundle["scaler"]
        feat_names = bundle.get("feature_names", FEATURE_COLUMNS)
        model_ver = str(bundle.get("version", "1.0"))

        X_infer = pd.DataFrame([latest_row[feat_names].values], columns=feat_names).fillna(0.0)
        X_infer_sc = scaler.transform(X_infer)

        prob_up = float(cal_model.predict_proba(X_infer_sc)[0, 1])

        # Generate signal via signals engine
        as_of_str = str(price_df["Date"].iloc[-1])
        sig_res = generate_signal(
            prob=prob_up,
            profile=profile,
            model_version=model_ver,
            as_of=as_of_str,
        )

        results.append({
            "symbol": h.symbol,
            "probability_up": round(prob_up, 4),
            "signal": sig_res["signal"],
            "risk_label": risk_label,
            "reason": reason,
            "model_version": model_ver,
        })

    return results


# Industry sector classifications for supported Indian equities
SECTOR_MAP: Dict[str, str] = {
    "RELIANCE": "Energy & Conglomerate",
    "TCS": "Information Technology",
    "INFY": "Information Technology",
    "HDFCBANK": "Financial Services",
    "ICICIBANK": "Financial Services",
    "KOTAKBANK": "Financial Services",
    "AXISBANK": "Financial Services",
    "SBIN": "Financial Services",
    "HINDUNILVR": "FMCG",
    "ITC": "FMCG",
    "BHARTIARTL": "Telecommunications",
    "LT": "Infrastructure & Capital Goods",
}


@dataclass
class HoldingDetail:
    """Holding item enriched with market valuation and risk classification."""
    symbol: str
    sector: str
    quantity: int
    buy_price: float
    current_price: float
    cost_basis: float
    current_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    weight_pct: float
    risk_label: str  # 'Low', 'Medium', 'High'
    as_of_date: str
    has_data: bool


@dataclass
class PortfolioSummary:
    """Aggregated user portfolio valuation and concentration health."""
    total_cost_basis: float
    total_current_value: float
    total_unrealized_pnl: float
    total_unrealized_pnl_pct: float
    holdings_count: int
    risk_counts: Dict[str, int]  # {'Low': x, 'Medium': y, 'High': z}
    holdings: List[HoldingDetail]
    sector_weights: Dict[str, float]
    concentration_alerts: List[Dict[str, str]]
    as_of_date: str
    source_report: str = "Saved Historical Bhavcopy Archive"

    @property
    def total_invested_value(self) -> float:
        return self.total_cost_basis


def compute_portfolio_summary(
    holdings_data: List[Dict[str, Any]],
    processed_dir: Path = DIR_PROCESSED,
) -> PortfolioSummary:
    """
    Computes real-time valuation, weight distribution, and concentration warnings
    for a user's holdings strictly from saved local price files.
    """
    if not holdings_data:
        return PortfolioSummary(
            total_cost_basis=0.0,
            total_current_value=0.0,
            total_unrealized_pnl=0.0,
            total_unrealized_pnl_pct=0.0,
            holdings_count=0,
            risk_counts={"Low": 0, "Medium": 0, "High": 0},
            holdings=[],
            sector_weights={},
            concentration_alerts=[],
            as_of_date="N/A",
        )

    enriched: List[HoldingDetail] = []
    latest_dates: List[str] = []

    # First pass: load prices and calculate values
    for item in holdings_data:
        sym = str(item.get("symbol", "")).strip().upper()
        qty = int(item.get("quantity", 0))
        buy_p = float(item.get("buy_price", 0.0))
        cost_basis = qty * buy_p

        sector = SECTOR_MAP.get(sym, "Diversified")
        price_df, _ = load_prices(sym, processed_dir=processed_dir)

        if not price_df.empty and "Close" in price_df.columns:
            latest_close = float(price_df["Close"].iloc[-1])
            as_of = str(price_df["Date"].iloc[-1])
            latest_dates.append(as_of)
            current_val = qty * latest_close
            pnl = current_val - cost_basis
            pnl_pct = (pnl / cost_basis * 100.0) if cost_basis > 0 else 0.0
            has_data = True

            # Assess risk level from 20-day historical volatility
            if len(price_df) >= 20:
                ret_1d = price_df["Close"].pct_change()
                vol_20d = float(ret_1d.tail(20).std() * (252 ** 0.5))
                if vol_20d < 0.20:
                    risk_label = "Low"
                elif vol_20d <= 0.30:
                    risk_label = "Medium"
                else:
                    risk_label = "High"
            else:
                risk_label = "Medium"
        else:
            latest_close = buy_p
            current_val = cost_basis
            pnl = 0.0
            pnl_pct = 0.0
            as_of = "N/A"
            has_data = False
            risk_label = "Medium"

        enriched.append(HoldingDetail(
            symbol=sym,
            sector=sector,
            quantity=qty,
            buy_price=round(buy_p, 2),
            current_price=round(latest_close, 2),
            cost_basis=round(cost_basis, 2),
            current_value=round(current_val, 2),
            unrealized_pnl=round(pnl, 2),
            unrealized_pnl_pct=round(pnl_pct, 2),
            weight_pct=0.0,  # Computed in second pass
            risk_label=risk_label,
            as_of_date=as_of,
            has_data=has_data,
        ))

    total_value = sum(h.current_value for h in enriched)
    total_cost = sum(h.cost_basis for h in enriched)
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100.0) if total_cost > 0 else 0.0

    # Second pass: compute weights and concentration
    sector_totals: Dict[str, float] = {}
    concentration_alerts: List[Dict[str, str]] = []
    risk_counts: Dict[str, int] = {"Low": 0, "Medium": 0, "High": 0}

    for h in enriched:
        weight = (h.current_value / total_value * 100.0) if total_value > 0 else 0.0
        h.weight_pct = round(weight, 1)

        sector_totals[h.sector] = sector_totals.get(h.sector, 0.0) + h.current_value
        risk_counts[h.risk_label] = risk_counts.get(h.risk_label, 0) + 1

        # Single stock concentration rule (> 30%)
        if weight > 30.0:
            concentration_alerts.append({
                "rule": "Stock Concentration > 30%",
                "message": f"{h.symbol} accounts for {weight:.1f}% of total portfolio value (exceeds 30% prudential guideline).",
            })

    # Single sector concentration rule (> 50%)
    sector_weights: Dict[str, float] = {}
    for sec, val in sector_totals.items():
        sec_wt = (val / total_value * 100.0) if total_value > 0 else 0.0
        sector_weights[sec] = round(sec_wt, 1)
        if sec_wt > 50.0:
            concentration_alerts.append({
                "rule": "Sector Overexposure > 50%",
                "message": f"Industry sector '{sec}' represents {sec_wt:.1f}% of your portfolio (exceeds 50% single-industry limit).",
            })

    overall_as_of = max(latest_dates) if latest_dates else "N/A"

    return PortfolioSummary(
        total_cost_basis=round(total_cost, 2),
        total_current_value=round(total_value, 2),
        total_unrealized_pnl=round(total_pnl, 2),
        total_unrealized_pnl_pct=round(total_pnl_pct, 2),
        holdings_count=len(enriched),
        risk_counts=risk_counts,
        holdings=enriched,
        sector_weights=sector_weights,
        concentration_alerts=concentration_alerts,
        as_of_date=overall_as_of,
    )


# Function alias
evaluate_portfolio = compute_portfolio_summary

