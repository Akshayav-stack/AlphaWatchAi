"""
AlphaWatch AI — Explainable AI (XAI) Rule & Threshold Configuration
ASTRAQUANT X 2026

Strict Empirical Guidelines:
  - All factor rules and risk alert thresholds are documented and transparent.
  - A factor is eligible ONLY if its quantitative rule fires on real feature values
    AND the matching feature's local SHAP contribution shares the exact same directional sign.
  - Zero fabricated data: all values are computed directly from model inputs and outputs.
"""

from typing import Any, Callable, Dict, List, Optional

# Supported equities universe
SUPPORTED_SYMBOLS: List[str] = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "SBIN", "BHARTIARTL", "ITC", "LT", "HINDUNILVR",
    "BAJFINANCE", "MARUTI",
]

# Benchmark & Risk Baseline Parameters
RBI_REPO_RATE_ANNUAL: float = 0.065
MAX_CONCENTRATION_THRESHOLD_PCT: float = 30.0

# Feature Metadata & Plain-English Labels
FEATURE_METADATA: Dict[str, Dict[str, Any]] = {
    "ret_1d": {
        "label": "1-Day Price Return",
        "unit": "%",
        "description": "Percentage change in closing price over the last trading session.",
    },
    "ret_5d": {
        "label": "5-Day Short-Term Momentum",
        "unit": "%",
        "description": "5-day rolling return indicating short-term momentum.",
    },
    "ret_20d": {
        "label": "20-Day Medium-Term Momentum",
        "unit": "%",
        "description": "20-day rolling return representing monthly trend direction.",
    },
    "sma_dist_5": {
        "label": "Distance to 5-Day SMA",
        "unit": "%",
        "description": "Relative percentage spread between current price and 5-day moving average.",
    },
    "sma_dist_20": {
        "label": "Distance to 20-Day SMA",
        "unit": "%",
        "description": "Relative percentage spread between current price and 20-day moving average.",
    },
    "sma_dist_50": {
        "label": "Distance to 50-Day SMA",
        "unit": "%",
        "description": "Relative percentage spread between current price and 50-day medium-term trendline.",
    },
    "ema_dist_5": {
        "label": "Distance to 5-Day EMA",
        "unit": "%",
        "description": "Distance to 5-day exponential moving average.",
    },
    "ema_dist_20": {
        "label": "Distance to 20-Day EMA",
        "unit": "%",
        "description": "Distance to 20-day exponential moving average.",
    },
    "ema_dist_50": {
        "label": "Distance to 50-Day EMA",
        "unit": "%",
        "description": "Distance to 50-day exponential moving average.",
    },
    "rsi_14": {
        "label": "14-Day Relative Strength Index (RSI)",
        "unit": "index",
        "description": "Wilder's RSI measuring speed and change of price movements (0-100).",
    },
    "volatility_20d": {
        "label": "20-Day Annualized Volatility",
        "unit": "%",
        "description": "Rolling 20-day annualized historical standard deviation of log returns.",
    },
    "volume_ratio_20": {
        "label": "20-Day Volume Ratio",
        "unit": "x",
        "description": "Current volume divided by 20-day average volume.",
    },
    "hl_range": {
        "label": "Intraday Price Range",
        "unit": "%",
        "description": "Intraday spread between High and Low as a fraction of Close.",
    },
    "nifty_ret_1d": {
        "label": "NIFTY 50 1-Day Return",
        "unit": "%",
        "description": "Benchmark index performance over the last session.",
    },
    "nifty_ret_5d": {
        "label": "NIFTY 50 5-Day Return",
        "unit": "%",
        "description": "Benchmark index 5-day rolling return.",
    },
    "vix_level": {
        "label": "India VIX Volatility Index",
        "unit": "pts",
        "description": "NSE India Volatility Index measuring near-term market risk expectation.",
    },
    "vix_change_5d": {
        "label": "5-Day India VIX Shift",
        "unit": "%",
        "description": "5-day percentage change in the India VIX index.",
    },
    "delivery_pct": {
        "label": "Delivery Volume Percentage",
        "unit": "%",
        "description": "Proportion of total traded shares settled via actual demat delivery.",
    },
    "delivery_ratio_20": {
        "label": "20-Day Delivery Ratio",
        "unit": "x",
        "description": "Current delivery volume compared to 20-day average delivery volume.",
    },
    "dist_52w_high": {
        "label": "Distance from 52-Week High",
        "unit": "%",
        "description": "Percentage drawdown from the rolling 252-day peak closing price.",
    },
}

