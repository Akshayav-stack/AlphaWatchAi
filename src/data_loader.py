"""
AlphaWatch AI — Unified Offline Data Access Layer
ASTRAQUANT X 2026

Reads ONLY local saved CSV files from data/processed/.
Validates:
  1. Chronological sorting
  2. Duplicate removal
  3. Positive price sanity checks (Open, High, Low, Close > 0, High >= Low)
  4. Trading day calendar gaps & market holidays
  5. Corporate action jump detection (>20% move flagged for review,
     reflecting unadjusted split/bonus bhavcopy prices)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIR_PROCESSED = PROJECT_ROOT / "data" / "processed"


@dataclass
class ValidationReport:
    """Diagnostic report for loaded price series."""
    symbol: str
    total_rows: int
    start_date: str
    end_date: str
    is_sorted: bool
    duplicate_dates_count: int
    non_positive_rows_count: int
    high_low_violations_count: int
    calendar_gaps: List[Tuple[str, str, int]] = field(default_factory=list)
    corporate_action_jumps: List[Tuple[str, float, float, float]] = field(default_factory=list)


def validate_and_clean_dataframe(
    df: pd.DataFrame,
    symbol: str,
    corporate_action_threshold: float = 0.20,
) -> Tuple[pd.DataFrame, ValidationReport]:
    """
    Validates, repairs, and enriches a raw price dataframe with sanity flags.

    Parameters:
        df: Input DataFrame with standard columns (Date, Open, High, Low, Close, Volume)
        symbol: Ticker symbol
        corporate_action_threshold: Fractional jump threshold (default 0.20 = 20%)

    Returns:
        (cleaned_df, validation_report)
    """
    if df.empty:
        report = ValidationReport(
            symbol=symbol,
            total_rows=0,
            start_date="N/A",
            end_date="N/A",
            is_sorted=True,
            duplicate_dates_count=0,
            non_positive_rows_count=0,
            high_low_violations_count=0,
        )
        return df, report

    clean = df.copy()

    # 1. Standardize dates & check sorting
    clean["Date"] = pd.to_datetime(clean["Date"]).dt.strftime("%Y-%m-%d")
    is_initially_sorted = clean["Date"].is_monotonic_increasing

    # 2. Duplicate detection
    dup_count = int(clean.duplicated(subset=["Date"]).sum())
    if dup_count > 0:
        clean = clean.drop_duplicates(subset=["Date"], keep="last")

    # Sort strictly chronologically
    clean = clean.sort_values(by="Date").reset_index(drop=True)

    # 3. Non-positive price and High/Low sanity checks
    numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in numeric_cols:
        if col in clean.columns:
            clean[col] = pd.to_numeric(clean[col], errors="coerce")

    non_pos_mask = (clean["Open"] <= 0) | (clean["High"] <= 0) | (clean["Low"] <= 0) | (clean["Close"] <= 0)
    non_pos_count = int(non_pos_mask.sum())

    hl_violation_mask = clean["High"] < clean["Low"]
    hl_violations_count = int(hl_violation_mask.sum())

    # Filter out corrupted rows
    valid_mask = (~non_pos_mask) & (~hl_violation_mask)
    clean = clean[valid_mask].reset_index(drop=True)

    # 4. Calendar gaps check (>5 calendar days between consecutive trading sessions)
    calendar_gaps: List[Tuple[str, str, int]] = []
    dates = pd.to_datetime(clean["Date"])
    if len(dates) > 1:
        diffs = (dates.iloc[1:].values - dates.iloc[:-1].values) / np.timedelta64(1, "D")
        for i, gap_days in enumerate(diffs):
            if gap_days > 5:
                d1 = clean["Date"].iloc[i]
                d2 = clean["Date"].iloc[i + 1]
                calendar_gaps.append((d1, d2, int(gap_days)))

    # 5. Corporate Action Jump Detection (> 20% move in Close)
    # Bhavcopy figures are unadjusted for bonus issues, splits, or capital restructuring.
    clean["prev_close"] = clean["Close"].shift(1)
    clean["pct_change"] = (clean["Close"] - clean["prev_close"]) / clean["prev_close"]
    
    jump_mask = clean["pct_change"].abs() > corporate_action_threshold
    clean["corporate_action_flag"] = jump_mask.fillna(False)

    corporate_action_jumps: List[Tuple[str, float, float, float]] = []
    jump_rows = clean[jump_mask]
    for _, row in jump_rows.iterrows():
        corporate_action_jumps.append((
            row["Date"],
            float(row["prev_close"]),
            float(row["Close"]),
            float(row["pct_change"]),
        ))

    clean = clean.drop(columns=["prev_close", "pct_change"])

    report = ValidationReport(
        symbol=symbol,
        total_rows=len(clean),
        start_date=clean["Date"].iloc[0] if len(clean) > 0 else "N/A",
        end_date=clean["Date"].iloc[-1] if len(clean) > 0 else "N/A",
        is_sorted=is_initially_sorted,
        duplicate_dates_count=dup_count,
        non_positive_rows_count=non_pos_count,
        high_low_violations_count=hl_violations_count,
        calendar_gaps=calendar_gaps,
        corporate_action_jumps=corporate_action_jumps,
    )

    return clean, report


def load_prices(
    symbol: str,
    processed_dir: Path = DIR_PROCESSED,
) -> Tuple[pd.DataFrame, ValidationReport]:
    """
    Loads price history for an equity symbol from saved local files.
    Never initiates network requests.

    Returns:
        (df, validation_report)
    """
    clean_sym = symbol.strip().upper()
    # Strip any directory path components to prevent path traversal
    clean_sym = Path(clean_sym).name.replace("/", "").replace("\\", "").replace("..", "")
    processed_dir_resolved = processed_dir.resolve()
    csv_file = (processed_dir / f"{clean_sym}.csv").resolve()

    # Enforce strict path containment: target must be inside processed_dir
    try:
        csv_file.relative_to(processed_dir_resolved)
    except ValueError:
        clean_sym = "INVALID"
        csv_file = processed_dir_resolved / "NONEXISTENT.csv"

    if not csv_file.exists():
        empty_df = pd.DataFrame(columns=[
            "Date", "Open", "High", "Low", "Close", "Volume",
            "DeliveryQty", "DeliveryPercent", "corporate_action_flag",
        ])
        report = ValidationReport(
            symbol=clean_sym,
            total_rows=0,
            start_date="N/A",
            end_date="N/A",
            is_sorted=True,
            duplicate_dates_count=0,
            non_positive_rows_count=0,
            high_low_violations_count=0,
        )
        return empty_df, report

    df = pd.read_csv(csv_file)
    return validate_and_clean_dataframe(df, clean_sym)


def load_nifty50(processed_dir: Path = DIR_PROCESSED) -> pd.DataFrame:
    """Loads cleaned NIFTY 50 historical index data."""
    csv_file = processed_dir / "NIFTY50.csv"
    if not csv_file.exists():
        return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    
    df = pd.read_csv(csv_file)
    clean_df, _ = validate_and_clean_dataframe(df, "NIFTY50", corporate_action_threshold=0.15)
    return clean_df


def load_vix(processed_dir: Path = DIR_PROCESSED) -> pd.DataFrame:
    """Loads cleaned India VIX historical volatility index data."""
    csv_file = processed_dir / "INDIAVIX.csv"
    if not csv_file.exists():
        return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close"])
    
    df = pd.read_csv(csv_file)
    clean_df, _ = validate_and_clean_dataframe(df, "INDIAVIX", corporate_action_threshold=0.50)
    return clean_df


def download_prices(
    symbols: List[str],
    start: Optional[str] = None,
    end: Optional[str] = None,
    out_dir: Optional[Path] = None,
    processed_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Downloads historical price data using yfinance:
      - Automatically adds .NS suffix for Indian NSE equities (e.g., RELIANCE.NS)
      - Maps NIFTY 50 to ^NSEI and India VIX to ^INDIAVIX
    Saves one CSV per symbol (Date, Open, High, Low, Close, Adj Close, Volume) to data/raw.
    Writes/appends to data/processed/data_manifest.csv with:
      source, download date, row count, date range, adjustment status.

    If a download fails or yfinance is not available, prints a clear message
    and keeps using the existing local CSV without disrupting the offline app.
    Never labels old data as live; exposes the as-of date.
    """
    raw_dir = out_dir or (PROJECT_ROOT / "data" / "raw")
    proc_dir = processed_dir or DIR_PROCESSED
    raw_dir.mkdir(parents=True, exist_ok=True)
    proc_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = proc_dir / "data_manifest.csv"
    results: Dict[str, str] = {}

    try:
        import yfinance as yf
    except ImportError:
        print("[NOTICE] yfinance is not installed in the local environment. Keeping existing local CSV files.")
        return {
            "status": "fallback",
            "message": "yfinance not installed. Kept existing local CSV data without interruption.",
            "symbols": symbols,
        }

    manifest_rows: List[Dict[str, Any]] = []
    if manifest_path.exists():
        try:
            m_df = pd.read_csv(manifest_path)
            manifest_rows = m_df.to_dict(orient="records")
        except Exception:
            manifest_rows = []

    for sym in symbols:
        clean_sym = sym.strip().upper()
        if clean_sym in ("NIFTY", "NIFTY50", "^NSEI"):
            yf_ticker = "^NSEI"
            save_name = "NIFTY50.csv"
        elif clean_sym in ("INDIAVIX", "VIX", "^INDIAVIX"):
            yf_ticker = "^INDIAVIX"
            save_name = "INDIAVIX.csv"
        else:
            yf_ticker = f"{clean_sym}.NS" if not clean_sym.endswith(".NS") else clean_sym
            save_name = f"{clean_sym.replace('.NS', '')}.csv"

        try:
            print(f"Downloading {yf_ticker} via yfinance...")
            df_yf = yf.download(yf_ticker, start=start, end=end, progress=False, auto_adjust=False)
            if df_yf is None or df_yf.empty:
                print(f"[WARNING] Download for {yf_ticker} returned no data. Using existing local file if available.")
                results[clean_sym] = "no_data_fallback"
                continue

            if isinstance(df_yf.columns, pd.MultiIndex):
                df_yf.columns = df_yf.columns.get_level_values(0)

            df_yf = df_yf.reset_index()
            cols = [c for c in ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"] if c in df_yf.columns]
            df_clean = df_yf[cols].copy()
            df_clean["Date"] = pd.to_datetime(df_clean["Date"]).dt.strftime("%Y-%m-%d")

            dest_file = raw_dir / save_name
            df_clean.to_csv(dest_file, index=False)

            download_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row_count = len(df_clean)
            date_range = f"{df_clean['Date'].iloc[0]} to {df_clean['Date'].iloc[-1]}" if row_count > 0 else "N/A"

            manifest_entry = {
                "source": f"yfinance ({yf_ticker})",
                "download_date": download_date,
                "file_name": save_name,
                "row_count": row_count,
                "date_range": date_range,
                "adjustment_status": "Unadjusted Close with separate Adj Close",
            }
            manifest_rows = [r for r in manifest_rows if r.get("file_name") != save_name]
            manifest_rows.append(manifest_entry)
            results[clean_sym] = "downloaded"

        except Exception as e:
            print(f"[WARNING] Download failed for {clean_sym} ({yf_ticker}): {e}. Retaining existing saved file.")
            results[clean_sym] = f"failed: {e}"

    if manifest_rows:
        try:
            pd.DataFrame(manifest_rows).to_csv(manifest_path, index=False)
        except Exception as e:
            print(f"[WARNING] Could not update manifest: {e}")

    return {"status": "completed", "results": results}

