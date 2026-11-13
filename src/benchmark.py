"""
AlphaWatch AI — Benchmark Comparison Engine (NIFTY 50 Relative Performance)
ASTRAQUANT X 2026

Calculates rigorous benchmark metrics vs NIFTY 50:
  - Jensen's Alpha & Beta
  - Tracking Error & Information Ratio
  - Up-Market & Down-Market Capture Ratios
  - Cumulative Outperformance Time-Series
  - Zero lookahead bias, fully offline from saved index CSVs
"""

from dataclasses import dataclass, field
import ctypes
from datetime import datetime
import json
import os
from pathlib import Path
import platform
import time
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.data_loader import load_prices

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIR_REPORTS = PROJECT_ROOT / "reports"


def get_system_specs() -> Dict[str, Any]:
    """Retrieves host hardware specifications: CPU, RAM, and Python version."""
    cpu_info = platform.processor() or "Unknown CPU"
    cpu_cores = os.cpu_count() or 1
    py_version = platform.python_version()

    ram_gb = 16.0
    try:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            ram_gb = round(stat.ullTotalPhys / (1024 ** 3), 2)
    except Exception:
        ram_gb = 16.0

    return {
        "cpu": cpu_info,
        "cpu_cores": cpu_cores,
        "ram_gb": ram_gb,
        "python_version": py_version,
        "os": f"{platform.system()} {platform.release()}",
    }


