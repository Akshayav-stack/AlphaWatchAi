"""
Unit Tests for src/market_trends.py (Macro Market Trends & Regime Diagnostics)
ASTRAQUANT X 2026

Features hand-checked tests on small deterministic series:
  1. index_trend: exact moving averages, percentage differentials, and regime rule labels
  2. vix_regime: exact empirical percentile ranking and regime categories
  3. breadth: hand-calculated advances, declines, and A/D ratios from saved files
  4. movers: hand-calculated 1-day and 5-day returns and ranking
  5. delivery_trend: 20-day delivery moving averages and accumulation/distribution classification
  6. Source report names and as-of dates verified across every function
"""

import io
from pathlib import Path
import pandas as pd
import pytest

import src.market_trends as mt


# -----------------------------------------------------------------------------
# 1. INDEX TREND: HAND-CHECKED TESTS
# -----------------------------------------------------------------------------

def test_index_trend_uptrend_hand_checked():
    """
    Hand-checked series of 5 days:
    Prices: [100.0, 102.0, 104.0, 106.0, 110.0]
    For n=5 (used window=5):
    SMA = (100 + 102 + 104 + 106 + 110) / 5 = 522 / 5 = 104.40
    Latest Close = 110.00
    diff_pct = (110.00 - 104.40) / 104.40 * 100 = 5.60 / 104.40 * 100 = +5.36%
    Expected Regime: 'Uptrend' (> +0.25%)
    """
    df = pd.DataFrame({
        "Date": ["2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05"],
        "Close": [100.0, 102.0, 104.0, 106.0, 110.0],
    })

    res = mt.index_trend(df)

    assert res.close == 110.0
    assert res.sma50 == 104.40
    assert res.diff_sma50_pct == 5.36
    assert res.regime_label == "Uptrend"
    assert "Uptrend" in res.regime_label
    assert res.as_of_date == "2026-10-05"
    assert "NIFTY 50" in res.source_report


def test_index_trend_downtrend_hand_checked():
    """
    Hand-checked series of 5 days:
    Prices: [110.0, 108.0, 106.0, 104.0, 95.0]
    SMA = (110 + 108 + 106 + 104 + 95) / 5 = 523 / 5 = 104.60
    Latest Close = 95.00
    diff_pct = (95.00 - 104.60) / 104.60 * 100 = -9.60 / 104.60 * 100 = -9.18%
    Expected Regime: 'Downtrend'
    """
    df = pd.DataFrame({
        "Date": ["2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05"],
        "Close": [110.0, 108.0, 106.0, 104.0, 95.0],
    })

    res = mt.index_trend(df)

    assert res.close == 95.0
    assert res.sma50 == 104.60
    assert res.diff_sma50_pct == -9.18
    assert res.regime_label == "Downtrend"
    assert res.as_of_date == "2026-10-05"


def test_index_trend_insufficient_data():
    """Verifies empty and insufficient data handling."""
    empty_df = pd.DataFrame()
    res = mt.index_trend(empty_df)

    assert res.regime_label == "Insufficient Data"
    assert res.as_of_date == "N/A"
    assert res.source_report != ""


# -----------------------------------------------------------------------------
# 2. INDIA VIX REGIME: HAND-CHECKED PERCENTILE TESTS
# -----------------------------------------------------------------------------

def test_vix_regime_hand_checked():
    """
    Hand-checked series of 10 observations:
    VIX values: [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0]
    
    Case A: Latest is 11.0
    Count <= 11.0 is 2. Percentile = 2/10 * 100 = 20.0%
    Expected Regime: 'Low Volatility' (< 33.33%)

    Case B: Latest is 15.0
    Count <= 15.0 is 6. Percentile = 6/10 * 100 = 60.0%
    Expected Regime: 'Normal Volatility' (33.33% to 66.67%)
    """
    # Case A: Low Volatility
    dates = [f"2026-10-{i:02d}" for i in range(1, 11)]
    closes_low = [19.0, 18.0, 17.0, 16.0, 15.0, 14.0, 13.0, 12.0, 10.0, 11.0]
    df_low = pd.DataFrame({"Date": dates, "Close": closes_low})

    res_low = mt.vix_regime(df_low)
    assert res_low.vix_level == 11.0
    assert res_low.vix_percentile == 20.0
    assert res_low.regime_label == "Low Volatility"
    assert res_low.as_of_date == "2026-10-10"
    assert "India VIX" in res_low.source_report

    # Case B: Normal Volatility
    closes_norm = [10.0, 11.0, 12.0, 13.0, 14.0, 16.0, 17.0, 18.0, 19.0, 15.0]
    df_norm = pd.DataFrame({"Date": dates, "Close": closes_norm})

    res_norm = mt.vix_regime(df_norm)
    assert res_norm.vix_level == 15.0
    # Values <= 15.0: 10, 11, 12, 13, 14, 15 = 6 observations -> 60.0%
    assert res_norm.vix_percentile == 60.0
    assert res_norm.regime_label == "Normal Volatility"


# -----------------------------------------------------------------------------
# 3. MARKET BREADTH: HAND-CHECKED ADVANCES & DECLINES
# -----------------------------------------------------------------------------