# ---------------------------------------------------------------------------
# FACTOR RULES TABLE (Positive & Negative)
# A factor is included if condition(feature_value, features_dict) is True
# AND sign(shap_contribution) matches expected sign (+ for positive, - for negative).
# ---------------------------------------------------------------------------

FACTOR_RULES: List[Dict[str, Any]] = [
    # 1. 5-Day Return
    {
        "id": "ret_5d_pos",
        "feature": "ret_5d",
        "direction": "positive",
        "threshold_desc": "5-day return > 0.0%",
        "condition": lambda val, row: val > 0.0,
        "reason_template": "5-day short-term momentum is positive at +{val_disp}.",
    },
    {
        "id": "ret_5d_neg",
        "feature": "ret_5d",
        "direction": "negative",
        "threshold_desc": "5-day return < 0.0%",
        "condition": lambda val, row: val < 0.0,
        "reason_template": "5-day short-term momentum declined by {val_disp}.",
    },
    # 2. 20-Day Return
    {
        "id": "ret_20d_pos",
        "feature": "ret_20d",
        "direction": "positive",
        "threshold_desc": "20-day return > 0.0%",
        "condition": lambda val, row: val > 0.0,
        "reason_template": "20-day medium-term momentum gained +{val_disp}.",
    },
    {
        "id": "ret_20d_neg",
        "feature": "ret_20d",
        "direction": "negative",
        "threshold_desc": "20-day return < 0.0%",
        "condition": lambda val, row: val < 0.0,
        "reason_template": "20-day medium-term trend declined by {val_disp}.",
    },
    # 3. Price Above / Below SMA 20
    {
        "id": "sma_20_above",
        "feature": "sma_dist_20",
        "direction": "positive",
        "threshold_desc": "Price above 20-day SMA (spread > 0.0%)",
        "condition": lambda val, row: val > 0.0,
        "reason_template": "Price trades +{val_disp} above its 20-day simple moving average.",
    },
    {
        "id": "sma_20_below",
        "feature": "sma_dist_20",
        "direction": "negative",
        "threshold_desc": "Price below 20-day SMA (spread < 0.0%)",
        "condition": lambda val, row: val < 0.0,
        "reason_template": "Price trades {val_disp} below its 20-day simple moving average.",
    },
    # 4. Price Above / Below SMA 50
    {
        "id": "sma_50_above",
        "feature": "sma_dist_50",
        "direction": "positive",
        "threshold_desc": "Price above 50-day SMA (spread > 0.0%)",
        "condition": lambda val, row: val > 0.0,
        "reason_template": "Price trades +{val_disp} above its 50-day primary trendline.",
    },
    {
        "id": "sma_50_below",
        "feature": "sma_dist_50",
        "direction": "negative",
        "threshold_desc": "Price below 50-day SMA (spread < 0.0%)",
        "condition": lambda val, row: val < 0.0,
        "reason_template": "Price trades {val_disp} below its 50-day primary trendline.",
    },
    # 5. Bullish / Bearish SMA Crossover state
    {
        "id": "sma_crossover_bull",
        "feature": "sma_dist_20",
        "direction": "positive",
        "threshold_desc": "SMA20 above SMA50 (Bullish moving average alignment)",
        "condition": lambda val, row: row.get("sma_dist_20", 0.0) > row.get("sma_dist_50", 0.0),
        "reason_template": "20-day SMA is positioned above the 50-day SMA, indicating bullish trend alignment.",
    },
    {
        "id": "sma_crossover_bear",
        "feature": "sma_dist_20",
        "direction": "negative",
        "threshold_desc": "SMA20 below SMA50 (Bearish moving average alignment)",
        "condition": lambda val, row: row.get("sma_dist_20", 0.0) < row.get("sma_dist_50", 0.0),
        "reason_template": "20-day SMA is positioned below the 50-day SMA, indicating bearish trend alignment.",
    },
    # 6. Volume Ratio
    {
        "id": "volume_rising",
        "feature": "volume_ratio_20",
        "direction": "positive",
        "threshold_desc": "20-day volume ratio > 1.2x (Rising trading volume)",
        "condition": lambda val, row: val > 1.20,
        "reason_template": "Trading volume is elevated at {val_disp} of its 20-day average, signaling institutional participation.",
    },
    {
        "id": "volume_low",
        "feature": "volume_ratio_20",
        "direction": "negative",
        "threshold_desc": "20-day volume ratio < 0.5x (Unusually low volume)",
        "condition": lambda val, row: val < 0.50,
        "reason_template": "Trading volume is subdued at {val_disp} of its 20-day average, indicating weak liquidity.",
    },
    # 7. Relative Strength Index (RSI)
    {
        "id": "rsi_momentum_pos",
        "feature": "rsi_14",
        "direction": "positive",
        "threshold_desc": "RSI between 50 and 70 (Constructive bullish momentum)",
        "condition": lambda val, row: 50.0 <= val <= 70.0,
        "reason_template": "14-day RSI is constructive at {val_disp}, demonstrating healthy bullish momentum.",
    },
    {
        "id": "rsi_oversold_rebound",
        "feature": "rsi_14",
        "direction": "positive",
        "threshold_desc": "RSI < 30 (Oversold condition with mean-reversion upside)",
        "condition": lambda val, row: val < 30.0,
        "reason_template": "14-day RSI is oversold at {val_disp}, setting up statistical mean-reversion potential.",
    },
    {
        "id": "rsi_overbought_exhaustion",
        "feature": "rsi_14",
        "direction": "negative",
        "threshold_desc": "RSI > 70 (Overbought condition with pullback risk)",
        "condition": lambda val, row: val > 70.0,
        "reason_template": "14-day RSI is overbought at {val_disp}, presenting elevated risk of technical exhaustion.",
    },
    {
        "id": "rsi_bearish_sub50",
        "feature": "rsi_14",
        "direction": "negative",
        "threshold_desc": "RSI < 50 (Bearish momentum below neutral centerline)",
        "condition": lambda val, row: 30.0 <= val < 50.0,
        "reason_template": "14-day RSI is sub-neutral at {val_disp}, reflecting sluggish demand.",
    },
    # 8. 20-Day Annualized Volatility
    {
        "id": "vol_calm_pos",
        "feature": "volatility_20d",
        "direction": "positive",
        "threshold_desc": "20-day annualized volatility <= 20.0% (Stable price distribution)",
        "condition": lambda val, row: val <= 0.20,
        "reason_template": "20-day annualized volatility is low at {val_disp}, indicating predictable price action.",
    },
    {
        "id": "vol_elevated_neg",
        "feature": "volatility_20d",
        "direction": "negative",
        "threshold_desc": "20-day annualized volatility > 30.0% (Elevated variance risk)",
        "condition": lambda val, row: val > 0.30,
        "reason_template": "20-day annualized volatility is high at {val_disp}, increasing variance and downside tail risk.",
    },
    # 9. India VIX Regime
    {
        "id": "vix_benign_pos",
        "feature": "vix_level",
        "direction": "positive",
        "threshold_desc": "India VIX < 15.0 pts (Benign macro volatility environment)",
        "condition": lambda val, row: val < 15.0,
        "reason_template": "India VIX is low at {val_disp}, supporting a stable broad market backdrop.",
    },
    {
        "id": "vix_elevated_neg",
        "feature": "vix_level",
        "direction": "negative",
        "threshold_desc": "India VIX > 18.0 pts (Elevated macro uncertainty)",
        "condition": lambda val, row: val > 18.0,
        "reason_template": "India VIX is elevated at {val_disp}, signaling market-wide turbulence.",
    },
    # 10. Delivery Volume
    {
        "id": "delivery_ratio_pos",
        "feature": "delivery_ratio_20",
        "direction": "positive",
        "threshold_desc": "20-day delivery ratio > 1.1x (Accumulation)",
        "condition": lambda val, row: val > 1.10,
        "reason_template": "Delivery accumulation ratio is strong at {val_disp}, showing genuine investor backing.",
    },
    {
        "id": "delivery_ratio_neg",
        "feature": "delivery_ratio_20",
        "direction": "negative",
        "threshold_desc": "20-day delivery ratio < 0.8x (Speculative churn)",
        "condition": lambda val, row: val < 0.80,
        "reason_template": "Delivery accumulation ratio is low at {val_disp}, reflecting intraday speculative turnover.",
    },
    # 11. Distance from 52-Week High
    {
        "id": "dist_52w_high_near",
        "feature": "dist_52w_high",
        "direction": "positive",
        "threshold_desc": "Within 5% of 52-week high (Strength/Breakout)",
        "condition": lambda val, row: abs(val) < 0.05,
        "reason_template": "Stock trades within {val_disp} of its 52-week peak, exhibiting leadership strength.",
    },
    {
        "id": "dist_52w_high_deep_drawdown",
        "feature": "dist_52w_high",
        "direction": "negative",
        "threshold_desc": "> 15% drawdown from 52-week high",
        "condition": lambda val, row: abs(val) > 0.15,
        "reason_template": "Stock has drawn down {val_disp} from its 52-week peak, under sustained selling pressure.",
    },
]

