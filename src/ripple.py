"""
AlphaWatch AI — Ripple Effect (Hypothetical Macro & Sector Shock Simulation)
ASTRAQUANT X 2026

Simulates hypothetical multi-asset portfolio impact under macroeconomic & sector stress scenarios:
  - Crude Oil Price Surge (+20% Brent Spike)
  - RBI Monetary Policy Tightening (+50 bps Repo Rate Hike)
  - Global Technology Selloff (-8% Global Tech Correction)
  - Broad Market Drawdown (NIFTY 50 -10% Systemic Correction)
  - FII Institutional Inflow Surge (+5% Large-Cap Rally)
  
IMPORTANT DISCLAIMER:
  Hypothetical educational simulation based on historical sector sensitivities and asset betas.
  This is NOT an investment forecast or guarantee of future asset behavior.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import pandas as pd

from src.portfolio import SECTOR_MAP
from src.risk import calculate_stock_beta
from src.data_loader import load_prices


@dataclass
class HoldingShockImpact:
    symbol: str
    sector: str
    quantity: int
    current_price: float
    current_value: float
    simulated_shock_pct: float
    simulated_price: float
    simulated_value: float
    impact_amount: float
    sensitivity_mechanism: str


@dataclass
class ScenarioSimulationResult:
    scenario_id: str
    scenario_name: str
    scenario_description: str
    economic_mechanism: str
    baseline_portfolio_value: float
    simulated_portfolio_value: float
    portfolio_impact_amount: float
    portfolio_impact_pct: float
    most_vulnerable_symbol: str
    most_vulnerable_impact_pct: float
    most_resilient_symbol: str
    most_resilient_impact_pct: float
    holdings_impact: List[HoldingShockImpact] = field(default_factory=list)
    disclaimer: str = (
        "Hypothetical educational simulation for academic research only. "
        "Calculated using historical beta sensitivities and documented sector transmission channels. Not investment advice."
    )


# Sector sensitivity rules (% shock under scenario)
SCENARIO_CONFIGS = {
    "crude_oil_spike": {
        "name": "Crude Oil Surge (+20% Brent Spike)",
        "description": "Global supply constraint pushes crude oil higher, impacting downstream energy consumers and input costs.",
        "mechanism": "Higher raw material expenditure compresses margins for paint, specialty chemicals, aviation, and auto makers; upstream oil exploration companies benefit from wider realizations.",
        "sector_shocks": {
            "Energy": 3.5,
            "Automobile": -2.8,
            "Consumer Discretionary": -3.2,
            "FMCG": -1.5,
            "Financials": -1.2,
            "Technology": 0.0,
            "Metals": 0.5,
            "Healthcare": -0.5,
            "Telecom": -0.8,
            "Default": -1.5,
        },
    },
    "rbi_rate_hike": {
        "name": "RBI Monetary Tightening (+50 bps Repo Rate)",
        "description": "Reserve Bank of India raises policy repo rate to curb domestic inflation, lifting cost of capital across the economy.",
        "mechanism": "Rate-sensitive industries (Auto, Real Estate, High-debt industrials) face demand contraction and elevated interest costs. Defensive sectors (Pharma, FMCG) exhibit relative insulation.",
        "sector_shocks": {
            "Automobile": -3.2,
            "Financials": -1.8,
            "Capital Goods": -2.5,
            "Consumer Discretionary": -2.8,
            "Technology": -0.5,
            "FMCG": 0.3,
            "Healthcare": 0.8,
            "Energy": -1.0,
            "Metals": -2.0,
            "Default": -1.8,
        },
    },
    "global_tech_selloff": {
        "name": "Global Tech Selloff (-8% Overseas Tech)",
        "description": "Tech index rout triggered by revised global enterprise IT spending and cross-border currency realignments.",
        "mechanism": "Export-oriented Indian IT service providers experience multiple compression and discretionary billing slowdown. Domestic consumption stocks remain largely decoupled.",
        "sector_shocks": {
            "Technology": -6.5,
            "Telecom": -2.0,
            "Financials": -1.0,
            "FMCG": 0.5,
            "Healthcare": 0.4,
            "Automobile": -0.8,
            "Energy": -0.5,
            "Metals": -1.2,
            "Default": -1.0,
        },
    },
    "nifty_systemic_correction": {
        "name": "Systemic Correction (NIFTY 50 -10%)",
        "description": "Broad-based index pullback across all NSE equities driven by macro de-risking.",
        "mechanism": "Equities react proportionally to their systematic covariance (historical Beta). High-beta cyclicals fall harder, while low-beta defensives hold ground.",
        "use_beta": True,
        "market_shock_pct": -10.0,
    },
    "fii_liquidity_rally": {
        "name": "FII Institutional Inflow (+5% NIFTY 50)",
        "description": "Strong foreign institutional liquidity deployment into Indian benchmark equities.",
        "mechanism": "Large-cap index heavyweights and high-beta growth stocks capture foreign institutional order flow proportionally to beta.",
        "use_beta": True,
        "market_shock_pct": 5.0,
    },
}


def simulate_ripple_scenario(
    scenario_id: str,
    holdings: List[Any],  # List of Holding db entities or dicts
) -> ScenarioSimulationResult:
    """
    Simulates hypothetical shock effect on a user's holdings portfolio.
    """
    cfg = SCENARIO_CONFIGS.get(scenario_id, SCENARIO_CONFIGS["crude_oil_spike"])
    is_beta_driven = cfg.get("use_beta", False)
    market_shock = cfg.get("market_shock_pct", 0.0)

    if not holdings:
        return ScenarioSimulationResult(
            scenario_id=scenario_id,
            scenario_name=cfg["name"],
            scenario_description=cfg["description"],
            economic_mechanism=cfg["mechanism"],
            baseline_portfolio_value=0.0,
            simulated_portfolio_value=0.0,
            portfolio_impact_amount=0.0,
            portfolio_impact_pct=0.0,
            most_vulnerable_symbol="N/A",
            most_vulnerable_impact_pct=0.0,
            most_resilient_symbol="N/A",
            most_resilient_impact_pct=0.0,
            holdings_impact=[],
        )

    baseline_total = 0.0
    simulated_total = 0.0
    impact_items: List[HoldingShockImpact] = []

    for h in holdings:
        if isinstance(h, dict):
            sym = str(h.get("symbol", "STOCK")).upper()
            qty = int(h.get("quantity", 0))
            buy_px = float(h.get("buy_price", 0.0))
        else:
            sym = str(getattr(h, "symbol", "STOCK")).upper()
            qty = int(getattr(h, "quantity", 0))
            buy_px = float(getattr(h, "buy_price", 0.0))

        # Fetch latest saved close
        cur_px = buy_px
        try:
            res = load_prices(sym)
            df = res[0] if isinstance(res, tuple) else res
            if not df.empty and "Close" in df.columns:
                cur_px = float(df["Close"].iloc[-1])
        except Exception:
            pass

        cur_val = qty * cur_px
        sector = SECTOR_MAP.get(sym, "Diversified")

        if is_beta_driven:
            # Beta-weighted shock
            beta = calculate_stock_beta(sym)
            shock_pct = beta * market_shock
            mech = f"Systematic shock: Beta ({beta:.2f}) × {market_shock:+.1f}% NIFTY move"
        else:
            # Sector-based sensitivity
            sector_shocks = cfg.get("sector_shocks", {})
            shock_pct = sector_shocks.get(sector, sector_shocks.get("Default", -1.0))
            mech = f"Sector sensitivity: {sector} historical transmission under {cfg['name']}"

        sim_px = max(0.01, cur_px * (1.0 + shock_pct / 100.0))
        sim_val = qty * sim_px
        impact_amt = sim_val - cur_val

        baseline_total += cur_val
        simulated_total += sim_val

        impact_items.append(
            HoldingShockImpact(
                symbol=sym,
                sector=sector,
                quantity=qty,
                current_price=round(cur_px, 2),
                current_value=round(cur_val, 2),
                simulated_shock_pct=round(shock_pct, 2),
                simulated_price=round(sim_px, 2),
                simulated_value=round(sim_val, 2),
                impact_amount=round(impact_amt, 2),
                sensitivity_mechanism=mech,
            )
        )

    portfolio_diff = simulated_total - baseline_total
    portfolio_diff_pct = (portfolio_diff / baseline_total * 100.0) if baseline_total > 0 else 0.0

    # Sort by shock percentage to identify most vulnerable and most resilient
    impact_items.sort(key=lambda x: x.simulated_shock_pct)
    most_vulnerable = impact_items[0] if impact_items else None
    most_resilient = impact_items[-1] if impact_items else None

    return ScenarioSimulationResult(
        scenario_id=scenario_id,
        scenario_name=cfg["name"],
        scenario_description=cfg["description"],
        economic_mechanism=cfg["mechanism"],
        baseline_portfolio_value=round(baseline_total, 2),
        simulated_portfolio_value=round(simulated_total, 2),
        portfolio_impact_amount=round(portfolio_diff, 2),
        portfolio_impact_pct=round(portfolio_diff_pct, 2),
        most_vulnerable_symbol=most_vulnerable.symbol if most_vulnerable else "N/A",
        most_vulnerable_impact_pct=most_vulnerable.simulated_shock_pct if most_vulnerable else 0.0,
        most_resilient_symbol=most_resilient.symbol if most_resilient else "N/A",
        most_resilient_impact_pct=most_resilient.simulated_shock_pct if most_resilient else 0.0,
        holdings_impact=impact_items,
    )
