"""
AlphaWatch AI — Leak-Free Feature Engineering Engine
ASTRAQUANT X 2026

Computes technical indicators and market context features strictly using
past information up to time t (zero lookahead bias):
  - 1, 5, 20-day returns
  - SMA distance for 5, 20, 50 days
  - EMA distance for 5, 20, 50 days
  - RSI 14 (Relative Strength Index)
  - 20-day rolling historical volatility (annualized)
  - Volume ratio (Volume / 20-day SMA Volume)
  - High-Low range ((High - Low) / Close)
  - NIFTY 50 1-day and 5-day returns
  - India VIX level and 5-day change
  - Delivery percentage and 20-day delivery ratio
  - Distance from 52-week (252-day) High
  - Target: y(t) = 1 if Close(t+1) > Close(t) else 0
"""

from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

FEATURE_COLUMNS: List[str] = [
    "ret_1d",
    "ret_5d",
    "ret_20d",
    "sma_dist_5",
    "sma_dist_20",
    "sma_dist_50",
    "ema_dist_5",
    "ema_dist_20",
    "ema_dist_50",
    "rsi_14",
    "volatility_20d",
    "volume_ratio_20",
    "hl_range",
    "nifty_ret_1d",
    "nifty_ret_5d",
    "vix_level",
    "vix_change_5d",
    "delivery_pct",
    "delivery_ratio_20",
    "dist_52w_high",
]


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Computes Relative Strength Index (RSI) using standard exponential smoothing.
    Uses strictly past prices.
    """
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    # Wilder's smoothing via ewm (alpha = 1 / period)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    # Where loss is 0, RSI is 100; where gain is 0, RSI is 0
    rsi = rsi.fillna(50.0)
    return rsi


def build_features(
    df_equity: pd.DataFrame,
    df_nifty: Optional[pd.DataFrame] = None,
    df_vix: Optional[pd.DataFrame] = None,
    min_history: int = 50,
) -> pd.DataFrame:
    """
    Constructs leak-free quantitative features from equity price history,
    optionally aligning with NIFTY 50 and India VIX.

    Parameters:
        df_equity: DataFrame with Date, Open, High, Low, Close, Volume, DeliveryQty, DeliveryPercent
        df_nifty: Optional DataFrame with Date, Close
        df_vix: Optional DataFrame with Date, Close
        min_history: Minimum required rows before features are non-null

    Returns:
        DataFrame containing all engineered features and target column 'target_up'.
    """
    if df_equity.empty or len(df_equity) < 2:
        return pd.DataFrame()

    df = df_equity.copy().sort_values("Date").reset_index(drop=True)

    # Ensure numeric columns
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    vol = df["Volume"].replace(0, np.nan)

    # 1. Historical Returns (past only)
    df["ret_1d"] = close.pct_change(1)
    df["ret_5d"] = close.pct_change(5)
    df["ret_20d"] = close.pct_change(20)

    # 2. Moving Average Distances
    for period in [5, 20, 50]:
        sma = close.rolling(window=period, min_periods=period).mean()
        df[f"sma_dist_{period}"] = (close - sma) / sma

        ema = close.ewm(span=period, min_periods=period, adjust=False).mean()
        df[f"ema_dist_{period}"] = (close - ema) / ema

    # 3. RSI 14
    df["rsi_14"] = compute_rsi(close, period=14)

    # 4. 20-day Annualized Volatility
    df["volatility_20d"] = df["ret_1d"].rolling(window=20, min_periods=20).std() * np.sqrt(252)

    # 5. Volume Ratio
    sma_vol_20 = vol.rolling(window=20, min_periods=5).mean()
    df["volume_ratio_20"] = (vol / sma_vol_20).fillna(1.0)

    # 6. High-Low Normalized Range
    df["hl_range"] = (high - low) / close

    # 7. NIFTY 50 Context
    if df_nifty is not None and not df_nifty.empty:
        nifty = df_nifty[["Date", "Close"]].rename(columns={"Close": "nifty_close"}).sort_values("Date")
        nifty["nifty_ret_1d"] = nifty["nifty_close"].pct_change(1)
        nifty["nifty_ret_5d"] = nifty["nifty_close"].pct_change(5)
        df = df.merge(nifty[["Date", "nifty_ret_1d", "nifty_ret_5d"]], on="Date", how="left")
    else:
        df["nifty_ret_1d"] = 0.0
        df["nifty_ret_5d"] = 0.0

    df["nifty_ret_1d"] = df["nifty_ret_1d"].fillna(0.0)
    df["nifty_ret_5d"] = df["nifty_ret_5d"].fillna(0.0)

    # 8. India VIX Context
    if df_vix is not None and not df_vix.empty:
        vix = df_vix[["Date", "Close"]].rename(columns={"Close": "vix_level"}).sort_values("Date")
        vix["vix_change_5d"] = vix["vix_level"] - vix["vix_level"].shift(5)
        df = df.merge(vix[["Date", "vix_level", "vix_change_5d"]], on="Date", how="left")
    else:
        df["vix_level"] = 15.0  # Median long-term historical fallback if VIX missing
        df["vix_change_5d"] = 0.0

    df["vix_level"] = df["vix_level"].fillna(15.0)
    df["vix_change_5d"] = df["vix_change_5d"].fillna(0.0)

    # 9. Delivery percentage and 20-day delivery ratio
    if "DeliveryPercent" in df.columns and df["DeliveryPercent"].notna().any() and (df["DeliveryPercent"] > 0).any():
        df["delivery_pct"] = df["DeliveryPercent"] / 100.0
    elif "DeliveryQty" in df.columns and (df["DeliveryQty"] > 0).any():
        df["delivery_pct"] = (df["DeliveryQty"] / df["Volume"]).clip(lower=0.0, upper=1.0)
    else:
        # If no delivery data available, use a conservative constant baseline
        df["delivery_pct"] = 0.40

    df["delivery_pct"] = df["delivery_pct"].fillna(0.40)
    sma_deliv_20 = df["delivery_pct"].rolling(window=20, min_periods=5).mean()
    df["delivery_ratio_20"] = (df["delivery_pct"] / sma_deliv_20).fillna(1.0)

    # 10. Distance from 52-week High (up to 252 trading days)
    rolling_52w_high = high.rolling(window=252, min_periods=20).max()
    df["dist_52w_high"] = (close - rolling_52w_high) / rolling_52w_high

    # Target: y(t) = 1 if Close(t+1) > Close(t) else 0
    # Note: shift(-1) looks at tomorrow's close relative to today's close
    next_close = close.shift(-1)
    df["target_up"] = (next_close > close).astype(float)
    # The last row has no tomorrow close, so target is NaN
    df.loc[df.index[-1], "target_up"] = np.nan

    return df


def prepare_ml_dataset(
    df_features: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Separates feature matrix X and label y for supervised learning,
    dropping rows with NaN features or NaN target (warmup period + latest unlabelled row).
    Also returns the latest unlabelled row for forward inference.

    Returns:
        (X_trainable, y_trainable, latest_row_for_inference)
    """
    if df_features.empty:
        return pd.DataFrame(), pd.Series(dtype=float), pd.DataFrame()

    # The very last row is for today's live prediction (target is unknown)
    latest_inference_row = df_features.iloc[[-1]].copy()

    # Training data requires all feature columns and target to be non-null
    train_mask = df_features[FEATURE_COLUMNS].notna().all(axis=1) & df_features["target_up"].notna()
    clean_train_df = df_features[train_mask].copy()

    X = clean_train_df[FEATURE_COLUMNS]
    y = clean_train_df["target_up"].astype(int)

    return X, y, latest_inference_row


