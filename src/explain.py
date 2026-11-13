"""
AlphaWatch AI — Explainable AI (XAI) Engine & Decision Intelligence
ASTRAQUANT X 2026

Transparent ML Decision Explanations:
  1. Reuses existing pipeline: load saved prices, make_features, saved model/calibrator, generate_signal.
  2. Local SHAP prediction attribution via shap.TreeExplainer (class 1, up-probability before calibration).
  3. Verifies SHAP additivity: base_value + sum(contributions) == raw_probability (within 1e-6).
  4. Explicit fallbacks: 'logistic coefficients' or 'global importance' (always explicitly labelled).
  5. Rule-based factor cards (Positive & Negative) governed by src/explain_config.py.
  6. Calibrated probability meter with active profile thresholds and validation metrics.
  7. Smart risk alerts with trigger values.
  8. Template-based summary sentence (zero fabricated LLM text).
  9. In-memory caching with mtime invalidation on model or CSV updates.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd

from src.data_loader import load_nifty50, load_prices, load_vix
from src.explain_config import (
    FACTOR_RULES,
    FEATURE_METADATA,
    MAX_CONCENTRATION_THRESHOLD_PCT,
    RISK_ALERT_CONFIG,
    SUPPORTED_SYMBOLS,
)
from src.features import FEATURE_COLUMNS, build_features
from src.fundamentals import load_and_evaluate_symbol
from src.models import DIR_MODELS_SAVED, extract_feature_importance
from src.portfolio import Holding, evaluate_portfolio
from src.signals import PROFILES, generate_signal

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# In-memory explanation cache:
# Key: (symbol, as_of_date, model_version, profile)
# Value: (result_dict, model_mtime, csv_mtime)
_EXPLAIN_CACHE: Dict[Tuple[str, str, str, str], Tuple[Dict[str, Any], float, float]] = {}


def format_feature_value(fname: str, val: float) -> str:
    """Formats numeric feature values into readable presentation strings."""
    if fname in ("ret_1d", "ret_5d", "ret_20d", "nifty_ret_1d", "nifty_ret_5d", "dist_52w_high"):
        return f"{val * 100.0:+.2f}%"
    if fname in ("sma_dist_5", "sma_dist_20", "sma_dist_50", "ema_dist_5", "ema_dist_20", "ema_dist_50"):
        return f"{val * 100.0:+.1f}%"
    if fname == "rsi_14":
        return f"{val:.1f}"
    if fname == "volatility_20d":
        return f"{val * 100.0:.1f}%"
    if fname in ("volume_ratio_20", "delivery_ratio_20"):
        return f"{val:.2f}x"
    if fname == "delivery_pct":
        return f"{val * 100.0:.1f}%"
    if fname == "vix_level":
        return f"{val:.2f}"
    if fname == "vix_change_5d":
        return f"{val * 100.0:+.2f}%"
    if fname == "hl_range":
        return f"{val * 100.0:.2f}%"
    return f"{val:.4f}"


def get_file_mtime(path: Path) -> float:
    """Returns file modification time safely, or 0.0 if file does not exist."""
    try:
        return path.stat().st_mtime if path.exists() else 0.0
    except OSError:
        return 0.0


def compute_shap_contributions(
    base_model: Any,
    scaler: Any,
    latest_feature_row: pd.Series,
    feature_names: List[str],
    raw_probability: float,
) -> Tuple[float, List[Dict[str, Any]], str, bool]:
    """
    Computes local SHAP individual-prediction attributions for class 1 (UP).
    Returns (base_value, contributions_list, method, is_verified).
    """
    X_df = pd.DataFrame([latest_feature_row[feature_names].values], columns=feature_names).fillna(0.0)
    X_scaled = scaler.transform(X_df)

    method = "TreeExplainer"
    is_verified = True
    base_value = 0.50
    contributions: List[Dict[str, Any]] = []

    try:
        import shap
        explainer = shap.TreeExplainer(base_model)
        shap_vals = explainer.shap_values(X_scaled)
        ev = explainer.expected_value

        # Handle various SHAP return dimensions: list of arrays or 3D ndarray
        if isinstance(shap_vals, list):
            # Class 1 (up) is at index 1
            vals = shap_vals[1][0] if len(shap_vals) > 1 else shap_vals[0][0]
            base_val = float(ev[1]) if isinstance(ev, (list, np.ndarray)) and len(ev) > 1 else float(ev)
        elif hasattr(shap_vals, "shape") and len(shap_vals.shape) == 3:
            # Shape: (1, n_features, 2)
            vals = shap_vals[0, :, 1]
            base_val = float(ev[1]) if isinstance(ev, (list, np.ndarray)) and len(ev) > 1 else float(ev)
        else:
            vals = shap_vals[0]
            base_val = float(ev)

        base_value = base_val
        sum_contribs = float(np.sum(vals))

        # Check additivity: base_value + sum(contributions) == raw_probability within 1e-6
        additivity_diff = abs((base_val + sum_contribs) - raw_probability)
        if additivity_diff > 1e-6:
            method = "unverified"
            is_verified = False

        for i, fname in enumerate(feature_names):
            raw_val = float(latest_feature_row.get(fname, 0.0))
            sv = float(vals[i])
            contributions.append({
                "feature": fname,
                "label": FEATURE_METADATA.get(fname, {}).get("label", fname),
                "value": raw_val,
                "value_formatted": format_feature_value(fname, raw_val),
                "shap_contribution": round(sv, 8),
                "direction": "positive" if sv > 0 else "negative",
            })

        return base_value, contributions, method, is_verified

    except Exception as e:
        logger.warning(f"TreeExplainer SHAP computation failed ({e}); attempting fallback.")

    # Fallback 1: Logistic Regression linear coefficients
    if hasattr(base_model, "coef_"):
        method = "logistic coefficients"
        is_verified = True
        coefs = base_model.coef_[0]
        intercept = float(base_model.intercept_[0]) if hasattr(base_model, "intercept_") else 0.0
        # Contribution = coef * x_scaled
        linear_contribs = coefs * X_scaled[0]
        base_value = float(1.0 / (1.0 + np.exp(-intercept)))

        for i, fname in enumerate(feature_names):
            raw_val = float(latest_feature_row.get(fname, 0.0))
            c_val = float(linear_contribs[i])
            contributions.append({
                "feature": fname,
                "label": FEATURE_METADATA.get(fname, {}).get("label", fname),
                "value": raw_val,
                "value_formatted": format_feature_value(fname, raw_val),
                "shap_contribution": round(c_val, 6),
                "direction": "positive" if c_val > 0 else "negative",
            })
        return base_value, contributions, method, is_verified

    # Fallback 2: Global feature importance
    method = "global importance"
    is_verified = False
    global_imps = extract_feature_importance(base_model, feature_names)
    for item in global_imps:
        fname = item["feature"]
        raw_val = float(latest_feature_row.get(fname, 0.0))
        contributions.append({
            "feature": fname,
            "label": FEATURE_METADATA.get(fname, {}).get("label", fname),
            "value": raw_val,
            "value_formatted": format_feature_value(fname, raw_val),
            "shap_contribution": 0.0,
            "direction": "neutral",
        })

    return 0.50, contributions, method, is_verified


def evaluate_factors(
    feature_dict: Dict[str, float],
    contributions_dict: Dict[str, float],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Evaluates rule table in src/explain_config.py:
    A factor is shown ONLY if its rule matches the actual data
    AND the matching feature's SHAP contribution has the exact same direction.
    """
    positive_factors: List[Dict[str, Any]] = []
    negative_factors: List[Dict[str, Any]] = []

    for rule in FACTOR_RULES:
        fname = rule["feature"]
        direction = rule["direction"]
        val = feature_dict.get(fname, 0.0)
        shap_contrib = contributions_dict.get(fname, 0.0)

        # 1. Check if the quantitative rule fires
        try:
            fires = rule["condition"](val, feature_dict)
        except Exception:
            fires = False

        if not fires:
            continue

        # 2. Check that SHAP contribution has the exact same direction
        if direction == "positive" and shap_contrib > 0.0:
            val_disp = format_feature_value(fname, val)
            reason = rule["reason_template"].format(val_disp=val_disp)
            positive_factors.append({
                "feature": fname,
                "label": FEATURE_METADATA.get(fname, {}).get("label", fname),
                "value": round(val, 4),
                "value_formatted": val_disp,
                "shap_contribution": round(shap_contrib, 4),
                "threshold_rule": rule["threshold_desc"],
                "reason": reason,
            })
        elif direction == "negative" and shap_contrib < 0.0:
            val_disp = format_feature_value(fname, val)
            reason = rule["reason_template"].format(val_disp=val_disp)
            negative_factors.append({
                "feature": fname,
                "label": FEATURE_METADATA.get(fname, {}).get("label", fname),
                "value": round(val, 4),
                "value_formatted": val_disp,
                "shap_contribution": round(shap_contrib, 4),
                "threshold_rule": rule["threshold_desc"],
                "reason": reason,
            })

    # Sort factors by absolute SHAP contribution magnitude
    positive_factors.sort(key=lambda x: abs(x["shap_contribution"]), reverse=True)
    negative_factors.sort(key=lambda x: abs(x["shap_contribution"]), reverse=True)

    return positive_factors, negative_factors


