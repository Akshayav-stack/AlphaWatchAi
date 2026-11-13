"""
AlphaWatch AI — Quantitative Signal Engine & Candidate Ranker
ASTRAQUANT X 2026

Generates:
  - Holding Predictions (BUY / HOLD / SELL with probability bar, risk label, reason)
  - Fundamentals Check Badge with full expandable audit trail
  - Buy Candidates ranked specifically for the user's Investor Profile
  - Combined 2x2 Educational Explanations
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd

from src.data_loader import load_nifty50, load_prices, load_vix
from src.features import FEATURE_COLUMNS, build_features, prepare_ml_dataset
from src.fundamentals import FundamentalScoreResult, combine, load_and_evaluate_symbol
from src.models import generate_signal_and_reason

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIR_PROCESSED = PROJECT_ROOT / "data" / "processed"
DIR_MODELS_SAVED = PROJECT_ROOT / "models" / "saved"

# Profile thresholds configuration.
# NOTE: These thresholds may only be tuned on training and validation data,
# never on test data, to avoid data snooping bias and lookahead leakage.
PROFILES: Dict[str, Dict[str, float]] = {
    "Conservative": {
        "buy_threshold": 0.65,
        "sell_threshold": 0.35,
        "max_position_pct": 10.0,
        "stop_loss_pct": 3.0,
    },
    "Moderate": {
        "buy_threshold": 0.60,
        "sell_threshold": 0.40,
        "max_position_pct": 20.0,
        "stop_loss_pct": 5.0,
    },
    "Aggressive": {
        "buy_threshold": 0.55,
        "sell_threshold": 0.45,
        "max_position_pct": 30.0,
        "stop_loss_pct": 8.0,
    },
}


def generate_signal(
    prob: float,
    profile: str = "Moderate",
    model_version: str = "1.0",
    as_of: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates a BUY, SELL, or HOLD signal from predicted upward probability.

    Thresholds are strictly configured via the PROFILES dict and never hardcoded.
    Note: Thresholds may only be tuned on training and validation data.

    Args:
        prob: Probability of positive return, must be in [0.0, 1.0].
        profile: Profile key in PROFILES ('Conservative', 'Moderate', 'Aggressive').
        model_version: Model identifier string.
        as_of: Optional timestamp or date string.

    Returns:
        Dict with keys: signal, probability_up, profile, timestamp, model_version.

    Raises:
        ValueError: If prob is not in [0.0, 1.0] or profile is unknown.
    """
    if not isinstance(prob, (int, float)) or isinstance(prob, bool):
        raise ValueError(f"Probability must be a numeric float between 0.0 and 1.0, got {prob}")
    if prob < 0.0 or prob > 1.0:
        raise ValueError(f"Probability must be between 0.0 and 1.0, got {prob}")

    if profile not in PROFILES:
        raise ValueError(
            f"Unknown investor profile: '{profile}'. Supported profiles: {list(PROFILES.keys())}"
        )

    cfg = PROFILES[profile]
    buy_thresh = cfg["buy_threshold"]
    sell_thresh = cfg["sell_threshold"]

    if prob >= buy_thresh:
        signal = "BUY"
    elif prob <= sell_thresh:
        signal = "SELL"
    else:
        signal = "HOLD"

    ts = str(as_of) if as_of is not None else datetime.now().isoformat()

    return {
        "signal": signal,
        "probability_up": float(prob),
        "profile": profile,
        "timestamp": ts,
        "model_version": str(model_version),
    }


DEFAULT_SUPPORTED = [
    "RELIANCE",
    "TCS",
    "HDFCBANK",
    "INFY",
    "ICICIBANK",
    "HINDUNILVR",
    "ITC",
    "SBIN",
    "BHARTIARTL",
    "KOTAKBANK",
    "LT",
    "AXISBANK",
]


@dataclass
class StockPredictionCard:
    """Consolidated quantitative prediction and fundamental audit card."""
    symbol: str
    company_name: str
    current_price: float
    change_1d_pct: float
    signal: str  # 'BUY', 'HOLD', 'SELL'
    probability_up: float  # e.g. 0.68
    probability_up_pct: float  # e.g. 68.0
    probability_down_pct: float  # e.g. 32.0
    confidence_pct: float
    risk_label: str  # 'Low', 'Medium', 'High'
    model_reason: str
    fundamentals: FundamentalScoreResult
    combined_explanation: str
    has_model: bool
    as_of_date: str
    source_model: str