def make_features(
    df: pd.DataFrame,
    df_nifty: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Constructs leak-free feature dataset with target y using only current and past data.

    Features computed strictly with past data:
      - 1, 5, and 20-day returns (ret_1d, ret_5d, ret_20d)
      - SMA and EMA distance for 5, 20, and 50 days (sma_dist_5, sma_dist_20, sma_dist_50, ema_dist_5, ema_dist_20, ema_dist_50)
      - RSI 14 (rsi_14)
      - 20-day rolling annualized volatility (volatility_20d)
      - Volume ratio to 20-day average volume (volume_ratio_20)
      - High-low range (hl_range)
      - Optional NIFTY index return (nifty_ret_1d, nifty_ret_5d)

    Target:
      - y = 1 if next-day close is higher than today's close (Close(t+1) > Close(t)), else 0.

    Drops:
      - Warm-up NaN rows (e.g. 50-day window)
      - The last row that has no forward target.

    Returns:
      Clean DataFrame ready for modeling with feature columns and binary target column 'y'.
    """
    if df.empty or len(df) < 5:
        return pd.DataFrame()

    feat_df = build_features(df_equity=df, df_nifty=df_nifty)
    if feat_df.empty:
        return pd.DataFrame()

    req_cols = [
        "ret_1d", "ret_5d", "ret_20d",
        "sma_dist_5", "sma_dist_20", "sma_dist_50",
        "ema_dist_5", "ema_dist_20", "ema_dist_50",
        "rsi_14", "volatility_20d", "volume_ratio_20", "hl_range",
    ]
    if df_nifty is not None and not df_nifty.empty:
        req_cols.extend(["nifty_ret_1d", "nifty_ret_5d"])

    # Drop warm-up NaN rows and the last unlabelled row without target
    valid_mask = feat_df[req_cols].notna().all(axis=1) & feat_df["target_up"].notna()
    clean_df = feat_df[valid_mask].copy().reset_index(drop=True)
    clean_df["y"] = clean_df["target_up"].astype(int)

    return clean_df