def evaluate_risk_alerts(
    feature_dict: Dict[str, float],
    calibrated_prob: float,
    current_price: float,
    profile: str,
    user_holdings: Optional[List[Holding]] = None,
    symbol: str = "",
) -> List[Dict[str, Any]]:
    """
    Computes data-backed risk alerts from explain_config.py thresholds.
    Every alert states the exact numeric value that triggered it.
    """
    alerts: List[Dict[str, Any]] = []
    cfg = PROFILES.get(profile, PROFILES["Moderate"])

    # 1. High Volatility
    vol = float(feature_dict.get("volatility_20d", 0.0))
    vol_thresh = RISK_ALERT_CONFIG["high_volatility"]["threshold"]
    if vol > vol_thresh:
        alerts.append({
            "type": "high_volatility",
            "severity": "High",
            "trigger_metric": "20-Day Annualized Volatility",
            "trigger_value": f"{vol * 100.0:.1f}%",
            "threshold_value": f"{vol_thresh * 100.0:.1f}%",
            "message": RISK_ALERT_CONFIG["high_volatility"]["message"].format(
                val=vol * 100.0, thresh=vol_thresh * 100.0
            ),
        })

    # 2. Negative Momentum
    ret_20d = float(feature_dict.get("ret_20d", 0.0))
    if ret_20d < RISK_ALERT_CONFIG["negative_momentum"]["threshold"]:
        alerts.append({
            "type": "negative_momentum",
            "severity": "Medium",
            "trigger_metric": "20-Day Return",
            "trigger_value": f"{ret_20d * 100.0:+.2f}%",
            "threshold_value": "0.00%",
            "message": RISK_ALERT_CONFIG["negative_momentum"]["message"].format(val=ret_20d * 100.0),
        })

    # 3. Low Trading Volume
    vol_ratio = float(feature_dict.get("volume_ratio_20", 1.0))
    low_vol_thresh = RISK_ALERT_CONFIG["low_volume"]["threshold"]
    if vol_ratio < low_vol_thresh:
        alerts.append({
            "type": "low_volume",
            "severity": "Medium",
            "trigger_metric": "20-Day Volume Ratio",
            "trigger_value": f"{vol_ratio:.2f}x",
            "threshold_value": f"{low_vol_thresh:.2f}x",
            "message": RISK_ALERT_CONFIG["low_volume"]["message"].format(val=vol_ratio),
        })

    # 4. Weak / In-Between Probability (HOLD zone / Neutral equilibrium)
    buy_thresh = cfg["buy_threshold"]
    sell_thresh = cfg["sell_threshold"]
    if sell_thresh < calibrated_prob < buy_thresh:
        alerts.append({
            "type": "weak_probability",
            "severity": "Low",
            "trigger_metric": "Calibrated Up-Probability",
            "trigger_value": f"{calibrated_prob * 100.0:.1f}%",
            "threshold_value": f"[{sell_thresh * 100.0:.0f}% - {buy_thresh * 100.0:.0f}%]",
            "message": (
                f"Calibrated probability is {calibrated_prob * 100.0:.1f}%, resting in the HOLD zone "
                f"between the {sell_thresh * 100.0:.0f}% SELL and {buy_thresh * 100.0:.0f}% BUY thresholds."
            ),
        })

    # 5. High Portfolio Exposure / Single-Stock Concentration
    if user_holdings and len(user_holdings) > 0 and symbol:
        try:
            # Use real portfolio valuation
            pv = evaluate_portfolio(user_holdings)
            for h_row in pv.holdings_table:
                if h_row.get("symbol") == symbol:
                    weight_pct = float(h_row.get("weight_pct", 0.0))
                    max_pos = cfg.get("max_position_pct", MAX_CONCENTRATION_THRESHOLD_PCT)
                    if weight_pct > max_pos:
                        alerts.append({
                            "type": "high_exposure",
                            "severity": "High",
                            "trigger_metric": "Portfolio Weight",
                            "trigger_value": f"{weight_pct:.1f}%",
                            "threshold_value": f"{max_pos:.1f}%",
                            "message": (
                                f"This stock represents {weight_pct:.1f}% of your portfolio, exceeding your "
                                f"{profile} profile's maximum allocation limit of {max_pos:.1f}%."
                            ),
                        })
                    break
        except Exception as e:
            logger.debug(f"Portfolio concentration check skipped: {e}")

    # 6. Deep Drawdown from 52-Week High
    dist_52w = float(feature_dict.get("dist_52w_high", 0.0))
    dd_thresh = RISK_ALERT_CONFIG["stock_drawdown"]["threshold"]
    if abs(dist_52w) > dd_thresh:
        alerts.append({
            "type": "stock_drawdown",
            "severity": "Medium",
            "trigger_metric": "Drawdown from 52-Week High",
            "trigger_value": f"{abs(dist_52w) * 100.0:.1f}%",
            "threshold_value": f"{dd_thresh * 100.0:.1f}%",
            "message": RISK_ALERT_CONFIG["stock_drawdown"]["message"].format(val=abs(dist_52w) * 100.0),
        })

    return alerts