# ---------------------------------------------------------------------------
# RISK ALERT THRESHOLDS
# Computed strictly against verified portfolio and equity market inputs.
# ---------------------------------------------------------------------------

RISK_ALERT_CONFIG: Dict[str, Dict[str, Any]] = {
    "high_volatility": {
        "threshold": 0.30,  # 30% annualized volatility
        "title": "Elevated Historical Volatility",
        "message": "20-day annualized volatility is {val:.1f}%, exceeding the risk threshold of {thresh:.1f}%.",
    },
    "negative_momentum": {
        "threshold": 0.0,  # 20d return < 0
        "title": "Negative Medium-Term Momentum",
        "message": "20-day price momentum is negative at {val:+.2f}%, indicating a downward medium-term trend.",
    },
    "low_volume": {
        "threshold": 0.50,  # Volume ratio < 0.5x
        "title": "Unusually Low Trading Volume",
        "message": "Trading volume is {val:.2f}x of its 20-day moving average, below the 0.50x threshold, signaling low liquidity.",
    },
    "weak_probability": {
        "margin": 0.05,  # within 5% of 50%
        "title": "Equivocal Statistical Edge",
        "message": "Calibrated probability is {val:.1f}%, close to 50% equilibrium. Directional conviction is limited.",
    },
    "high_exposure": {
        "portfolio_threshold_pct": 30.0,
        "title": "Concentration Risk Alert",
        "message": "This stock represents {val:.1f}% of your portfolio, exceeding the 30.0% single-stock concentration ceiling.",
    },
    "stock_drawdown": {
        "threshold": 0.15,  # > 15% drawdown
        "title": "Deep Drawdown from 52-Week Peak",
        "message": "Stock is currently {val:.1f}% below its 52-week high, exceeding the 15.0% drawdown watch limit.",
    },
}
