"""
AlphaWatch AI — 6-Pillar Fundamental Health Engine
ASTRAQUANT X 2026

Evaluates corporate fundamentals strictly using saved Screener.in exports:
  1. Valuation: P/E relative to stock's own historical median
  2. Profitability: Return on Equity (ROE)
  3. Efficiency: Return on Capital Employed (ROCE)
  4. Solvency: Debt to Equity ratio (with bank-specific solvency awareness)
  5. Growth: 3-Year Sales and Net Profit Growth
  6. Ownership: Promoter holding stability over 3 years

Badge Output:
  - Strong: >= 4 pillars positive, 0 red flags
  - Weak:   >= 3 pillars negative, or critical solvency/profitability red flag
  - Mixed:  Balanced or diverging metrics
  - Insufficient Data: < 3 pillars available

Includes:
  - Stale data detection (> 120 days old triggers a stale-data audit warning)
  - combine(signal, badge): Educational synthesis of ML momentum and financial health
  - Strict compliance: Everything is educational research, never investment advice.
"""

import csv
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FUNDAMENTALS_CSV = PROJECT_ROOT / "data" / "processed" / "fundamentals.csv"

# Financials with regulatory capital structures (deposits vs debt)
BANKING_SYMBOLS = {"HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK"}


@dataclass
class PillarRuleEvaluation:
    """Evaluation result for an individual fundamental pillar."""
    pillar_name: str
    input_value: Optional[float]
    status: str  # 'Pass', 'Neutral', 'Fail', 'Not Available'
    rule_description: str


@dataclass
class FundamentalScoreResult:
    """Full 6-pillar fundamental health diagnostic result."""
    symbol: str
    company_name: str
    badge: str  # 'Strong', 'Mixed', 'Weak', 'Insufficient Data'
    score_fraction: str  # e.g. "5/6"
    score_percent: float
    inputs: Dict[str, Optional[float]]
    rules_fired: List[str]
    pillar_evaluations: List[PillarRuleEvaluation]
    source_export_date: str
    days_since_export: int
    is_stale: bool  # True if > 120 days old
    stale_warning: Optional[str]
    educational_disclaimer: str = (
        "Educational research signal only. Not investment advice or an endorsement to buy or sell."
    )