def build_explanation_summary(
    signal: str,
    positive_factors: List[Dict[str, Any]],
    negative_factors: List[Dict[str, Any]],
    risk_alerts: List[Dict[str, Any]],
    calibrated_prob: float,
) -> str:
    """
    Constructs a deterministic, template-based natural language summary.
    No generative LLM or fabricated sentences.
    """
    prob_str = f"{calibrated_prob * 100.0:.1f}%"

    if positive_factors:
        p1 = positive_factors[0]["label"].lower()
        if len(positive_factors) > 1:
            p2 = positive_factors[1]["label"].lower()
            pos_phrase = f"positive contributions from {p1} and {p2}"
        else:
            pos_phrase = f"positive contribution from {p1}"
    else:
        pos_phrase = "limited positive technical momentum"

    if negative_factors:
        n1 = negative_factors[0]["label"].lower()
        neg_phrase = f"downward pressure from {n1}"
    elif risk_alerts:
        neg_phrase = f"an active alert on {risk_alerts[0]['trigger_metric'].lower()}"
    else:
        neg_phrase = "no immediate major technical headwinds"

    sentence = (
        f"AlphaWatch AI generated a {signal} signal with a {prob_str} calibrated up-probability, "
        f"primarily supported by {pos_phrase}, while acknowledging {neg_phrase}. "
        f"This classification represents historical walk-forward statistical likelihood and carries uncertainty. "
        f"Educational research signal, not investment advice."
    )
    return sentence


