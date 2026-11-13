"""
AlphaWatch AI — Walk-Forward ML Engine & Predictor
ASTRAQUANT X 2026

Enforces strict ML research principles:
  1. Target: y(t) = 1 if Close(t+1) > Close(t) else 0
  2. Features derived strictly from past data up to t
  3. Chronological 70/15/15 split (Train / Validation / Test)
  4. 5-Fold Expanding Walk-Forward Cross-Validation
  5. Scalers fit exclusively on Training slices
  6. Logistic Regression baseline, Random Forest main
  7. Probability calibration performed on validation split only
  8. Feature importance & explainability fallback
  9. Joblib model bundle serialization paired with metrics JSON
  10. Profile-adapted signal thresholds (Conservative, Moderate, Aggressive)
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIR_MODELS_SAVED = PROJECT_ROOT / "models" / "saved"


@dataclass
class DatasetSplits:
    """Chronologically separated datasets with zero temporal leakage."""
    X_train: pd.DataFrame
    y_train: pd.Series
    X_val: pd.DataFrame
    y_val: pd.Series
    X_test: pd.DataFrame
    y_test: pd.Series
    train_dates: Tuple[str, str]
    val_dates: Tuple[str, str]
    test_dates: Tuple[str, str]


@dataclass
class ModelMetrics:
    """Standardized performance metrics evaluation."""
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    brier_score: float
    confusion_matrix: Optional[List[List[int]]] = None
    majority_baseline_accuracy: Optional[float] = None


def chronological_split(
    X: pd.DataFrame,
    y: pd.Series,
    dates: pd.Series,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> DatasetSplits:
    """
    Performs strict chronological 70/15/15 dataset partitioning.
    No shuffling; preserves temporal sequence.
    """
    n = len(X)
    if n < 10:
        raise ValueError(f"Insufficient samples for 70/15/15 split: {n} rows")

    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
    X_val, y_val = X.iloc[train_end:val_end], y.iloc[train_end:val_end]
    X_test, y_test = X.iloc[val_end:], y.iloc[val_end:]

    date_strs = dates.astype(str)
    train_dates = (date_strs.iloc[0], date_strs.iloc[train_end - 1])
    val_dates = (date_strs.iloc[train_end], date_strs.iloc[val_end - 1])
    test_dates = (date_strs.iloc[val_end], date_strs.iloc[-1])

    return DatasetSplits(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
        train_dates=train_dates,
        val_dates=val_dates,
        test_dates=test_dates,
    )


def expanding_walk_forward_cv(
    X: pd.DataFrame,
    y: pd.Series,
    n_folds: int = 5,
) -> List[Dict[str, float]]:
    """
    Evaluates model stability across expanding chronological windows:
      Fold k: Train on [0 : k*step], Validate on [k*step : (k+1)*step].
    """
    n = len(X)
    if n < n_folds * 4:
        return []

    step = n // (n_folds + 1)
    fold_scores: List[Dict[str, float]] = []

    for fold in range(1, n_folds + 1):
        train_idx = fold * step
        val_idx = min(train_idx + step, n)

        X_tr, y_tr = X.iloc[:train_idx], y.iloc[:train_idx]
        X_va, y_va = X.iloc[train_idx:val_idx], y.iloc[train_idx:val_idx]

        # Ensure both classes are present in fold
        if len(np.unique(y_tr)) < 2 or len(np.unique(y_va)) < 2:
            continue

        scaler = StandardScaler()
        X_tr_sc = scaler.fit_transform(X_tr)
        X_va_sc = scaler.transform(X_va)

        model = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=42)
        model.fit(X_tr_sc, y_tr)

        preds = model.predict(X_va_sc)
        probs = model.predict_proba(X_va_sc)[:, 1]

        acc = float(accuracy_score(y_va, preds))
        prec = float(precision_score(y_va, preds, zero_division=0))
        brier = float(brier_score_loss(y_va, probs))
        try:
            auc = float(roc_auc_score(y_va, probs))
        except ValueError:
            auc = 0.5

        fold_scores.append({
            "fold": fold,
            "train_samples": train_idx,
            "train_size": train_idx,
            "val_samples": len(y_va),
            "val_size": len(y_va),
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "roc_auc": round(auc, 4),
            "brier_score": round(brier, 4),
        })

    return fold_scores


def evaluate_classifier(y_true: pd.Series, y_pred: np.ndarray, y_prob: np.ndarray) -> ModelMetrics:
    """Calculates standardized classification metrics and compares with majority-class baseline."""
    from sklearn.metrics import confusion_matrix
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    brier = float(brier_score_loss(y_true, y_prob))
    try:
        auc = float(roc_auc_score(y_true, y_prob))
    except ValueError:
        auc = 0.5

    try:
        cm = confusion_matrix(y_true, y_pred).tolist()
    except Exception:
        cm = [[0, 0], [0, 0]]

    # Majority-class baseline: always predict the most frequent class in y_true
    if len(y_true) > 0:
        majority_class = int(pd.Series(y_true).mode().iloc[0])
        baseline_preds = np.full_like(y_pred, majority_class)
        baseline_acc = float(accuracy_score(y_true, baseline_preds))
    else:
        baseline_acc = 0.5

    return ModelMetrics(
        accuracy=round(acc, 4),
        precision=round(prec, 4),
        recall=round(rec, 4),
        f1=round(f1, 4),
        roc_auc=round(auc, 4),
        brier_score=round(brier, 4),
        confusion_matrix=cm,
        majority_baseline_accuracy=round(baseline_acc, 4),
    )


def train_and_calibrate_pipeline(
    splits: DatasetSplits,
    model_type: str = "random_forest",
) -> Tuple[Any, StandardScaler, CalibratedClassifierCV, ModelMetrics, ModelMetrics]:
    """
    Trains base classifier (RandomForest, LogisticRegression, or XGBoost),
    calibrates probabilities on validation split,
    and returns (base_model, scaler, calibrated_model, val_metrics, test_metrics).
    """
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(splits.X_train)
    X_val_scaled = scaler.transform(splits.X_val)
    X_test_scaled = scaler.transform(splits.X_test)

    # Base Classifier selection
    if model_type == "logistic_regression":
        base_model = LogisticRegression(C=1.0, max_iter=500, random_state=42)
    elif model_type in ("xgboost", "xgb"):
        try:
            from xgboost import XGBClassifier
            base_model = XGBClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.05,
                random_state=42,
                eval_metric="logloss",
            )
        except ImportError:
            print("[NOTICE] XGBClassifier not installed; using RandomForestClassifier with fixed random seed 42.")
            base_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                min_samples_split=10,
                random_state=42,
            )
    else:
        base_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            min_samples_split=10,
            random_state=42,
        )

    base_model.fit(X_train_scaled, splits.y_train)

    # Calibration strictly using pre-fit base model on VALIDATION set
    try:
        from sklearn.frozen import FrozenEstimator
        calibrated_model = CalibratedClassifierCV(estimator=FrozenEstimator(base_model))
    except (ImportError, TypeError):
        # Fallback for earlier scikit-learn versions
        calibrated_model = CalibratedClassifierCV(estimator=base_model, cv="prefit")

    calibrated_model.fit(X_val_scaled, splits.y_val)

    # Validation Evaluation
    val_pred = calibrated_model.predict(X_val_scaled)
    val_prob = calibrated_model.predict_proba(X_val_scaled)[:, 1]
    val_metrics = evaluate_classifier(splits.y_val, val_pred, val_prob)

    # Test Evaluation (Final holdout, never tuned on)
    test_pred = calibrated_model.predict(X_test_scaled)
    test_prob = calibrated_model.predict_proba(X_test_scaled)[:, 1]
    test_metrics = evaluate_classifier(splits.y_test, test_pred, test_prob)

    return base_model, scaler, calibrated_model, val_metrics, test_metrics


def extract_feature_importance(model: Any, feature_names: List[str]) -> List[Dict[str, Any]]:
    """Extracts sorted feature importance weights from trained base model."""
    importances: List[Dict[str, Any]] = []

    if hasattr(model, "feature_importances_"):
        weights = model.feature_importances_
        for name, weight in zip(feature_names, weights):
            importances.append({"feature": name, "importance": round(float(weight), 4)})
    elif hasattr(model, "coef_"):
        weights = model.coef_[0]
        for name, weight in zip(feature_names, weights):
            importances.append({"feature": name, "importance": round(float(abs(weight)), 4)})
    else:
        for name in feature_names:
            importances.append({"feature": name, "importance": 0.05})

    importances.sort(key=lambda x: x["importance"], reverse=True)
    return importances


def generate_signal_and_reason(
    probability_up: float,
    feature_row: pd.Series,
    top_features: List[Dict[str, Any]],
    investor_profile: str = "Moderate",
) -> Tuple[str, str, float]:
    """
    Translates calibrated probability and top driving features into an educational signal.

    Profile thresholds:
      - Conservative: BUY if P >= 0.60, SELL if P <= 0.40, else HOLD
      - Moderate:     BUY if P >= 0.55, SELL if P <= 0.45, else HOLD
      - Aggressive:   BUY if P >= 0.52, SELL if P <= 0.48, else HOLD

    Returns:
        (signal_label, human_readable_reason, confidence_percentage)
    """
    profile_clean = investor_profile.strip().title()
    if profile_clean == "Conservative":
        buy_threshold, sell_threshold = 0.60, 0.40
    elif profile_clean == "Aggressive":
        buy_threshold, sell_threshold = 0.52, 0.48
    else:  # Moderate (default)
        buy_threshold, sell_threshold = 0.55, 0.45

    if probability_up >= buy_threshold:
        signal = "BUY"
        confidence = probability_up * 100.0
    elif probability_up <= sell_threshold:
        signal = "SELL"
        confidence = (1.0 - probability_up) * 100.0
    else:
        signal = "HOLD"
        confidence = (1.0 - abs(probability_up - 0.50) * 2) * 100.0

    # Build plain-English educational explanation based on dominant features
    reasons: List[str] = []
    top_feature_names = [f["feature"] for f in top_features[:3]]

    if "rsi_14" in top_feature_names:
        rsi = float(feature_row.get("rsi_14", 50.0))
        if rsi < 35:
            reasons.append(f"RSI-14 ({rsi:.1f}) is in oversold territory")
        elif rsi > 65:
            reasons.append(f"RSI-14 ({rsi:.1f}) indicates extended overbought conditions")
        else:
            reasons.append(f"RSI-14 ({rsi:.1f}) is in a neutral momentum zone")

    if "sma_dist_50" in top_feature_names or "sma_dist_20" in top_feature_names:
        sma_dist = float(feature_row.get("sma_dist_50", feature_row.get("sma_dist_20", 0.0)))
        if sma_dist > 0:
            reasons.append(f"Price is trading {abs(sma_dist)*100:.1f}% above its medium-term trend")
        else:
            reasons.append(f"Price is trading {abs(sma_dist)*100:.1f}% below its medium-term trend")

    if "volatility_20d" in top_feature_names:
        vol = float(feature_row.get("volatility_20d", 0.15))
        reasons.append(f"20-day annualized volatility stands at {vol*100:.1f}%")

    if not reasons:
        reasons.append(f"Model probability {probability_up*100:.1f}% aligned with historical statistical patterns")

    reason_str = "; ".join(reasons)
    return signal, reason_str, round(confidence, 1)


def explain_prediction_shap(
    model: Any,
    feature_sample: Union[pd.DataFrame, pd.Series, np.ndarray],
    feature_names: List[str],
) -> List[Dict[str, Any]]:
    """
    Computes top 5 driving features for a single sample using SHAP TreeExplainer.
    Falls back gracefully to model feature importances if SHAP fails or is not installed.
    """
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        if isinstance(feature_sample, pd.Series):
            X_in = pd.DataFrame([feature_sample.values], columns=feature_names)
        elif isinstance(feature_sample, np.ndarray) and feature_sample.ndim == 1:
            X_in = feature_sample.reshape(1, -1)
        else:
            X_in = feature_sample

        shap_vals = explainer.shap_values(X_in)
        if isinstance(shap_vals, list):
            vals = shap_vals[1][0]
        elif hasattr(shap_vals, "shape") and len(shap_vals.shape) == 3:
            vals = shap_vals[0, :, 1]
        else:
            vals = shap_vals[0]

        top_indices = np.argsort(np.abs(vals))[::-1][:5]
        return [
            {
                "feature": feature_names[i],
                "importance": round(float(abs(vals[i])), 4),
                "shap_value": round(float(vals[i]), 4),
            }
            for i in top_indices
        ]
    except Exception:
        return extract_feature_importance(model, feature_names)[:5]


def train_and_save_symbol_model(
    symbol: str,
    df_features: pd.DataFrame,
    save_dir: Path = DIR_MODELS_SAVED,
) -> Dict[str, Any]:
    """
    Executes full modeling lifecycle for a given symbol:
      - Chronological split
      - Expanding walk-forward CV
      - Random forest + calibration
      - Evaluation on test set
      - Serialization to models/saved/<symbol>_rf.joblib and JSON metrics.
    """
    import time
    from sklearn.calibration import calibration_curve

    save_dir.mkdir(parents=True, exist_ok=True)
    sym = symbol.strip().upper()

    from src.features import FEATURE_COLUMNS

    # Extract clean trainable rows
    clean_mask = df_features[FEATURE_COLUMNS].notna().all(axis=1) & df_features["target_up"].notna()
    clean_df = df_features[clean_mask].copy()

    if len(clean_df) < 15:
        return {"status": "error", "message": f"Insufficient clean rows for {sym}: {len(clean_df)}"}

    X = clean_df[FEATURE_COLUMNS]
    y = clean_df["target_up"].astype(int)
    dates = clean_df["Date"]

    splits = chronological_split(X, y, dates)
    wf_cv_scores = expanding_walk_forward_cv(X, y, n_folds=5)

    # Measure training latency
    t_start_train = time.perf_counter()
    base_rf, scaler, cal_rf, val_metrics, test_metrics = train_and_calibrate_pipeline(
        splits, model_type="random_forest"
    )
    training_time_sec = round(time.perf_counter() - t_start_train, 4)

    # Measure inference latency on a single test sample
    t_start_infer = time.perf_counter()
    sample_sc = scaler.transform(splits.X_test.iloc[0:1])
    _ = cal_rf.predict_proba(sample_sc)
    infer_time_sec = round(time.perf_counter() - t_start_infer, 6)

    # Validation calibration curve
    val_probs = cal_rf.predict_proba(scaler.transform(splits.X_val))[:, 1]
    prob_true, prob_pred = calibration_curve(splits.y_val, val_probs, n_bins=10)
    calibration_data = {
        "prob_true": [round(float(p), 4) for p in prob_true],
        "prob_pred": [round(float(p), 4) for p in prob_pred],
    }

    feature_importances = extract_feature_importance(base_rf, FEATURE_COLUMNS)
    top_shap_features = explain_prediction_shap(base_rf, splits.X_test.iloc[0:1], FEATURE_COLUMNS)

    # Save model pipeline bundle
    model_bundle = {
        "symbol": sym,
        "base_model": base_rf,
        "scaler": scaler,
        "calibrated_model": cal_rf,
        "feature_names": FEATURE_COLUMNS,
        "version": "1.0.0",
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    model_file = save_dir / f"{sym}_rf.joblib"
    joblib.dump(model_bundle, model_file)

    # Save metrics JSON
    metrics_data = {
        "symbol": sym,
        "model_version": "1.0.0",
        "model_type": "RandomForestClassifier (Calibrated)",
        "train_samples": len(splits.X_train),
        "val_samples": len(splits.X_val),
        "test_samples": len(splits.X_test),
        "train_date_range": splits.train_dates,
        "val_date_range": splits.val_dates,
        "test_date_range": splits.test_dates,
        "val_metrics": asdict(val_metrics),
        "test_metrics": asdict(test_metrics),
        "walk_forward_cv": wf_cv_scores,
        "calibration_curve": calibration_data,
        "top_features": top_shap_features,
        "all_feature_importances": feature_importances,
        "training_time_sec": training_time_sec,
        "inference_time_per_sample_sec": infer_time_sec,
        "as_of_date": splits.test_dates[1],
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    metrics_file = save_dir / f"{sym}_metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)

    # Save to reports/latency.json
    try:
        latency_file = PROJECT_ROOT / "reports" / "latency.json"
        latency_file.parent.mkdir(parents=True, exist_ok=True)
        latency_dict = {}
        if latency_file.exists():
            try:
                with open(latency_file, "r", encoding="utf-8") as lf:
                    latency_dict = json.load(lf)
            except Exception:
                latency_dict = {}
        latency_dict[sym] = {
            "training_time_sec": training_time_sec,
            "inference_time_per_sample_sec": infer_time_sec,
            "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(latency_file, "w", encoding="utf-8") as lf:
            json.dump(latency_dict, lf, indent=2)
    except Exception as e:
        print(f"[WARNING] Could not write latency report: {e}")

    return metrics_data
