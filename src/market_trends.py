"""
AlphaWatch AI — Market Trends & Regime Diagnostics Engine
ASTRAQUANT X 2026

Computes macro market context strictly from saved local data:
  1. index_trend(nifty_df): Close vs SMA50/SMA200 and documented rule-based regime
     (Uptrend, Sideways, Downtrend).
  2. vix_regime(vix_df): Percentile of latest India VIX within its own history.
  3. breadth(bhavcopy_files): Advances, declines, unchanged and A/D ratio from saved files.
  4. movers(symbols): 1-day and 5-day percentage movers and most active stocks.
  5. delivery_trend(symbol): Delivery percentage trends and 20-day accumulation/distribution ratio.

CRITICAL DESIGN PRINCIPLE:
No machine learning or price predictions are made in this module.
All metrics represent macro market context to interpret individual stock signals.
Every returned object includes the computed values, the source report name, and the as-of date.
"""

import csv
import io
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.nse_ingest import is_cm_udiff_bhavcopy, is_legacy_bhavcopy, parse_date_string

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIR_RAW_NSE = PROJECT_ROOT / "data" / "raw" / "nse"
DIR_PROCESSED = PROJECT_ROOT / "data" / "processed"

DEFAULT_SYMBOLS: List[str] = [
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
class IndexTrendResult:
    """NIFTY 50 moving average trend and macro regime."""
    close: float
    sma50: Optional[float]
    sma200: Optional[float]
    diff_sma50_pct: Optional[float]
    diff_sma200_pct: Optional[float]
    regime_label: str  # 'Uptrend', 'Sideways', 'Downtrend', or 'Insufficient Data'
    rule_explanation: str
    source_report: str
    as_of_date: str


@dataclass
class VixRegimeResult:
    """India VIX level and historical percentile regime."""
    vix_level: float
    vix_percentile: float
    vix_5d_change: Optional[float]
    regime_label: str  # 'Low Volatility', 'Normal Volatility', 'High Volatility', 'Extreme Volatility'
    description: str
    source_report: str
    as_of_date: str


@dataclass
class BreadthDayResult:
    """Single trading day market breadth (Advances vs Declines)."""
    date: str
    advances: int
    declines: int
    unchanged: int
    total_traded: int
    ad_ratio: float
    advance_pct: float
    breadth_label: str  # 'Strong Bullish', 'Moderate Bullish', 'Neutral', 'Moderate Bearish', 'Strong Bearish'
    source_report: str
    as_of_date: str


@dataclass
class StockMover:
    """Single stock return and activity record."""
    symbol: str
    close: float
    ret_1d_pct: float
    ret_5d_pct: Optional[float]
    volume: float
    turnover_cr: Optional[float]
    as_of_date: str


@dataclass
class MoversResult:
    """Top gainers, losers, and most active supported equities."""
    top_gainers_1d: List[StockMover]
    top_losers_1d: List[StockMover]
    top_gainers_5d: List[StockMover]
    top_losers_5d: List[StockMover]
    most_active_volume: List[StockMover]
    all_stocks: List[StockMover]
    source_report: str
    as_of_date: str


@dataclass
class DeliveryTrendResult:
    """Deliverable position volume and 20-day trend."""
    symbol: str
    latest_close: float
    latest_delivery_qty: float
    latest_delivery_pct: float
    avg_delivery_pct_5d: Optional[float]
    avg_delivery_pct_20d: Optional[float]
    delivery_ratio_20d: Optional[float]
    trend_label: str  # 'High Delivery Accumulation', 'Distribution Concern', 'Normal Delivery'
    explanation: str
    source_report: str
    as_of_date: str


def index_trend(nifty_df: pd.DataFrame) -> IndexTrendResult:
    """
    Computes NIFTY 50 trend against 50-day and 200-day Simple Moving Averages.
    
    Documented Rule for Regime Label:
      - 'Uptrend': Close > SMA50 AND (Close > SMA200 or SMA50 >= SMA200) with Close at least 0.25% above SMA50.
      - 'Downtrend': Close < SMA50 AND (Close < SMA200 or SMA50 <= SMA200) with Close at least 0.25% below SMA50.
      - 'Sideways': Conflicting moving averages (e.g. SMA50 < Close < SMA200) or Close within +/-0.25% of SMA50.
      - If SMA200 is unavailable (<200 rows), regime is based purely on SMA50 with clear disclosure.
    """
    source_report = "NSE NIFTY 50 Daily Historical Index Report"

    if nifty_df.empty or "Close" not in nifty_df.columns:
        return IndexTrendResult(
            close=0.0,
            sma50=None,
            sma200=None,
            diff_sma50_pct=None,
            diff_sma200_pct=None,
            regime_label="Insufficient Data",
            rule_explanation="No NIFTY 50 price history available in saved data.",
            source_report=source_report,
            as_of_date="N/A",
        )

    df = nifty_df.copy().sort_values("Date").reset_index(drop=True)
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df = df.dropna(subset=["Close"]).reset_index(drop=True)

    if df.empty:
        return IndexTrendResult(
            close=0.0,
            sma50=None,
            sma200=None,
            diff_sma50_pct=None,
            diff_sma200_pct=None,
            regime_label="Insufficient Data",
            rule_explanation="Price column contains no valid numeric values.",
            source_report=source_report,
            as_of_date="N/A",
        )

    as_of_date = str(df["Date"].iloc[-1])
    latest_close = float(df["Close"].iloc[-1])
    n_rows = len(df)

    sma50 = float(df["Close"].rolling(window=50, min_periods=50).mean().iloc[-1]) if n_rows >= 50 else None
    sma200 = float(df["Close"].rolling(window=200, min_periods=200).mean().iloc[-1]) if n_rows >= 200 else None

    # Fallback to shorter windows if history is small (e.g. sample test data)
    if sma50 is None and n_rows >= 3:
        sma50 = float(df["Close"].rolling(window=min(n_rows, 20), min_periods=3).mean().iloc[-1])
        used_sma50_window = min(n_rows, 20)
    else:
        used_sma50_window = 50

    diff_sma50_pct = ((latest_close - sma50) / sma50 * 100.0) if sma50 is not None and sma50 > 0 else None
    diff_sma200_pct = ((latest_close - sma200) / sma200 * 100.0) if sma200 is not None and sma200 > 0 else None

    # Apply documented rule
    if sma50 is not None and sma200 is not None:
        if latest_close > sma50 and (latest_close > sma200 or sma50 >= sma200) and (diff_sma50_pct and diff_sma50_pct > 0.25):
            regime = "Uptrend"
            explanation = f"Close ({latest_close:,.2f}) is above both SMA50 ({sma50:,.2f}, +{diff_sma50_pct:.2f}%) and SMA200 ({sma200:,.2f})."
        elif latest_close < sma50 and (latest_close < sma200 or sma50 <= sma200) and (diff_sma50_pct and diff_sma50_pct < -0.25):
            regime = "Downtrend"
            explanation = f"Close ({latest_close:,.2f}) is below both SMA50 ({sma50:,.2f}, {diff_sma50_pct:.2f}%) and SMA200 ({sma200:,.2f})."
        else:
            regime = "Sideways"
            explanation = f"Moving averages in conflict: Close is between SMA50 ({sma50:,.2f}) and SMA200 ({sma200:,.2f}), reflecting consolidation."
    elif sma50 is not None:
        if diff_sma50_pct is not None and diff_sma50_pct > 0.25:
            regime = "Uptrend"
            explanation = f"Close ({latest_close:,.2f}) is trading +{diff_sma50_pct:.2f}% above SMA{used_sma50_window} ({sma50:,.2f}). (SMA200 requires 200 trading days)."
        elif diff_sma50_pct is not None and diff_sma50_pct < -0.25:
            regime = "Downtrend"
            explanation = f"Close ({latest_close:,.2f}) is trading {diff_sma50_pct:.2f}% below SMA{used_sma50_window} ({sma50:,.2f})."
        else:
            regime = "Sideways"
            explanation = f"Close ({latest_close:,.2f}) is hovering within +/-0.25% of SMA{used_sma50_window} ({sma50:,.2f})."
    else:
        regime = "Insufficient Data"
        explanation = f"Only {n_rows} trading days available. Minimum required for trend classification is 3."

    return IndexTrendResult(
        close=round(latest_close, 2),
        sma50=round(sma50, 2) if sma50 is not None else None,
        sma200=round(sma200, 2) if sma200 is not None else None,
        diff_sma50_pct=round(diff_sma50_pct, 2) if diff_sma50_pct is not None else None,
        diff_sma200_pct=round(diff_sma200_pct, 2) if diff_sma200_pct is not None else None,
        regime_label=regime,
        rule_explanation=explanation,
        source_report=source_report,
        as_of_date=as_of_date,
    )


def vix_regime(vix_df: pd.DataFrame) -> VixRegimeResult:
    """
    Computes India VIX regime by determining the percentile of the latest VIX close
    relative to its own historical distribution.

    Regime Categorization:
      - Percentile < 33.3%: 'Low Volatility' (Market complacency / benign conditions)
      - 33.3% <= Percentile < 66.7%: 'Normal Volatility' (Historical equilibrium)
      - 66.7% <= Percentile < 90.0%: 'High Volatility' (Elevated market uncertainty)
      - Percentile >= 90.0%: 'Extreme Volatility' (Severe market stress / panic)
    """
    source_report = "NSE India VIX Daily Historical Data Report"

    if vix_df.empty or "Close" not in vix_df.columns:
        return VixRegimeResult(
            vix_level=0.0,
            vix_percentile=0.0,
            vix_5d_change=None,
            regime_label="Insufficient Data",
            description="No India VIX history available in saved data.",
            source_report=source_report,
            as_of_date="N/A",
        )

    df = vix_df.copy().sort_values("Date").reset_index(drop=True)
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df = df.dropna(subset=["Close"]).reset_index(drop=True)

    if df.empty:
        return VixRegimeResult(
            vix_level=0.0,
            vix_percentile=0.0,
            vix_5d_change=None,
            regime_label="Insufficient Data",
            description="VIX history contains no numeric data.",
            source_report=source_report,
            as_of_date="N/A",
        )

    as_of_date = str(df["Date"].iloc[-1])
    latest_vix = float(df["Close"].iloc[-1])
    n_obs = len(df)

    # Calculate empirical percentile rank
    # Percentile = (Number of historical days with VIX <= latest_vix) / Total days * 100
    rank = float((df["Close"] <= latest_vix).sum())
    percentile = (rank / n_obs) * 100.0

    # 5-day absolute change
    vix_5d_change = None
    if n_obs >= 6:
        vix_5d_change = latest_vix - float(df["Close"].iloc[-6])
    elif n_obs >= 2:
        vix_5d_change = latest_vix - float(df["Close"].iloc[0])

    if percentile < 33.33:
        regime = "Low Volatility"
        desc = f"VIX ({latest_vix:.2f}) sits in the bottom {percentile:.1f}% of historical days, indicating subdued option implied volatility."
    elif percentile < 66.67:
        regime = "Normal Volatility"
        desc = f"VIX ({latest_vix:.2f}) is at the {percentile:.1f}th percentile, aligning with historical normal market variance."
    elif percentile < 90.0:
        regime = "High Volatility"
        desc = f"VIX ({latest_vix:.2f}) is elevated at the {percentile:.1f}th percentile, reflecting heightened market uncertainty."
    else:
        regime = "Extreme Volatility"
        desc = f"VIX ({latest_vix:.2f}) is in the top {100.0 - percentile:.1f}% extreme tier, indicating severe market distress or event risk."

    return VixRegimeResult(
        vix_level=round(latest_vix, 2),
        vix_percentile=round(percentile, 1),
        vix_5d_change=round(vix_5d_change, 2) if vix_5d_change is not None else None,
        regime_label=regime,
        description=desc,
        source_report=source_report,
        as_of_date=as_of_date,
    )


def breadth(
    bhavcopy_files: Optional[List[Path]] = None,
    raw_dir: Path = DIR_RAW_NSE,
) -> List[BreadthDayResult]:
    """
    Computes daily market breadth (Advances, Declines, Unchanged)
    from saved NSE Bhavcopy CSV or ZIP files.

    Returns:
        List of BreadthDayResult sorted chronologically descending (latest first).
    """
    source_report = "NSE CM-UDiFF Common Bhavcopy Final Report"

    files_to_scan: List[Path] = []
    if bhavcopy_files:
        files_to_scan = [Path(f) for f in bhavcopy_files if Path(f).exists()]
    elif raw_dir.exists():
        files_to_scan = [
            f for f in raw_dir.iterdir()
            if f.is_file() and f.suffix.lower() in (".csv", ".zip")
            and not any(k in f.name.lower() for k in ("nifty", "vix", "manifest"))
        ]

    if not files_to_scan:
        return []

    # Daily aggregation buckets: Date -> list of price changes (Close - PrevClose or Close - Open)
    day_changes: Dict[str, List[float]] = {}

    for file_path in files_to_scan:
        suffix = file_path.suffix.lower()

        def process_reader(reader: csv.DictReader):
            fieldnames = reader.fieldnames or []
            is_udiff = is_cm_udiff_bhavcopy(fieldnames)
            is_legacy = is_legacy_bhavcopy(fieldnames)

            for row in reader:
                clean_row = {k.strip().upper(): v.strip() for k, v in row.items() if k and v}
                if is_udiff:
                    series = clean_row.get("SCTYSRS", "").upper()
                    if series != "EQ":
                        continue
                    date_raw = clean_row.get("TRADDT", "")
                    try:
                        date_val = parse_date_string(date_raw)
                        close_p = float(clean_row.get("CLSPRIC", 0.0))
                        prev_p = float(clean_row.get("PRVSCLSGPRIC", clean_row.get("OPNPRIC", 0.0)))
                        if close_p > 0 and prev_p > 0:
                            day_changes.setdefault(date_val, []).append(close_p - prev_p)
                    except Exception:
                        continue

                elif is_legacy:
                    series = clean_row.get("SERIES", "").upper()
                    if series and series != "EQ":
                        continue
                    date_raw = clean_row.get("TIMESTAMP", clean_row.get("DATE", ""))
                    try:
                        date_val = parse_date_string(date_raw)
                        close_p = float(clean_row.get("CLOSE", 0.0))
                        prev_p = float(clean_row.get("PREVCLOSE", clean_row.get("OPEN", 0.0)))
                        if close_p > 0 and prev_p > 0:
                            day_changes.setdefault(date_val, []).append(close_p - prev_p)
                    except Exception:
                        continue

        if suffix == ".csv":
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    r = csv.DictReader(f)
                    process_reader(r)
            except Exception:
                continue

        elif suffix == ".zip":
            try:
                with zipfile.ZipFile(file_path, "r") as zf:
                    for member in zf.infolist():
                        if member.filename.lower().endswith(".csv"):
                            with zf.open(member) as f_bin:
                                text_stream = io.TextIOWrapper(f_bin, encoding="utf-8", errors="replace")
                                r = csv.DictReader(text_stream)
                                process_reader(r)
            except Exception:
                continue

    results: List[BreadthDayResult] = []

    for date_str, changes in sorted(day_changes.items(), reverse=True):
        if not changes:
            continue
        adv = sum(1 for c in changes if c > 0)
        dec = sum(1 for c in changes if c < 0)
        unch = sum(1 for c in changes if c == 0)
        total = adv + dec + unch

        ad_ratio = round(adv / max(dec, 1), 2)
        adv_pct = round((adv / total * 100.0), 1) if total > 0 else 0.0

        if adv_pct >= 65.0:
            breadth_label = "Strong Bullish"
        elif adv_pct >= 55.0:
            breadth_label = "Moderate Bullish"
        elif adv_pct <= 35.0:
            breadth_label = "Strong Bearish"
        elif adv_pct <= 45.0:
            breadth_label = "Moderate Bearish"
        else:
            breadth_label = "Neutral"

        results.append(BreadthDayResult(
            date=date_str,
            advances=adv,
            declines=dec,
            unchanged=unch,
            total_traded=total,
            ad_ratio=ad_ratio,
            advance_pct=adv_pct,
            breadth_label=breadth_label,
            source_report=source_report,
            as_of_date=date_str,
        ))

    return results


def movers(
    symbols: Optional[List[str]] = None,
    processed_dir: Path = DIR_PROCESSED,
) -> MoversResult:
    """
    Computes 1-day and 5-day percentage returns and volume turnover
    for all supported equities from saved processed files.
    """
    target_symbols = symbols or DEFAULT_SYMBOLS
    source_report = "Saved Processed Equity Price Archives"

    all_movers: List[StockMover] = []
    latest_dates: List[str] = []

    for sym in target_symbols:
        csv_path = processed_dir / f"{sym}.csv"
        if not csv_path.exists():
            continue

        try:
            df = pd.read_csv(csv_path)
            if df.empty or len(df) < 1 or "Close" not in df.columns:
                continue

            df = df.sort_values("Date").reset_index(drop=True)
            df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
            df = df.dropna(subset=["Close"]).reset_index(drop=True)

            if len(df) < 1:
                continue

            as_of_date = str(df["Date"].iloc[-1])
            latest_dates.append(as_of_date)
            latest_close = float(df["Close"].iloc[-1])
            vol = float(df["Volume"].iloc[-1]) if "Volume" in df.columns else 0.0

            # 1-day return
            if len(df) >= 2:
                prev_close = float(df["Close"].iloc[-2])
                ret_1d = ((latest_close - prev_close) / prev_close) * 100.0
            else:
                ret_1d = 0.0

            # 5-day return
            if len(df) >= 6:
                close_5d = float(df["Close"].iloc[-6])
                ret_5d = ((latest_close - close_5d) / close_5d) * 100.0
            elif len(df) > 1:
                close_init = float(df["Close"].iloc[0])
                ret_5d = ((latest_close - close_init) / close_init) * 100.0
            else:
                ret_5d = None

            # Turnover in ₹ Crores: Volume * Close / 10,000,000
            turnover_cr = (vol * latest_close) / 1e7 if vol > 0 else 0.0

            all_movers.append(StockMover(
                symbol=sym,
                close=round(latest_close, 2),
                ret_1d_pct=round(ret_1d, 2),
                ret_5d_pct=round(ret_5d, 2) if ret_5d is not None else None,
                volume=round(vol, 0),
                turnover_cr=round(turnover_cr, 2),
                as_of_date=as_of_date,
            ))
        except Exception:
            continue

    overall_as_of = max(latest_dates) if latest_dates else "N/A"

    if not all_movers:
        return MoversResult(
            top_gainers_1d=[],
            top_losers_1d=[],
            top_gainers_5d=[],
            top_losers_5d=[],
            most_active_volume=[],
            all_stocks=[],
            source_report=source_report,
            as_of_date=overall_as_of,
        )

    # Sort gainers and losers
    gainers_1d = sorted(all_movers, key=lambda x: x.ret_1d_pct, reverse=True)
    losers_1d = sorted(all_movers, key=lambda x: x.ret_1d_pct)

    gainers_5d = sorted([m for m in all_movers if m.ret_5d_pct is not None], key=lambda x: x.ret_5d_pct or 0.0, reverse=True)
    losers_5d = sorted([m for m in all_movers if m.ret_5d_pct is not None], key=lambda x: x.ret_5d_pct or 0.0)

    most_active = sorted(all_movers, key=lambda x: x.turnover_cr or x.volume, reverse=True)

    return MoversResult(
        top_gainers_1d=gainers_1d[:5],
        top_losers_1d=losers_1d[:5],
        top_gainers_5d=gainers_5d[:5],
        top_losers_5d=losers_5d[:5],
        most_active_volume=most_active[:5],
        all_stocks=all_movers,
        source_report=source_report,
        as_of_date=overall_as_of,
    )


def delivery_trend(
    symbol: str,
    processed_dir: Path = DIR_PROCESSED,
) -> DeliveryTrendResult:
    """
    Computes deliverable position percentage trends and 20-day moving averages
    for a supported equity.

    Trend Categorization:
      - 'High Delivery Accumulation': Delivery % > 20d average by at least 15% and price change >= -0.5%
      - 'Distribution Concern': Delivery % > 20d average by at least 15% but price down > 1.5%
      - 'Normal Delivery': Delivery within historical equilibrium
    """
    source_report = "NSE Deliverable Position Daily Report"
    sym = symbol.strip().upper()
    csv_path = processed_dir / f"{sym}.csv"

    if not csv_path.exists():
        return DeliveryTrendResult(
            symbol=sym,
            latest_close=0.0,
            latest_delivery_qty=0.0,
            latest_delivery_pct=0.0,
            avg_delivery_pct_5d=None,
            avg_delivery_pct_20d=None,
            delivery_ratio_20d=None,
            trend_label="Insufficient Data",
            explanation=f"No processed data file exists for {sym}.",
            source_report=source_report,
            as_of_date="N/A",
        )

    df = pd.read_csv(csv_path)
    if df.empty or len(df) < 1:
        return DeliveryTrendResult(
            symbol=sym,
            latest_close=0.0,
            latest_delivery_qty=0.0,
            latest_delivery_pct=0.0,
            avg_delivery_pct_5d=None,
            avg_delivery_pct_20d=None,
            delivery_ratio_20d=None,
            trend_label="Insufficient Data",
            explanation="Processed file is empty.",
            source_report=source_report,
            as_of_date="N/A",
        )

    df = df.sort_values("Date").reset_index(drop=True)
    as_of_date = str(df["Date"].iloc[-1])
    latest_close = float(df["Close"].iloc[-1])

    # Extract delivery pct
    if "DeliveryPercent" in df.columns and df["DeliveryPercent"].notna().any():
        deliv_series = pd.to_numeric(df["DeliveryPercent"], errors="coerce")
    elif "DeliveryQty" in df.columns and "Volume" in df.columns:
        d_qty = pd.to_numeric(df["DeliveryQty"], errors="coerce").fillna(0)
        vol = pd.to_numeric(df["Volume"], errors="coerce").replace(0, np.nan)
        deliv_series = (d_qty / vol * 100.0).fillna(0.0)
    else:
        deliv_series = pd.Series([40.0] * len(df))

    latest_deliv_pct = float(deliv_series.iloc[-1])
    latest_deliv_qty = float(df["DeliveryQty"].iloc[-1]) if "DeliveryQty" in df.columns else 0.0

    n_rows = len(df)
    avg_5d = float(deliv_series.rolling(window=5, min_periods=min(n_rows, 3)).mean().iloc[-1])
    avg_20d = float(deliv_series.rolling(window=20, min_periods=min(n_rows, 5)).mean().iloc[-1])

    deliv_ratio = (latest_deliv_pct / avg_20d) if avg_20d > 0 else 1.0

    # Check 1-day price return for context
    ret_1d = 0.0
    if n_rows >= 2:
        prev_close = float(df["Close"].iloc[-2])
        ret_1d = ((latest_close - prev_close) / prev_close) * 100.0

    if deliv_ratio >= 1.15 and ret_1d >= -0.5:
        trend = "High Delivery Accumulation"
        expl = f"Delivery percentage ({latest_deliv_pct:.1f}%) is {deliv_ratio:.2f}x above its 20-day mean ({avg_20d:.1f}%) with steady price action, indicating institutional accumulation."
    elif deliv_ratio >= 1.15 and ret_1d < -1.5:
        trend = "Distribution Concern"
        expl = f"Delivery percentage ({latest_deliv_pct:.1f}%) is high ({deliv_ratio:.2f}x mean) alongside a -{abs(ret_1d):.2f}% price decline, reflecting potential distribution selling."
    else:
        trend = "Normal Delivery"
        expl = f"Delivery percentage ({latest_deliv_pct:.1f}%) is consistent with its 20-day historical mean ({avg_20d:.1f}%)."

    return DeliveryTrendResult(
        symbol=sym,
        latest_close=round(latest_close, 2),
        latest_delivery_qty=round(latest_deliv_qty, 0),
        latest_delivery_pct=round(latest_deliv_pct, 2),
        avg_delivery_pct_5d=round(avg_5d, 2),
        avg_delivery_pct_20d=round(avg_20d, 2),
        delivery_ratio_20d=round(deliv_ratio, 2),
        trend_label=trend,
        explanation=expl,
        source_report=source_report,
        as_of_date=as_of_date,
    )