def explain_prediction(
    symbol: str,
    profile: str = "Moderate",
    user_holdings: Optional[List[Holding]] = None,
    processed_dir: Path = PROJECT_ROOT / "data" / "processed",
    models_dir: Path = DIR_MODELS_SAVED,
) -> Dict[str, Any]:
    """
    Computes or retrieves cached Explainable AI decision intelligence for a symbol.
    Reuses the existing pipeline (load_prices, build_features, saved model/calibrator, generate_signal).
    """
    t0 = time.perf_counter()
    sym = symbol.strip().upper()

    if profile not in PROFILES:
        raise ValueError(f"Invalid investor profile '{profile}'. Must be one of {list(PROFILES.keys())}")

    # Check file dependencies
    csv_file = processed_dir / f"{sym}.csv"
    model_file = models_dir / f"{sym}_rf.joblib"
    metrics_file = models_dir / f"{sym}_metrics.json"

    if not csv_file.exists():
        raise FileNotFoundError(f"Missing price history CSV for symbol '{sym}' at {csv_file}")
    if not model_file.exists():
        raise FileNotFoundError(f"Missing trained model bundle for symbol '{sym}' at {model_file}")

    csv_mtime = get_file_mtime(csv_file)
    model_mtime = get_file_mtime(model_file)

    # 1. Load price and market series
    price_df, _ = load_prices(sym, processed_dir=processed_dir)
    nifty_df = load_nifty50(processed_dir=processed_dir)
    vix_df = load_vix(processed_dir=processed_dir)
    fund_res = load_and_evaluate_symbol(sym)

    if price_df.empty or len(price_df) < 5:
        raise ValueError(f"Insufficient price history for '{sym}' (found {len(price_df)} rows).")

    as_of_date = str(price_df["Date"].iloc[-1])
    latest_close = float(price_df["Close"].iloc[-1])

    # Load metrics JSON for version & validation statistics
    model_version = "1.0.0"
    val_brier = 0.25
    val_auc = 0.50
    if metrics_file.exists():
        try:
            with open(metrics_file, "r", encoding="utf-8") as mf:
                mdata = json.load(mf)
                model_version = str(mdata.get("model_version", "1.0.0"))
                v_metrics = mdata.get("val_metrics", {})
                val_brier = float(v_metrics.get("brier_score", 0.25))
                val_auc = float(v_metrics.get("roc_auc", 0.50))
        except Exception as e:
            logger.debug(f"Could not read metrics JSON for {sym}: {e}")

    # Check cache
    cache_key = (sym, as_of_date, model_version, profile)
    if cache_key in _EXPLAIN_CACHE:
        cached_result, cached_model_mtime, cached_csv_mtime = _EXPLAIN_CACHE[cache_key]
        if cached_model_mtime == model_mtime and cached_csv_mtime == csv_mtime:
            # Valid cache hit! If user_holdings provided, re-evaluate user-specific risk alerts
            cached_copy = dict(cached_result)
            if user_holdings is not None:
                feat_dict = cached_copy.get("features_snapshot", {})
                cal_prob = cached_copy.get("calibrated_probability", 0.50)
                cached_copy["risk_alerts"] = evaluate_risk_alerts(
                    feat_dict, cal_prob, latest_close, profile, user_holdings, symbol=sym
                )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            cached_copy["execution_time_ms"] = round(elapsed_ms, 2)
            return cached_copy

    # 2. Build feature vector
    feat_df = build_features(price_df, df_nifty=nifty_df, df_vix=vix_df)
    latest_feature_row = feat_df.iloc[-1]
    feature_dict = {col: float(latest_feature_row[col]) for col in FEATURE_COLUMNS if col in latest_feature_row}

    # 3. Load model bundle (never retrain)
    bundle = joblib.load(model_file)
    base_model = bundle.get("base_model")
    cal_model = bundle.get("calibrated_model")
    scaler = bundle.get("scaler")
    feat_names = bundle.get("feature_names", FEATURE_COLUMNS)

    # 4. Predict raw and calibrated probabilities
    X_df = pd.DataFrame([latest_feature_row[feat_names].values], columns=feat_names).fillna(0.0)
    X_scaled = scaler.transform(X_df)

    raw_prob = float(base_model.predict_proba(X_scaled)[0, 1])
    calibrated_prob = float(cal_model.predict_proba(X_scaled)[0, 1]) if cal_model else raw_prob

    # 5. Generate signal via existing pipeline
    sig_result = generate_signal(
        prob=calibrated_prob,
        profile=profile,
        model_version=model_version,
        as_of=as_of_date,
    )
    signal = sig_result["signal"]

    # 6. Compute SHAP or explicit fallbacks
    base_value, all_contributions, method, is_verified = compute_shap_contributions(
        base_model=base_model,
        scaler=scaler,
        latest_feature_row=latest_feature_row,
        feature_names=feat_names,
        raw_probability=raw_prob,
    )

    contrib_dict = {c["feature"]: c["shap_contribution"] for c in all_contributions}
    # Top 5 by absolute contribution
    sorted_contribs = sorted(all_contributions, key=lambda c: abs(c["shap_contribution"]), reverse=True)
    top_five = sorted_contribs[:5]

    # Global feature importance
    global_importance_list = extract_feature_importance(base_model, feat_names)
    for g in global_importance_list:
        g["label"] = FEATURE_METADATA.get(g["feature"], {}).get("label", g["feature"])

    # 7. Evaluate Factors (Positive and Negative)
    positive_factors, negative_factors = evaluate_factors(feature_dict, contrib_dict)

    # 8. Probability Meter band & thresholds
    cfg_profile = PROFILES[profile]
    buy_thresh = cfg_profile["buy_threshold"]
    sell_thresh = cfg_profile["sell_threshold"]

    if calibrated_prob >= buy_thresh:
        band_label = "At or above BUY threshold"
    elif calibrated_prob <= sell_thresh:
        band_label = "At or below SELL threshold"
    else:
        band_label = "Between thresholds (HOLD zone)"

    # 9. Smart Risk Alerts
    risk_alerts = evaluate_risk_alerts(
        feature_dict=feature_dict,
        calibrated_prob=calibrated_prob,
        current_price=latest_close,
        profile=profile,
        user_holdings=user_holdings,
        symbol=sym,
    )

    # 10. Template Summary
    summary_text = build_explanation_summary(
        signal=signal,
        positive_factors=positive_factors,
        negative_factors=negative_factors,
        risk_alerts=risk_alerts,
        calibrated_prob=calibrated_prob,
    )

    # 11. Known Limitations
    limitations = [
        "SHAP explains the raw model output before probability calibration.",
        "Calibration shifts the directional probability but does not alter individual feature attributions.",
        "Correlated financial indicators (such as multiple moving averages) can share attribution credit.",
        "Explanations represent empirical statistical associations, not definitive causal drivers.",
    ]

    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    result: Dict[str, Any] = {
        "status": "success",
        "symbol": sym,
        "name": fund_res.company_name or sym,
        "latest_close": round(latest_close, 2),
        "as_of_date": as_of_date,
        "data_source": "Local Processed NSE Equity History",
        "model_version": model_version,
        "raw_probability": round(raw_prob, 6),
        "calibrated_probability": round(calibrated_prob, 6),
        "signal": signal,
        "profile": profile,
        "thresholds_used": {
            "buy_threshold": buy_thresh,
            "sell_threshold": sell_thresh,
            "max_position_pct": cfg_profile.get("max_position_pct", 20.0),
            "stop_loss_pct": cfg_profile.get("stop_loss_pct", 5.0),
        },
        "shap": {
            "base_value": round(base_value, 8),
            "contributions": all_contributions,
            "top_five": top_five,
            "contributions_note": "Contributions explain the raw up-probability BEFORE calibration.",
            "additivity_check": is_verified,
            "global_importance": global_importance_list,
            "global_importance_label": "Global importance (whole model)",
            "warning": None if is_verified else "SHAP additivity difference exceeded numerical tolerance.",
        },
        "factors": {
            "positive": positive_factors,
            "negative": negative_factors,
            "positive_qualifies": len(positive_factors) > 0,
            "negative_qualifies": len(negative_factors) > 0,
            "message": None if (positive_factors or negative_factors) else "No factors currently qualify under active criteria.",
        },
        "risk_alerts": risk_alerts,
        "probability_meter": {
            "calibrated_probability": round(calibrated_prob, 6),
            "percentage": round(calibrated_prob * 100.0, 1),
            "band_label": band_label,
            "buy_threshold": buy_thresh,
            "sell_threshold": sell_thresh,
            "calibration_method": "Validation-set calibration",
            "validation_brier_score": round(val_brier, 4),
            "validation_roc_auc": round(val_auc, 3),
            "disclaimer": "This is the model's estimated probability of a higher next-day close. It is not the probability of making a profit and not a guarantee.",
        },
        "summary": summary_text,
        "method": method,
        "limitations": limitations,
        "features_snapshot": feature_dict,
        "execution_time_ms": round(elapsed_ms, 2),
    }

    # Store in cache
    _EXPLAIN_CACHE[cache_key] = (result, model_mtime, csv_mtime)
    return result