def evaluate_fundamentals(
    fundamental_data: Dict[str, Any],
    reference_date: Optional[datetime] = None,
    stale_threshold_days: int = 120,
) -> FundamentalScoreResult:
    """
    Applies the documented 6-pillar fundamental health evaluation rules
    to an equity's fundamental inputs.
    """
    ref_dt = reference_date or datetime.now()
    symbol = str(fundamental_data.get("symbol", "UNKNOWN")).strip().upper()
    company_name = str(fundamental_data.get("company_name", symbol)).strip()
    is_bank = symbol in BANKING_SYMBOLS

    # Extract numeric inputs
    pe = fundamental_data.get("current_pe")
    pe_median = fundamental_data.get("historical_pe_median")
    roe = fundamental_data.get("roe_pct")
    roce = fundamental_data.get("roce_pct")
    debt_equity = fundamental_data.get("debt_to_equity")
    sales_growth_3y = fundamental_data.get("sales_growth_3y_pct")
    profit_growth_3y = fundamental_data.get("profit_growth_3y_pct")
    promoter_holding = fundamental_data.get("promoter_holding_pct")
    promoter_change_3y = fundamental_data.get("promoter_holding_change_3y_pct")

    inputs_dict: Dict[str, Optional[float]] = {
        "current_pe": pe,
        "historical_pe_median": pe_median,
        "roe_pct": roe,
        "roce_pct": roce,
        "debt_to_equity": debt_equity,
        "sales_growth_3y_pct": sales_growth_3y,
        "profit_growth_3y_pct": profit_growth_3y,
        "promoter_holding_pct": promoter_holding,
        "promoter_holding_change_3y_pct": promoter_change_3y,
    }

    evaluations: List[PillarRuleEvaluation] = []
    rules_fired: List[str] = []

    # -------------------------------------------------------------------------
    # Pillar 1: Valuation (P/E relative to own historical median)
    # -------------------------------------------------------------------------
    if pe is not None and pe > 0:
        if pe_median is not None and pe_median > 0:
            pe_ratio = pe / pe_median
            if pe_ratio <= 1.10:
                evaluations.append(PillarRuleEvaluation(
                    pillar_name="Valuation",
                    input_value=pe,
                    status="Pass",
                    rule_description=f"P/E ({pe:.1f}x) trades below or near historical median ({pe_median:.1f}x), indicating reasonable valuation.",
                ))
            elif pe_ratio <= 1.35:
                evaluations.append(PillarRuleEvaluation(
                    pillar_name="Valuation",
                    input_value=pe,
                    status="Neutral",
                    rule_description=f"P/E ({pe:.1f}x) is moderately above historical median ({pe_median:.1f}x, +{(pe_ratio-1)*100:.0f}%).",
                ))
            else:
                evaluations.append(PillarRuleEvaluation(
                    pillar_name="Valuation",
                    input_value=pe,
                    status="Fail",
                    rule_description=f"P/E ({pe:.1f}x) is stretched over 35% above historical median ({pe_median:.1f}x).",
                ))
        else:
            if pe <= 30.0:
                evaluations.append(PillarRuleEvaluation(
                    pillar_name="Valuation",
                    input_value=pe,
                    status="Pass",
                    rule_description=f"Current P/E is {pe:.1f}x (within typical benchmark range).",
                ))
            else:
                evaluations.append(PillarRuleEvaluation(
                    pillar_name="Valuation",
                    input_value=pe,
                    status="Neutral",
                    rule_description=f"Current P/E is {pe:.1f}x.",
                ))
    else:
        evaluations.append(PillarRuleEvaluation(
            pillar_name="Valuation",
            input_value=None,
            status="Not Available",
            rule_description="P/E valuation metric missing in export.",
        ))

    # -------------------------------------------------------------------------
    # Pillar 2: Profitability (ROE)
    # -------------------------------------------------------------------------
    if roe is not None:
        if roe >= 15.0:
            evaluations.append(PillarRuleEvaluation(
                pillar_name="Profitability (ROE)",
                input_value=roe,
                status="Pass",
                rule_description=f"ROE ({roe:.1f}%) exceeds the 15% strong threshold.",
            ))
        elif roe >= 10.0:
            evaluations.append(PillarRuleEvaluation(
                pillar_name="Profitability (ROE)",
                input_value=roe,
                status="Neutral",
                rule_description=f"ROE ({roe:.1f}%) is moderate (10% to 15%).",
            ))
        else:
            evaluations.append(PillarRuleEvaluation(
                pillar_name="Profitability (ROE)",
                input_value=roe,
                status="Fail",
                rule_description=f"ROE ({roe:.1f}%) is subpar (< 10%).",
            ))
    else:
        evaluations.append(PillarRuleEvaluation(
            pillar_name="Profitability (ROE)",
            input_value=None,
            status="Not Available",
            rule_description="Return on Equity missing.",
        ))

    # -------------------------------------------------------------------------
    # Pillar 3: Efficiency (ROCE)
    # -------------------------------------------------------------------------
    if roce is not None:
        if roce >= 15.0:
            evaluations.append(PillarRuleEvaluation(
                pillar_name="Efficiency (ROCE)",
                input_value=roce,
                status="Pass",
                rule_description=f"ROCE ({roce:.1f}%) satisfies capital efficiency threshold (>= 15%).",
            ))
        elif roce >= 10.0:
            evaluations.append(PillarRuleEvaluation(
                pillar_name="Efficiency (ROCE)",
                input_value=roce,
                status="Neutral",
                rule_description=f"ROCE ({roce:.1f}%) is acceptable (10% to 15%).",
            ))
        else:
            evaluations.append(PillarRuleEvaluation(
                pillar_name="Efficiency (ROCE)",
                input_value=roce,
                status="Fail",
                rule_description=f"ROCE ({roce:.1f}%) reflects weak capital efficiency (< 10%).",
            ))
    else:
        evaluations.append(PillarRuleEvaluation(
            pillar_name="Efficiency (ROCE)",
            input_value=None,
            status="Not Available",
            rule_description="Return on Capital Employed missing.",
        ))

    # -------------------------------------------------------------------------
    # Pillar 4: Solvency (Debt to Equity)
    # -------------------------------------------------------------------------
    if is_bank:
        evaluations.append(PillarRuleEvaluation(
            pillar_name="Solvency (Debt to Equity)",
            input_value=debt_equity,
            status="Pass",
            rule_description="Banking / Financial Institution: evaluated under RBI regulatory capital adequacy rather than industrial D/E.",
        ))
    elif debt_equity is not None:
        if debt_equity <= 0.50:
            evaluations.append(PillarRuleEvaluation(
                pillar_name="Solvency (Debt to Equity)",
                input_value=debt_equity,
                status="Pass",
                rule_description=f"Debt-to-Equity ratio ({debt_equity:.2f}) indicates robust balance sheet solvency (<= 0.50).",
            ))
        elif debt_equity <= 1.00:
            evaluations.append(PillarRuleEvaluation(
                pillar_name="Solvency (Debt to Equity)",
                input_value=debt_equity,
                status="Neutral",
                rule_description=f"Debt-to-Equity ratio ({debt_equity:.2f}) is manageable (0.50 to 1.00).",
            ))
        else:
            evaluations.append(PillarRuleEvaluation(
                pillar_name="Solvency (Debt to Equity)",
                input_value=debt_equity,
                status="Fail",
                rule_description=f"Debt-to-Equity ratio ({debt_equity:.2f}) indicates elevated leverage risk (> 1.00).",
            ))
    else:
        evaluations.append(PillarRuleEvaluation(
            pillar_name="Solvency (Debt to Equity)",
            input_value=None,
            status="Not Available",
            rule_description="Debt to Equity ratio missing.",
        ))

    # -------------------------------------------------------------------------
    # Pillar 5: Growth (3-Year Sales & Profit Compound Growth)
    # -------------------------------------------------------------------------
    has_sales_growth = sales_growth_3y is not None
    has_profit_growth = profit_growth_3y is not None

    if has_sales_growth or has_profit_growth:
        s_val = sales_growth_3y if has_sales_growth else 0.0
        p_val = profit_growth_3y if has_profit_growth else 0.0

        if s_val >= 10.0 and p_val >= 10.0:
            evaluations.append(PillarRuleEvaluation(
                pillar_name="Multi-Year Growth",
                input_value=p_val,
                status="Pass",
                rule_description=f"Robust 3-year compound growth: Sales (+{s_val:.1f}%), Profit (+{p_val:.1f}%).",
            ))
        elif s_val >= 5.0 and p_val >= 5.0:
            evaluations.append(PillarRuleEvaluation(
                pillar_name="Multi-Year Growth",
                input_value=p_val,
                status="Neutral",
                rule_description=f"Moderate 3-year growth: Sales (+{s_val:.1f}%), Profit (+{p_val:.1f}%).",
            ))
        elif s_val < 0 or p_val < 0:
            evaluations.append(PillarRuleEvaluation(
                pillar_name="Multi-Year Growth",
                input_value=p_val,
                status="Fail",
                rule_description=f"Negative growth contraction in Sales ({s_val:.1f}%) or Profit ({p_val:.1f}%).",
            ))
        else:
            evaluations.append(PillarRuleEvaluation(
                pillar_name="Multi-Year Growth",
                input_value=p_val,
                status="Neutral",
                rule_description=f"Low single-digit growth: Sales ({s_val:.1f}%), Profit ({p_val:.1f}%).",
            ))
    else:
        evaluations.append(PillarRuleEvaluation(
            pillar_name="Multi-Year Growth",
            input_value=None,
            status="Not Available",
            rule_description="3-Year Sales and Profit growth records missing.",
        ))

    # -------------------------------------------------------------------------
    # Pillar 6: Ownership Stability (Promoter Holding Trend)
    # -------------------------------------------------------------------------
    if promoter_holding is not None:
        p_change = promoter_change_3y if promoter_change_3y is not None else 0.0
        if p_change >= 0 and promoter_holding >= 40.0:
            evaluations.append(PillarRuleEvaluation(
                pillar_name="Ownership Stability",
                input_value=promoter_holding,
                status="Pass",
                rule_description=f"Stable promoter stake ({promoter_holding:.1f}%, 3Y change: {p_change:+.1f}%).",
            ))
        elif p_change < -3.0:
            evaluations.append(PillarRuleEvaluation(
                pillar_name="Ownership Stability",
                input_value=promoter_holding,
                status="Fail",
                rule_description=f"Significant promoter stake dilution ({p_change:.1f}% over 3 years, current: {promoter_holding:.1f}%).",
            ))
        else:
            evaluations.append(PillarRuleEvaluation(
                pillar_name="Ownership Stability",
                input_value=promoter_holding,
                status="Neutral",
                rule_description=f"Promoter holding stands at {promoter_holding:.1f}% (3Y change: {p_change:+.1f}%).",
            ))
    else:
        evaluations.append(PillarRuleEvaluation(
            pillar_name="Ownership Stability",
            input_value=None,
            status="Not Available",
            rule_description="Promoter shareholding data missing.",
        ))

    # Compile rules fired
    rules_fired = [e.rule_description for e in evaluations if e.status != "Not Available"]

    # Calculate Badge and Score
    valid_evals = [e for e in evaluations if e.status != "Not Available"]
    passes = sum(1 for e in valid_evals if e.status == "Pass")
    fails = sum(1 for e in valid_evals if e.status == "Fail")
    total_evaluated = len(valid_evals)

    if total_evaluated < 3:
        badge = "Insufficient Data"
        score_fraction = f"{passes}/{total_evaluated}" if total_evaluated > 0 else "0/0"
        score_pct = 0.0
    else:
        score_fraction = f"{passes}/{total_evaluated}"
        score_pct = round((passes / total_evaluated) * 100.0, 1)

        # Critical red flags: Heavy leverage (>2.0 D/E non-bank) or negative ROE
        critical_red_flag = (debt_equity is not None and not is_bank and debt_equity > 2.0) or (roe is not None and roe < 0.0)

        if passes >= 4 and fails == 0 and not critical_red_flag:
            badge = "Strong"
        elif fails >= 3 or critical_red_flag:
            badge = "Weak"
        else:
            badge = "Mixed"

    # Stale data check (> 120 days)
    export_date_str = str(fundamental_data.get("source_export_date", "1970-01-01"))
    days_since = 999
    is_stale = True
    stale_warning = None

    try:
        exp_dt = datetime.strptime(export_date_str, "%Y-%m-%d")
        days_since = (ref_dt - exp_dt).days
        if days_since > stale_threshold_days:
            is_stale = True
            stale_warning = (
                f"Export is {days_since} days old (exceeds {stale_threshold_days}-day fresh threshold). "
                f"Financial health badge may not capture recent quarterly results."
            )
        else:
            is_stale = False
    except Exception:
        is_stale = True
        stale_warning = "Could not verify workbook export date."

    return FundamentalScoreResult(
        symbol=symbol,
        company_name=company_name,
        badge=badge,
        score_fraction=score_fraction,
        score_percent=score_pct,
        inputs=inputs_dict,
        rules_fired=rules_fired,
        pillar_evaluations=evaluations,
        source_export_date=export_date_str,
        days_since_export=days_since,
        is_stale=is_stale,
        stale_warning=stale_warning,
    )


