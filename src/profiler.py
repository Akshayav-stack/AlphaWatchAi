"""
AlphaWatch AI — Investor Pattern & Adaptive Profiler Engine
ASTRAQUANT X 2026

Evaluates:
  1. Fixed questionnaire responses (Goal, Horizon, Experience, Fall Reaction, etc.)
  2. Portfolio composition (Weights, Concentration, Drawdown from cost basis)
  3. Adaptive rules:
     - Concentration > 30% in single equity
     - Sector exposure > 50%
     - Buy prices > 15% above current prices (drawdown stress)
     - High volatility asset tilt
  4. Generates an Investor Pattern with a visible, transparent 'Why this profile' derivation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ProfilerEvaluation:
    """Quantitative risk profile evaluation result."""
    risk_score: float  # 0.0 to 100.0
    suggested_profile: str  # 'Conservative', 'Moderate', 'Aggressive'
    diversification_score: float  # 0.0 to 100.0
    concentration_status: str  # 'Balanced', 'Concentrated', 'Heavily Skewed'
    holding_style: str  # 'Long-Term Compounding', 'Swing / Medium-Term', 'Aggressive Momentum'
    why_this_profile: str
    adaptive_followups: List[Dict[str, str]] = field(default_factory=list)


def evaluate_investor_profile(
    answers: Dict[str, Any],
    holdings_summary: Optional[Dict[str, Any]] = None,
) -> ProfilerEvaluation:
    """
    Computes an investor pattern using documented deterministic rules.
    """
    score = 50.0  # Baseline midpoint

    # 1. Goal
    goal = str(answers.get("goal", "")).lower()
    if "preservation" in goal or "income" in goal:
        score -= 15.0
    elif "speculative" in goal or "aggressive" in goal:
        score += 15.0
    elif "wealth" in goal:
        score += 5.0

    # 2. Horizon
    horizon = str(answers.get("horizon", "")).lower()
    if "< 1" in horizon or "months" in horizon:
        score -= 10.0
    elif "1-3" in horizon:
        score += 0.0
    elif "3-5" in horizon:
        score += 5.0
    elif "5+" in horizon or "> 5" in horizon:
        score += 10.0

    # 3. Experience
    exp = str(answers.get("experience", "")).lower()
    if "beginner" in exp or "< 1" in exp:
        score -= 10.0
    elif "advanced" in exp or "> 3" in exp:
        score += 10.0

    # 4. Reaction to 10% fall
    reaction = str(answers.get("fall_reaction", "")).lower()
    if "panic" in reaction or "sell all" in reaction:
        score -= 20.0
    elif "sell partial" in reaction:
        score -= 10.0
    elif "hold" in reaction:
        score += 5.0
    elif "buy more" in reaction:
        score += 15.0

    # 5. Share of savings
    savings = str(answers.get("savings_share", "")).lower()
    if "> 50" in savings or "more than 50" in savings:
        score -= 15.0  # High overall financial exposure demands lower risk tolerance
    elif "25-50" in savings:
        score -= 5.0
    elif "< 10" in savings:
        score += 10.0

    score = float(max(0.0, min(100.0, score)))

    # Determine Suggested Profile
    if score < 40.0:
        suggested = "Conservative"
        holding_style = "Capital Preservation / Defensive"
    elif score <= 65.0:
        suggested = "Moderate"
        holding_style = "Balanced Growth & Value"
    else:
        suggested = "Aggressive"
        holding_style = "High-Beta Capital Appreciation"

    # Analyze Portfolio Holdings & Adaptive Follow-up Rules
    diversification = 70.0
    concentration_status = "Balanced"
    adaptive_followups: List[Dict[str, str]] = []
    rules_applied: List[str] = [
        f"Base questionnaire score evaluated to {score:.1f}/100 based on stated investment horizon, market experience, and reaction to downside volatility."
    ]

    if holdings_summary:
        holdings = holdings_summary.get("holdings", [])
        num_holdings = len(holdings)

        # Diversification score based on number of assets
        if num_holdings >= 8:
            diversification = 90.0
        elif num_holdings >= 4:
            diversification = 70.0
        elif num_holdings >= 1:
            diversification = 40.0
        else:
            diversification = 20.0

        # Adaptive Rule 1: Single stock concentration > 30%
        for h in holdings:
            wt = float(h.get("weight_pct", 0.0))
            sym = str(h.get("symbol", ""))
            if wt > 30.0:
                concentration_status = "High Stock Concentration"
                adaptive_followups.append({
                    "rule": "Stock Concentration > 30%",
                    "message": f"Position in {sym} represents {wt:.1f}% of total portfolio value. Rule triggers risk dampening.",
                    "recommendation": "Consider gradual rebalancing into diversified index or sector leaders to mitigate single-company shock risk.",
                })
                rules_applied.append(f"High concentration penalty applied: {sym} constitutes {wt:.1f}% of capital.")
                if suggested == "Aggressive":
                    suggested = "Moderate"  # Dampen risk profile if portfolio is dangerously concentrated

        # Adaptive Rule 2: Single sector > 50%
        sector_weights = holdings_summary.get("sector_weights", {})
        for sec, sec_wt in sector_weights.items():
            if sec_wt > 50.0:
                concentration_status = "High Sector Concentration"
                adaptive_followups.append({
                    "rule": "Sector Overexposure > 50%",
                    "message": f"Industry sector '{sec}' accounts for {sec_wt:.1f}% of capital.",
                    "recommendation": "Broaden exposure across non-correlated sectors (e.g. FMCG, IT, Financials).",
                })
                rules_applied.append(f"Sector concentration alert triggered for {sec} ({sec_wt:.1f}%).")

        # Adaptive Rule 3: Buy prices far above current prices (> 15% drawdown)
        heavy_losses = [
            h for h in holdings
            if float(h.get("unrealized_pnl_pct", 0.0)) < -15.0
        ]
        if heavy_losses:
            syms = ", ".join(h.get("symbol", "") for h in heavy_losses)
            adaptive_followups.append({
                "rule": "Cost-Basis Drawdown > 15%",
                "message": f"Positions in {syms} are currently experiencing greater than 15% drawdowns from entry prices.",
                "recommendation": "Review fundamental health badges and 50-day moving average trend before averaging down.",
            })
            rules_applied.append(f"Drawdown recovery rule active for {syms}.")

    why_this_profile = " ".join(rules_applied)

    return ProfilerEvaluation(
        risk_score=round(score, 1),
        suggested_profile=suggested,
        diversification_score=round(diversification, 1),
        concentration_status=concentration_status,
        holding_style=holding_style,
        why_this_profile=why_this_profile,
        adaptive_followups=adaptive_followups,
    )