def explain_trade_decision(
    symbol: str,
    investor_profile: str = "Moderate",
    processed_dir: Path = PROJECT_ROOT / "data" / "processed",
    models_dir: Path = DIR_MODELS_SAVED,
) -> Dict[str, Any]:
    """
    Backward-compatible wrapper mapping to explain_prediction.
    """
    try:
        exp = explain_prediction(
            symbol=symbol,
            profile=investor_profile,
            processed_dir=processed_dir,
            models_dir=models_dir,
        )
    except Exception as e:
        return {
            "status": "error",
            "symbol": symbol.strip().upper(),
            "message": str(e),
            "has_model": False,
        }

    # Map keys for existing endpoints/tests
    top_feats = []
    max_mag = max([abs(item["shap_contribution"]) for item in exp["shap"]["top_five"]] or [1.0])
    for item in exp["shap"]["top_five"]:
        top_feats.append({
            "feature": item["feature"],
            "label": item["label"],
            "raw_value": item["value_formatted"],
            "shap_value": item["shap_contribution"],
            "direction": "Positive" if item["shap_contribution"] > 0 else "Negative",
            "relative_strength_pct": round((abs(item["shap_contribution"]) / (max_mag or 1.0)) * 100.0, 1),
            "explanation": f"Feature value {item['value_formatted']} contributed {item['shap_contribution']:+.4f} to directional probability.",
        })

    return {
        "status": "success",
        "symbol": exp["symbol"],
        "company_name": exp["name"],
        "current_price": exp["latest_close"],
        "signal": exp["signal"],
        "probability_up": exp["calibrated_probability"],
        "probability_up_pct": exp["probability_meter"]["percentage"],
        "probability_meter": exp["probability_meter"],
        "top_features": top_feats,
        "positive_factors": exp["factors"]["positive"],
        "negative_factors": exp["factors"]["negative"],
        "risk_warnings": exp["risk_alerts"],
        "dynamic_explanation": exp["summary"],
        "final_summary": exp["summary"],
        "as_of_date": exp["as_of_date"],
        "execution_time_ms": exp["execution_time_ms"],
        "method": exp["method"],
        "limitations": exp["limitations"],
        "shap": exp["shap"],
    }