def load_and_evaluate_symbol(
    symbol: str,
    fundamentals_csv: Path = FUNDAMENTALS_CSV,
    reference_date: Optional[datetime] = None,
) -> FundamentalScoreResult:
    """Loads fundamental record for a symbol from fundamentals.csv and evaluates score."""
    sym = symbol.strip().upper()
    if not fundamentals_csv.exists():
        empty_data: Dict[str, Any] = {"symbol": sym, "source_export_date": "N/A"}
        return evaluate_fundamentals(empty_data, reference_date=reference_date)

    with open(fundamentals_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("symbol", "").strip().upper() == sym:
                # Convert numeric fields
                parsed_row: Dict[str, Any] = {}
                for k, v in row.items():
                    if v is None or v == "":
                        parsed_row[k] = None
                    else:
                        try:
                            parsed_row[k] = float(v)
                        except ValueError:
                            parsed_row[k] = v
                return evaluate_fundamentals(parsed_row, reference_date=reference_date)

    empty_data = {"symbol": sym, "source_export_date": "N/A"}
    return evaluate_fundamentals(empty_data, reference_date=reference_date)


def combine(signal: str, badge: str) -> str:
    """
    Synthesizes the algorithmic ML model signal with the fundamental health badge
    into an educational explanation.

    CRITICAL COMPLIANCE NOTICE:
    Returns research explanations only, never trade instructions or financial advice.
    """
    sig = signal.strip().upper()
    bdg = badge.strip().title()

    disclaimer = " [Educational research context only — not investment advice.]"

    if bdg == "Insufficient Data":
        return f"Model signal is {sig}. Fundamental data is currently unavailable to cross-verify this setup.{disclaimer}"

    if sig == "BUY":
        if bdg == "Strong":
            return (
                "Model says BUY, fundamentals Strong: Algorithmic momentum aligns with robust balance sheet health "
                f"and high capital efficiency. Both short-term trend and long-term quality indicators align.{disclaimer}"
            )
        elif bdg == "Mixed":
            return (
                "Model says BUY, fundamentals Mixed: Model identifies favorable short-term statistical momentum, "
                f"but corporate financial health is mixed; consider reviewing growth and valuation metrics before adding.{disclaimer}"
            )
        else:  # Weak
            return (
                "Model says BUY, fundamentals Weak: Short-term price momentum has triggered an algorithmic signal, "
                f"but underlying balance sheet or profitability health is Weak; review financial quality carefully before acting.{disclaimer}"
            )

    elif sig == "SELL":
        if bdg == "Strong":
            return (
                "Model says SELL, fundamentals Strong: Algorithmic indicators project short-term downward price pressure "
                f"despite healthy underlying balance sheet quality. This divergence often reflects temporary sector rotation or broader index headwinds.{disclaimer}"
            )
        elif bdg == "Mixed":
            return (
                "Model says SELL, fundamentals Mixed: Negative price momentum accompanied by balanced financial metrics. "
                f"Technical indicators project downward drift.{disclaimer}"
            )
        else:  # Weak
            return (
                "Model says SELL, fundamentals Weak: Both statistical momentum and corporate financial health align negatively. "
                f"High leverage or deteriorating profitability compounds negative price momentum.{disclaimer}"
            )

    else:  # HOLD
        if bdg == "Strong":
            return (
                f"Model says HOLD, fundamentals Strong: Momentum is in a neutral consolidation zone while corporate balance sheet "
                f"health remains high; suggests patience while waiting for directional clarity.{disclaimer}"
            )
        elif bdg == "Weak":
            return (
                f"Model says HOLD, fundamentals Weak: Sideways price action with weak financial fundamentals; "
                f"unfavorable risk-to-reward for initiating new positions.{disclaimer}"
            )
        else:
            return (
                f"Model says HOLD, fundamentals Mixed: Neutral statistical momentum and balanced corporate quality metrics; "
                f"no actionable directional divergence detected.{disclaimer}"
            )