def run_system_benchmark(
    n_infer_runs: int = 1000,
    n_warmup: int = 50,
    reports_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Executes empirical performance benchmarking using time.perf_counter:
      1. Training time per model (RandomForestClassifier, LogisticRegression)
      2. Inference latency per prediction (mean and 95th percentile in ms over 1000 runs after warmup)
      3. Throughput in predictions per second
      4. End-to-end time from a new raw data row to a signal
      5. Prints CPU, RAM, Python version and writes reports/latency.json
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from src.features import FEATURE_COLUMNS, build_features
    from src.signals import generate_signal

    sys_info = get_system_specs()
    print("=" * 70)
    print("ALPHAWATCH AI — SYSTEM PERFORMANCE & INFERENCE BENCHMARK")
    print("=" * 70)
    print(f"Host CPU:       {sys_info['cpu']} ({sys_info['cpu_cores']} logical cores)")
    print(f"System RAM:     {sys_info['ram_gb']} GB")
    print(f"Python Runtime: {sys_info['python_version']} ({sys_info['os']})")
    print("=" * 70)

    # Prepare feature matrix
    rng = np.random.RandomState(42)
    n_samples = 1000
    n_feats = len(FEATURE_COLUMNS)
    X_train = rng.randn(n_samples, n_feats)
    y_train = rng.randint(0, 2, n_samples)
    X_sample = X_train[0:1]

    # Benchmark Scaler
    scaler = StandardScaler().fit(X_train)
    X_train_sc = scaler.transform(X_train)
    X_sample_sc = scaler.transform(X_sample)

    models_to_test = {
        "RandomForestClassifier": RandomForestClassifier(n_estimators=100, max_depth=5, min_samples_split=10, random_state=42),
        "LogisticRegression": LogisticRegression(max_iter=500, random_state=42),
    }

    try:
        from xgboost import XGBClassifier
        models_to_test["XGBClassifier"] = XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42, eval_metric="logloss")
    except ImportError:
        pass

    training_results = {}
    inference_results = {}

    for name, model in models_to_test.items():
        # 1. Training Latency
        t_tr0 = time.perf_counter()
        model.fit(X_train_sc, y_train)
        t_tr_ms = (time.perf_counter() - t_tr0) * 1000.0

        training_results[name] = {
            "training_time_ms": round(t_tr_ms, 2),
            "training_time_sec": round(t_tr_ms / 1000.0, 4),
            "samples": n_samples,
            "features": n_feats,
        }

        # 2. Warm-up
        for _ in range(n_warmup):
            _ = model.predict_proba(X_sample_sc)

        # 3. 1000 measured runs
        latencies_ms = []
        t_loop_start = time.perf_counter()
        for _ in range(n_infer_runs):
            t_inf0 = time.perf_counter()
            _ = model.predict_proba(X_sample_sc)
            latencies_ms.append((time.perf_counter() - t_inf0) * 1000.0)
        total_time_sec = time.perf_counter() - t_loop_start

        mean_ms = float(np.mean(latencies_ms))
        p95_ms = float(np.percentile(latencies_ms, 95))
        throughput_pps = float(n_infer_runs / total_time_sec) if total_time_sec > 0 else 0.0

        inference_results[name] = {
            "runs": n_infer_runs,
            "mean_latency_ms": round(mean_ms, 4),
            "p95_latency_ms": round(p95_ms, 4),
            "throughput_preds_per_sec": round(throughput_pps, 1),
        }
        print(f"[{name}] Training: {t_tr_ms:.1f}ms | Inference: {mean_ms:.3f}ms (P95: {p95_ms:.3f}ms) | Throughput: {throughput_pps:.1f} preds/sec")

    # 4. End-to-End latency from a new raw data row to a signal
    e2e_dates = pd.date_range("2026-01-01", periods=60)
    base_df = pd.DataFrame({
        "Date": e2e_dates,
        "Open": np.linspace(100, 150, 60),
        "High": np.linspace(102, 152, 60),
        "Low": np.linspace(98, 148, 60),
        "Close": np.linspace(100, 150, 60),
        "Volume": [100000] * 60,
    })

    rf_model = models_to_test["RandomForestClassifier"]
    # Warmup
    for _ in range(10):
        _f = build_features(base_df)
        _last = pd.DataFrame([_f[FEATURE_COLUMNS].iloc[-1].values], columns=FEATURE_COLUMNS).fillna(0.0)
        _p = float(rf_model.predict_proba(scaler.transform(_last))[0, 1])
        _ = generate_signal(_p, profile="Moderate", as_of="2026-03-01")

    e2e_latencies = []
    for _ in range(200):
        t_e2e_0 = time.perf_counter()
        feat_df = build_features(base_df)
        last_row = pd.DataFrame([feat_df[FEATURE_COLUMNS].iloc[-1].values], columns=FEATURE_COLUMNS).fillna(0.0)
        prob = float(rf_model.predict_proba(scaler.transform(last_row))[0, 1])
        _ = generate_signal(prob, profile="Moderate", as_of="2026-03-01")
        e2e_latencies.append((time.perf_counter() - t_e2e_0) * 1000.0)

    mean_e2e_ms = round(float(np.mean(e2e_latencies)), 3)
    p95_e2e_ms = round(float(np.percentile(e2e_latencies, 95)), 3)
    print(f"[End-to-End Pipeline] Mean: {mean_e2e_ms:.2f}ms | P95: {p95_e2e_ms:.2f}ms (over 200 runs)")

    benchmark_summary = {
        "system": sys_info,
        "training": training_results,
        "inference": inference_results,
        "end_to_end": {
            "description": "Raw OHLCV data row -> Feature engineering -> Scaling -> RF inference -> Signal generation",
            "mean_latency_ms": mean_e2e_ms,
            "p95_latency_ms": p95_e2e_ms,
            "measured_runs": 200,
        },
        "benchmarked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    out_dir = reports_dir or DIR_REPORTS
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / "latency.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_summary, f, indent=2)

    print(f"Report written to: {report_file.resolve()}")
    return benchmark_summary



@dataclass
class BenchmarkComparison:
    """Benchmark performance comparison metrics."""
    symbol_or_portfolio: str
    start_date: str
    end_date: str
    trading_days: int
    portfolio_annual_return_pct: float
    benchmark_annual_return_pct: float
    portfolio_volatility_pct: float
    benchmark_volatility_pct: float
    beta: float
    alpha_pct: float
    r_squared: float
    tracking_error_pct: float
    information_ratio: float
    up_capture_pct: float
    down_capture_pct: float
    cumulative_series: List[Dict[str, Any]] = field(default_factory=list)


def compare_with_nifty(
    portfolio_returns: Optional[pd.Series] = None,
    symbol: Optional[str] = None,
    risk_free_rate: float = 0.065,  # 6.5% Indian 91-day T-Bill rate
) -> BenchmarkComparison:
    """
    Compares daily return series against saved NIFTY 50 index returns.
    """
    res_nifty = load_prices("NIFTY50")
    nifty_df = res_nifty[0] if isinstance(res_nifty, tuple) else res_nifty
    if nifty_df.empty:
        return _empty_benchmark(symbol or "PORTFOLIO")

    nifty_df = nifty_df.copy()
    nifty_df["Date"] = pd.to_datetime(nifty_df["Date"])
    nifty_df = nifty_df.sort_values("Date").drop_duplicates(subset=["Date"]).set_index("Date")
    nifty_ret = nifty_df["Close"].pct_change().dropna()

    if portfolio_returns is not None and not portfolio_returns.empty:
        port_series = portfolio_returns.copy()
        if not isinstance(port_series.index, pd.DatetimeIndex):
            port_series.index = pd.to_datetime(port_series.index)
        label = symbol or "User Portfolio"
    elif symbol is not None:
        res_stock = load_prices(symbol)
        stock_df = res_stock[0] if isinstance(res_stock, tuple) else res_stock
        if stock_df.empty:
            return _empty_benchmark(symbol)
        stock_df = stock_df.copy()
        stock_df["Date"] = pd.to_datetime(stock_df["Date"])
        stock_df = stock_df.sort_values("Date").drop_duplicates(subset=["Date"]).set_index("Date")
        port_series = stock_df["Close"].pct_change().dropna()
        label = symbol
    else:
        return _empty_benchmark("PORTFOLIO")

    # Align on common trading days
    combined = pd.DataFrame({"Portfolio": port_series, "Benchmark": nifty_ret}).dropna()
    if len(combined) < 10:
        return _empty_benchmark(label)

    rp = combined["Portfolio"]
    rm = combined["Benchmark"]
    n_days = len(combined)

    # Annualized Returns & Volatilities
    ann_rp = float(rp.mean() * 250.0)
    ann_rm = float(rm.mean() * 250.0)
    vol_p = float(rp.std() * np.sqrt(250.0))
    vol_m = float(rm.std() * np.sqrt(250.0))

    # Beta and Alpha
    cov_pm = float(np.cov(rp, rm)[0, 1])
    var_m = float(np.var(rm, ddof=1))
    beta = float(cov_pm / var_m) if var_m > 1e-8 else 1.0

    # Jensen's Alpha = Rp - [Rf + Beta * (Rm - Rf)]
    alpha = ann_rp - (risk_free_rate + beta * (ann_rm - risk_free_rate))

    # Correlation & R^2
    corr = float(np.corrcoef(rp, rm)[0, 1]) if vol_p > 0 and vol_m > 0 else 0.0
    r_squared = float(corr ** 2)

    # Tracking Error & Information Ratio
    excess_ret = rp - rm
    tracking_error = float(excess_ret.std() * np.sqrt(250.0))
    info_ratio = float((ann_rp - ann_rm) / (tracking_error + 1e-6))

    # Up/Down Market Capture
    up_days = combined[combined["Benchmark"] > 0]
    down_days = combined[combined["Benchmark"] < 0]

    if not up_days.empty and up_days["Benchmark"].sum() > 0:
        up_capture = float((up_days["Portfolio"].mean() / up_days["Benchmark"].mean()) * 100.0)
    else:
        up_capture = 100.0

    if not down_days.empty and abs(down_days["Benchmark"].sum()) > 0:
        down_capture = float((down_days["Portfolio"].mean() / down_days["Benchmark"].mean()) * 100.0)
    else:
        down_capture = 100.0

    # Cumulative series for charts
    cum_p = (1.0 + rp).cumprod() - 1.0
    cum_m = (1.0 + rm).cumprod() - 1.0

    chart_series = []
    for dt, p_val, m_val in zip(combined.index, cum_p, cum_m):
        chart_series.append(
            {
                "date": dt.strftime("%Y-%m-%d"),
                "portfolio_return_pct": round(float(p_val) * 100.0, 2),
                "nifty_return_pct": round(float(m_val) * 100.0, 2),
                "outperformance_pct": round(float(p_val - m_val) * 100.0, 2),
            }
        )

    return BenchmarkComparison(
        symbol_or_portfolio=label,
        start_date=combined.index[0].strftime("%Y-%m-%d"),
        end_date=combined.index[-1].strftime("%Y-%m-%d"),
        trading_days=n_days,
        portfolio_annual_return_pct=round(ann_rp * 100.0, 2),
        benchmark_annual_return_pct=round(ann_rm * 100.0, 2),
        portfolio_volatility_pct=round(vol_p * 100.0, 2),
        benchmark_volatility_pct=round(vol_m * 100.0, 2),
        beta=round(beta, 2),
        alpha_pct=round(alpha * 100.0, 2),
        r_squared=round(r_squared, 3),
        tracking_error_pct=round(tracking_error * 100.0, 2),
        information_ratio=round(info_ratio, 2),
        up_capture_pct=round(up_capture, 2),
        down_capture_pct=round(down_capture, 2),
        cumulative_series=chart_series,
    )


def _empty_benchmark(label: str) -> BenchmarkComparison:
    return BenchmarkComparison(
        symbol_or_portfolio=label,
        start_date="N/A",
        end_date="N/A",
        trading_days=0,
        portfolio_annual_return_pct=0.0,
        benchmark_annual_return_pct=0.0,
        portfolio_volatility_pct=0.0,
        benchmark_volatility_pct=0.0,
        beta=1.0,
        alpha_pct=0.0,
        r_squared=0.0,
        tracking_error_pct=0.0,
        information_ratio=0.0,
        up_capture_pct=100.0,
        down_capture_pct=100.0,
        cumulative_series=[],
    )


if __name__ == "__main__":
    run_system_benchmark()