def test_breadth_hand_checked(tmp_path: Path):
    """
    Creates a tiny test bhavcopy CSV with 4 stocks:
      - Stock 1: PrevClose=100, Close=105 -> Advance
      - Stock 2: PrevClose=100, Close=95  -> Decline
      - Stock 3: PrevClose=100, Close=110 -> Advance
      - Stock 4: PrevClose=100, Close=100 -> Unchanged
    
    Hand-checked:
      Advances: 2
      Declines: 1
      Unchanged: 1
      Total: 4
      AD Ratio = 2 / 1 = 2.0
      Advance % = 2 / 4 * 100 = 50.0% -> 'Neutral'
    """
    bhav_file = tmp_path / "BhavCopy_TEST_20261030.csv"
    csv_content = (
        "TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,OpnPric,HghPric,LwPric,ClsPric,LastPric,PrvsClsgPric,TtlTradgVol\n"
        "2026-10-30,2026-10-30,CM,NSE,STK,1,INE001,STOCK1,EQ,100,106,99,105,105,100,1000\n"
        "2026-10-30,2026-10-30,CM,NSE,STK,2,INE002,STOCK2,EQ,100,101,94,95,95,100,1000\n"
        "2026-10-30,2026-10-30,CM,NSE,STK,3,INE003,STOCK3,EQ,100,111,99,110,110,100,1000\n"
        "2026-10-30,2026-10-30,CM,NSE,STK,4,INE004,STOCK4,EQ,100,101,99,100,100,100,1000\n"
        "2026-10-30,2026-10-30,CM,NSE,STK,5,INE005,IGNORED,BE,100,105,99,105,105,100,1000\n"  # Series BE ignored
    )
    bhav_file.write_text(csv_content, encoding="utf-8")

    res_list = mt.breadth(bhavcopy_files=[bhav_file])

    assert len(res_list) == 1
    day_res = res_list[0]

    assert day_res.date == "2026-10-30"
    assert day_res.advances == 2
    assert day_res.declines == 1
    assert day_res.unchanged == 1
    assert day_res.total_traded == 4
    assert day_res.ad_ratio == 2.0
    assert day_res.advance_pct == 50.0
    assert day_res.breadth_label == "Neutral"
    assert day_res.as_of_date == "2026-10-30"
    assert "Common Bhavcopy" in day_res.source_report


# -----------------------------------------------------------------------------
# 4. MOVERS: HAND-CHECKED 1D & 5D RETURNS
# -----------------------------------------------------------------------------

def test_movers_hand_checked(tmp_path: Path):
    """
    Creates small processed CSVs for 3 stocks:
      - Stock A: Close = [100.0, 110.0] -> 1d return = +10.0%
      - Stock B: Close = [100.0, 95.0]  -> 1d return = -5.0%
      - Stock C: Close = [100.0, 102.0] -> 1d return = +2.0%
    """
    (tmp_path / "A.csv").write_text("Date,Open,High,Low,Close,Volume\n2026-10-29,100,101,99,100,1000\n2026-10-30,100,111,99,110,2000\n", encoding="utf-8")
    (tmp_path / "B.csv").write_text("Date,Open,High,Low,Close,Volume\n2026-10-29,100,101,99,100,1000\n2026-10-30,100,101,94,95,1500\n", encoding="utf-8")
    (tmp_path / "C.csv").write_text("Date,Open,High,Low,Close,Volume\n2026-10-29,100,101,99,100,1000\n2026-10-30,100,103,99,102,1200\n", encoding="utf-8")

    res = mt.movers(symbols=["A", "B", "C"], processed_dir=tmp_path)

    assert len(res.all_stocks) == 3
    assert res.top_gainers_1d[0].symbol == "A"
    assert res.top_gainers_1d[0].ret_1d_pct == 10.0

    assert res.top_losers_1d[0].symbol == "B"
    assert res.top_losers_1d[0].ret_1d_pct == -5.0

    assert res.as_of_date == "2026-10-30"
    assert res.source_report != ""


# -----------------------------------------------------------------------------
# 5. DELIVERY TREND: HAND-CHECKED ACCUMULATION / DISTRIBUTION
# -----------------------------------------------------------------------------

def test_delivery_trend_hand_checked(tmp_path: Path):
    """
    Hand-checked 20-day delivery baseline of 30.0%.
    On day 21, delivery rises to 45.0% with positive price movement:
    Ratio = 45.0 / 30.0 = 1.50x (> 1.15x) -> 'High Delivery Accumulation'.
    """
    rows = ["Date,Open,High,Low,Close,Volume,DeliveryQty,DeliveryPercent"]
    for i in range(1, 21):
        rows.append(f"2026-10-{i:02d},100,102,98,100,10000,3000,30.0")
    # Day 21: High delivery (45.0%) with price up to 102 (+2.0%)
    rows.append("2026-10-21,100,103,99,102,10000,4500,45.0")

    (tmp_path / "TESTSYM.csv").write_text("\n".join(rows), encoding="utf-8")

    res = mt.delivery_trend(symbol="TESTSYM", processed_dir=tmp_path)

    assert res.symbol == "TESTSYM"
    assert res.latest_delivery_pct == 45.0
    # Ratio = 45.0 / approx 30.0
    assert res.delivery_ratio_20d is not None and res.delivery_ratio_20d >= 1.40
    assert res.trend_label == "High Delivery Accumulation"
    assert res.as_of_date == "2026-10-21"
    assert "Deliverable Position" in res.source_report
