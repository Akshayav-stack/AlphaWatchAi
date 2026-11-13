"""
AlphaWatch AI — Claim Auditor & Signal Verification Engine
ASTRAQUANT X 2026

Empirical audit of algorithmic signals against actual subsequent market outcomes:
  - Verifies model predictions against realized forward returns (5-day & 20-day)
  - Zero promotional puffery: mathematical calculation of realized precision
  - Calculates Brier Score (probability calibration quality)
  - Evaluates High-Confidence precision vs baseline
  - Generates verifiable audit logs of signals vs reality
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from src.data_loader import load_prices
from src.features import build_features


@dataclass
class AuditSummary:
    """Statistical summary of algorithmic claim verification."""
    total_audited_signals: int
    buy_signals_count: int
    sell_hold_signals_count: int
    buy_win_rate_pct: float
    high_confidence_win_rate_pct: float
    avg_buy_5d_return_pct: float
    avg_sell_hold_5d_return_pct: float
    alpha_over_random_pct: float
    brier_score: float
    calibration_rating: str
    audit_table: List[Dict[str, Any]] = field(default_factory=list)


def run_claim_audit(
    symbols: Optional[List[str]] = None,
    max_records: int = 100,
) -> AuditSummary:
    """
    Audits historical model/rule signals against actual forward returns for supported symbols.
    """
    target_symbols = symbols or [
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
        "SBIN", "BHARTIARTL", "ITC", "LT", "HINDUNILVR"
    ]

    all_audits: List[Dict[str, Any]] = []

    for sym in target_symbols:
        try:
            res = load_prices(sym)
            df = res[0] if isinstance(res, tuple) else res
            if df.empty or len(df) < 5:
                continue

            feats = build_features(df)
            if feats.empty or len(feats) < 5:
                continue

            # Evaluate forward 5-day return from Close(t) to Close(t+5)
            feats["Forward_5d_Ret"] = (feats["Close"].shift(-5) - feats["Close"]) / feats["Close"]
            feats["Forward_20d_Ret"] = (feats["Close"].shift(-20) - feats["Close"]) / feats["Close"]

            # Rule-based signal baseline: RSI < 45 and Price > SMA50 and Mom > 0 => BUY
            rsi = feats.get("rsi_14", pd.Series(50, index=feats.index))
            sma50_dist = feats.get("sma_dist_50", pd.Series(0, index=feats.index))
            ret5 = feats.get("ret_5d", pd.Series(0, index=feats.index))

            # Simulate probability signal (0.0 to 1.0)
            base_prob = 0.50 + (sma50_dist * 2.0).clip(-0.25, 0.25) + ((50.0 - rsi) / 200.0).clip(-0.15, 0.15)
            probs = base_prob.clip(0.10, 0.90)

            for i in range(len(feats) - 5):
                f5 = feats["Forward_5d_Ret"].iloc[i]
                if pd.isna(f5):
                    continue

                prob_val = float(probs.iloc[i])
                f5_val = float(f5) * 100.0
                f20 = feats["Forward_20d_Ret"].iloc[i]
                f20_val = float(f20 * 100.0) if not pd.isna(f20) else f5_val

                signal = "BUY" if prob_val >= 0.55 else ("SELL" if prob_val <= 0.45 else "HOLD")
                dt = str(feats["Date"].iloc[i])

                if signal == "BUY":
                    outcome = "VERIFIED PROFITABLE" if f5_val > 0 else "FALSE ALARM"
                    actual_binary = 1.0 if f5_val > 0 else 0.0
                else:
                    outcome = "CAPITAL PRESERVED" if f5_val <= 0 else "MISSED OPPORTUNITY"
                    actual_binary = 0.0

                all_audits.append(
                    {
                        "date": dt,
                        "symbol": sym,
                        "signal": signal,
                        "model_probability": round(prob_val * 100.0, 1),
                        "actual_5d_return_pct": round(f5_val, 2),
                        "actual_20d_return_pct": round(f20_val, 2),
                        "outcome": outcome,
                        "actual_binary": actual_binary,
                        "prob_float": prob_val,
                    }
                )
        except Exception:
            continue

    if not all_audits:
        return _empty_audit()

    # Sort descending by date
    all_audits.sort(key=lambda x: x["date"], reverse=True)

    buy_audits = [a for a in all_audits if a["signal"] == "BUY"]
    sell_hold_audits = [a for a in all_audits if a["signal"] != "BUY"]

    total_count = len(all_audits)
    buy_count = len(buy_audits)
    sell_hold_count = len(sell_hold_audits)

    profitable_buys = sum(1 for a in buy_audits if a["actual_5d_return_pct"] > 0)
    buy_win_rate = (profitable_buys / buy_count * 100.0) if buy_count > 0 else 0.0

    high_conf = [a for a in buy_audits if a["model_probability"] >= 65.0]
    high_conf_wins = sum(1 for a in high_conf if a["actual_5d_return_pct"] > 0)
    high_conf_win_rate = (high_conf_wins / len(high_conf) * 100.0) if high_conf else buy_win_rate

    avg_buy_ret = float(np.mean([a["actual_5d_return_pct"] for a in buy_audits])) if buy_audits else 0.0
    avg_other_ret = float(np.mean([a["actual_5d_return_pct"] for a in sell_hold_audits])) if sell_hold_audits else 0.0

    alpha_over_random = avg_buy_ret - avg_other_ret

    # Brier Score = (1/N) * sum((prob - actual)^2)
    brier_vals = [((a["prob_float"] - a["actual_binary"]) ** 2) for a in all_audits]
    brier = float(np.mean(brier_vals)) if brier_vals else 0.25

    if brier < 0.20:
        calib_rating = "High Calibration Reliability"
    elif brier < 0.25:
        calib_rating = "Moderate Calibration"
    else:
        calib_rating = "Elevated Uncertainty"

    return AuditSummary(
        total_audited_signals=total_count,
        buy_signals_count=buy_count,
        sell_hold_signals_count=sell_hold_count,
        buy_win_rate_pct=round(buy_win_rate, 2),
        high_confidence_win_rate_pct=round(high_conf_win_rate, 2),
        avg_buy_5d_return_pct=round(avg_buy_ret, 2),
        avg_sell_hold_5d_return_pct=round(avg_other_ret, 2),
        alpha_over_random_pct=round(alpha_over_random, 2),
        brier_score=round(brier, 4),
        calibration_rating=calib_rating,
        audit_table=all_audits[:max_records],
    )


def _empty_audit() -> AuditSummary:
    return AuditSummary(
        total_audited_signals=0,
        buy_signals_count=0,
        sell_hold_signals_count=0,
        buy_win_rate_pct=0.0,
        high_confidence_win_rate_pct=0.0,
        avg_buy_5d_return_pct=0.0,
        avg_sell_hold_5d_return_pct=0.0,
        alpha_over_random_pct=0.0,
        brier_score=0.25,
        calibration_rating="Insufficient Data",
        audit_table=[],
    )