def get_or_train_prediction(
    symbol: str,
    investor_profile: str = "Moderate",
    processed_dir: Path = DIR_PROCESSED,
    models_dir: Path = DIR_MODELS_SAVED,
) -> StockPredictionCard:
    """
    Computes or loads the model prediction, features, and fundamentals for an equity.
    """
    sym = symbol.strip().upper()
    price_df, _ = load_prices(sym, processed_dir=processed_dir)
    nifty_df = load_nifty50(processed_dir=processed_dir)
    vix_df = load_vix(processed_dir=processed_dir)

    # Fundamental diagnostic
    fundamentals_result = load_and_evaluate_symbol(sym)

    if price_df.empty or len(price_df) < 2:
        return StockPredictionCard(
            symbol=sym,
            company_name=fundamentals_result.company_name or sym,
            current_price=0.0,
            change_1d_pct=0.0,
            signal="HOLD",
            probability_up=0.50,
            probability_up_pct=50.0,
            probability_down_pct=50.0,
            confidence_pct=50.0,
            risk_label="Medium",
            model_reason="Insufficient saved price data to generate feature momentum.",
            fundamentals=fundamentals_result,
            combined_explanation="Price history unavailable. Fundamental data displayed as saved.",
            has_model=False,
            as_of_date="N/A",
            source_model="None",
        )

    as_of = str(price_df["Date"].iloc[-1])
    current_price = float(price_df["Close"].iloc[-1])
    prev_close = float(price_df["Close"].iloc[-2]) if len(price_df) >= 2 else current_price
    change_1d_pct = ((current_price - prev_close) / prev_close) * 100.0

    # Build features
    df_feat = build_features(price_df, df_nifty=nifty_df, df_vix=vix_df)
    latest_row = df_feat.iloc[-1] if not df_feat.empty else pd.Series(dtype=float)

    # Determine risk label from 20-day volatility
    vol_20d = float(latest_row.get("volatility_20d", 0.22))
    if vol_20d < 0.20:
        risk_label = "Low"
    elif vol_20d <= 0.30:
        risk_label = "Medium"
    else:
        risk_label = "High"

    # Load or generate model prediction
    model_path = models_dir / f"{sym}_rf.joblib"
    probability_up = 0.50
    has_model = False
    top_features: List[Dict[str, Any]] = [
        {"feature": "rsi_14", "importance": 0.30},
        {"feature": "sma_dist_50", "importance": 0.25},
        {"feature": "volatility_20d", "importance": 0.20},
    ]

    if model_path.exists():
        try:
            bundle = joblib.load(model_path)
            cal_model = bundle.get("calibrated_model")
            scaler = bundle.get("scaler")
            feat_names = bundle.get("feature_names", FEATURE_COLUMNS)

            # Extract latest feature vector
            X_infer = pd.DataFrame([latest_row[feat_names].values], columns=feat_names).fillna(0.0)
            X_infer_sc = scaler.transform(X_infer)

            prob = float(cal_model.predict_proba(X_infer_sc)[0, 1])
            probability_up = prob
            has_model = True
        except Exception:
            has_model = False

    if not has_model:
        # Transparent rule-based fallback based on momentum & trend
        rsi = float(latest_row.get("rsi_14", 50.0))
        sma_dist = float(latest_row.get("sma_dist_20", 0.0))
        base_p = 0.50
        if rsi < 35:
            base_p += 0.08
        elif rsi > 65:
            base_p -= 0.08
        if sma_dist > 0.02:
            base_p += 0.05
        elif sma_dist < -0.02:
            base_p -= 0.05
        probability_up = float(np.clip(base_p, 0.20, 0.80))

    signal, reason, confidence = generate_signal_and_reason(
        probability_up=probability_up,
        feature_row=latest_row,
        top_features=top_features,
        investor_profile=investor_profile,
    )

    prob_up_pct = round(probability_up * 100.0, 1)
    prob_down_pct = round((1.0 - probability_up) * 100.0, 1)

    combined_expl = combine(signal, fundamentals_result.badge)

    return StockPredictionCard(
        symbol=sym,
        company_name=fundamentals_result.company_name or sym,
        current_price=round(current_price, 2),
        change_1d_pct=round(change_1d_pct, 2),
        signal=signal,
        probability_up=round(probability_up, 4),
        probability_up_pct=prob_up_pct,
        probability_down_pct=prob_down_pct,
        confidence_pct=confidence,
        risk_label=risk_label,
        model_reason=reason,
        fundamentals=fundamentals_result,
        combined_explanation=combined_expl,
        has_model=has_model,
        as_of_date=as_of,
        source_model="RandomForestClassifier (Calibrated)" if has_model else "Empirical Technical Baseline",
    )


def get_ranked_buy_candidates(
    investor_profile: str = "Moderate",
    supported_symbols: Optional[List[str]] = None,
    processed_dir: Path = DIR_PROCESSED,
) -> List[StockPredictionCard]:
    """
    Ranks supported stocks by model signal probability and fundamental quality,
    specifically tailored for the user's investor profile.
    """
    targets = supported_symbols or DEFAULT_SUPPORTED
    candidates: List[StockPredictionCard] = []

    for sym in targets:
        card = get_or_train_prediction(
            sym,
            investor_profile=investor_profile,
            processed_dir=processed_dir,
        )
        candidates.append(card)

    # Profile filtering and ranking logic:
    # Conservative: Strong fundamentals preferred, lower risk
    # Aggressive: Highest probability_up preferred
    def sort_key(card: StockPredictionCard):
        badge_score = 3 if card.fundamentals.badge == "Strong" else (2 if card.fundamentals.badge == "Mixed" else 1)
        risk_penalty = 0.9 if card.risk_label == "High" and investor_profile == "Conservative" else 1.0
        return (card.probability_up * badge_score * risk_penalty)

    ranked = sorted(candidates, key=sort_key, reverse=True)
    return ranked
