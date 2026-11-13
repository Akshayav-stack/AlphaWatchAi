"""
AlphaWatch AI — NSE Bhavcopy & Index Ingestion Engine
ASTRAQUANT X 2026

Ingests and standardizes official NSE market data files:
  - CM-UDiFF Common Bhavcopy (ZIP or CSV)
  - Legacy Bhavcopy layout (older formats)
  - Security-wise deliverable position archives
  - NIFTY 50 Index history
  - India VIX historical data

Filters strictly for Series 'EQ' and supported equities.
Emits clean, sorted, standardized datasets to data/processed/<SYMBOL>.csv
"""

import csv
import io
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIR_RAW_NSE = PROJECT_ROOT / "data" / "raw" / "nse"
DIR_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Supported equities for AlphaWatch AI MVP
DEFAULT_SUPPORTED_SYMBOLS: List[str] = [
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

STANDARD_COLUMNS = [
    "Date",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "DeliveryQty",
    "DeliveryPercent",
]


def parse_date_string(date_str: str) -> str:
    """
    Normalizes various date string formats to ISO standard YYYY-MM-DD.
    Examples: '2026-10-30', '30-OCT-2026', '30-10-2026', '30/10/2026'.
    """
    clean_str = date_str.strip()
    if not clean_str:
        raise ValueError("Empty date string")

    # Try common formats
    formats = [
        "%Y-%m-%d",
        "%d-%b-%Y",
        "%d-%B-%Y",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d-%m-%y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(clean_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Fallback to pandas parser if standard patterns fail
    parsed = pd.to_datetime(clean_str)
    return parsed.strftime("%Y-%m-%d")


def is_cm_udiff_bhavcopy(headers: List[str]) -> bool:
    """Detects if header belongs to modern CM-UDiFF Common Bhavcopy format."""
    norm = {h.strip().upper() for h in headers}
    return {"TRADDT", "TCKRSYMB", "SCTYSRS", "CLSPRIC"}.issubset(norm)


def is_legacy_bhavcopy(headers: List[str]) -> bool:
    """Detects if header belongs to legacy NSE Bhavcopy format."""
    norm = {h.strip().upper() for h in headers}
    return {"SYMBOL", "SERIES", "CLOSE"}.issubset(norm) and (
        "TIMESTAMP" in norm or "DATE" in norm
    )


def parse_bhavcopy_stream(
    stream: io.TextIOBase,
    supported_symbols: Set[str],
) -> List[Dict[str, float | str]]:
    """
    Parses a single Bhavcopy CSV stream (CM-UDiFF or Legacy),
    filtering strictly for Series == 'EQ' and target symbols.
    """
    reader = csv.DictReader(stream)
    if not reader.fieldnames:
        return []

    # Map headers to uppercase stripped keys
    field_map = {f.strip().upper(): f for f in reader.fieldnames}
    records: List[Dict[str, float | str]] = []

    is_udiff = is_cm_udiff_bhavcopy(reader.fieldnames)
    is_legacy = is_legacy_bhavcopy(reader.fieldnames)

    if not is_udiff and not is_legacy:
        # Check if generic format with Symbol, Date, Open, High, Low, Close
        norm = {h.strip().upper() for h in reader.fieldnames}
        if {"SYMBOL", "DATE", "CLOSE"}.issubset(norm):
            is_legacy = True
        else:
            return []

    for row in reader:
        # Clean row dictionary keys
        clean_row = {k.strip().upper(): v.strip() for k, v in row.items() if k and v}

        if is_udiff:
            series = clean_row.get("SCTYSRS", "").upper()
            symbol = clean_row.get("TCKRSYMB", "").upper()
            if series != "EQ" or symbol not in supported_symbols:
                continue

            try:
                date_val = parse_date_string(clean_row.get("TRADDT", ""))
                open_val = float(clean_row.get("OPNPRIC", 0.0))
                high_val = float(clean_row.get("HGHPRIC", 0.0))
                low_val = float(clean_row.get("LWPRIC", 0.0))
                close_val = float(clean_row.get("CLSPRIC", 0.0))
                vol_val = float(clean_row.get("TTLTRADGVOL", 0.0))
            except (ValueError, TypeError):
                continue

        else:  # Legacy
            series = clean_row.get("SERIES", "").upper()
            symbol = clean_row.get("SYMBOL", "").upper()
            # In legacy, some files have no series column or series is EQ
            if series and series != "EQ":
                continue
            if symbol not in supported_symbols:
                continue

            date_raw = clean_row.get("TIMESTAMP", clean_row.get("DATE", ""))
            try:
                date_val = parse_date_string(date_raw)
                open_val = float(clean_row.get("OPEN", 0.0))
                high_val = float(clean_row.get("HIGH", 0.0))
                low_val = float(clean_row.get("LOW", 0.0))
                close_val = float(clean_row.get("CLOSE", 0.0))
                vol_val = float(clean_row.get("TOTTRDQTY", clean_row.get("VOLUME", 0.0)))
            except (ValueError, TypeError):
                continue

        records.append({
            "Symbol": symbol,
            "Date": date_val,
            "Open": open_val,
            "High": high_val,
            "Low": low_val,
            "Close": close_val,
            "Volume": vol_val,
            "DeliveryQty": 0.0,
            "DeliveryPercent": 0.0,
        })

    return records


def parse_delivery_file(file_path: Path, supported_symbols: Set[str]) -> Dict[Tuple[str, str], Tuple[float, float]]:
    """
    Parses security delivery report (e.g. sec_bhavdata_full_YYYYMMDD.csv).
    Returns mapping: (Symbol, Date) -> (DeliveryQty, DeliveryPercent).
    """
    delivery_map: Dict[Tuple[str, str], Tuple[float, float]] = {}

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return delivery_map

            for row in reader:
                clean_row = {k.strip().upper(): v.strip() for k, v in row.items() if k and v}
                series = clean_row.get("SERIES", "").upper()
                symbol = clean_row.get("SYMBOL", "").upper()
                if series != "EQ" or symbol not in supported_symbols:
                    continue

                date_raw = clean_row.get("DATE", "")
                if not date_raw:
                    continue
                try:
                    date_val = parse_date_string(date_raw)
                    deliv_qty = float(clean_row.get("DELIVERABLE QTY", clean_row.get("DELIV_QTY", 0.0)))
                    deliv_per = float(clean_row.get("% DLY QT TO TRADED QTY", clean_row.get("DELIV_PER", 0.0)))
                    delivery_map[(symbol, date_val)] = (deliv_qty, deliv_per)
                except (ValueError, TypeError):
                    continue
    except Exception:
        pass

    return delivery_map


def ingest_all_nse_bhavcopies(
    raw_dir: Path = DIR_RAW_NSE,
    output_dir: Path = DIR_PROCESSED,
    supported_symbols: Optional[List[str]] = None,
) -> Dict[str, int]:
    """
    Scans raw_dir for Bhavcopy ZIPs and CSVs, parses and consolidates
    records per symbol, merges delivery metrics if available,
    and writes clean CSV files to data/processed/<SYMBOL>.csv.
    """
    symbols = set(supported_symbols or DEFAULT_SUPPORTED_SYMBOLS)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_records: List[Dict[str, float | str]] = []
    delivery_lookup: Dict[Tuple[str, str], Tuple[float, float]] = {}

    if not raw_dir.exists():
        return {}

    # Pass 1: Parse all delivery reports first to build delivery lookup
    for file_path in raw_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".csv":
            if "delivery" in file_path.name.lower() or "sec_bhavdata" in file_path.name.lower():
                lookup = parse_delivery_file(file_path, symbols)
                delivery_lookup.update(lookup)

    # Pass 2: Ingest Bhavcopy files (both uncompressed CSV and ZIP files)
    for file_path in raw_dir.iterdir():
        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()

        # Direct CSV bhavcopies
        if suffix == ".csv":
            # Skip pure delivery or index files in bhavcopy parser pass
            if any(k in file_path.name.lower() for k in ("nifty", "vix", "delivery", "sec_bhavdata")):
                continue

            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                records = parse_bhavcopy_stream(f, symbols)
                all_records.extend(records)

        # ZIP Archives containing bhavcopy CSVs
        elif suffix == ".zip":
            try:
                with zipfile.ZipFile(file_path, "r") as zf:
                    for member in zf.infolist():
                        if member.filename.lower().endswith(".csv"):
                            with zf.open(member) as f_bin:
                                text_stream = io.TextIOWrapper(f_bin, encoding="utf-8", errors="replace")
                                records = parse_bhavcopy_stream(text_stream, symbols)
                                all_records.extend(records)
            except Exception as exc:
                print(f"[Warning] Failed to read zip archive {file_path.name}: {exc}")

    if not all_records:
        return {}

    # Merge delivery metrics into records
    for rec in all_records:
        key = (str(rec["Symbol"]), str(rec["Date"]))
        if key in delivery_lookup:
            d_qty, d_pct = delivery_lookup[key]
            rec["DeliveryQty"] = d_qty
            rec["DeliveryPercent"] = d_pct
        elif rec["Volume"] > 0 and rec["DeliveryQty"] == 0:
            # Estimate delivery pct as conservative 0.0 if delivery file not present
            rec["DeliveryPercent"] = 0.0

    # Group by Symbol and write per-symbol CSV
    df_all = pd.DataFrame(all_records)
    summary: Dict[str, int] = {}

    for symbol, df_group in df_all.groupby("Symbol"):
        # Sort chronologically and drop duplicate dates
        df_group = df_group.drop_duplicates(subset=["Date"]).sort_values(by="Date").reset_index(drop=True)
        out_path = output_dir / f"{symbol}.csv"
        
        # Ensure standard column sequence
        df_group = df_group[STANDARD_COLUMNS]
        df_group.to_csv(out_path, index=False)
        summary[str(symbol)] = len(df_group)

    return summary


def ingest_nifty50_history(
    raw_dir: Path = DIR_RAW_NSE,
    output_dir: Path = DIR_PROCESSED,
) -> Optional[Path]:
    """Ingests NIFTY 50 historical data and produces data/processed/NIFTY50.csv."""
    output_dir.mkdir(parents=True, exist_ok=True)
    target_out = output_dir / "NIFTY50.csv"

    candidate_files = [
        f for f in raw_dir.glob("*nifty*50*.csv") if "list" not in f.name.lower()
    ]
    if not candidate_files:
        candidate_files = list(raw_dir.glob("*NIFTY*.csv"))

    if not candidate_files:
        return None

    # Load candidate file
    df_raw = pd.read_csv(candidate_files[0])
    col_map = {c.strip().upper(): c for c in df_raw.columns}

    date_col = next((col_map[c] for c in ["DATE", "HISTORICALDATE"] if c in col_map), None)
    open_col = next((col_map[c] for c in ["OPEN", "OPEN PRICE"] if c in col_map), None)
    high_col = next((col_map[c] for c in ["HIGH", "HIGH PRICE"] if c in col_map), None)
    low_col = next((col_map[c] for c in ["LOW", "LOW PRICE"] if c in col_map), None)
    close_col = next((col_map[c] for c in ["CLOSE", "CLOSE PRICE"] if c in col_map), None)
    vol_col = next((col_map[c] for c in ["SHARES TRADED", "VOLUME", "TOTAL TRADED QUANTITY"] if c in col_map), None)

    if not (date_col and close_col):
        return None

    clean_df = pd.DataFrame()
    clean_df["Date"] = df_raw[date_col].astype(str).apply(parse_date_string)
    clean_df["Open"] = pd.to_numeric(df_raw[open_col], errors="coerce") if open_col else df_raw[close_col]
    clean_df["High"] = pd.to_numeric(df_raw[high_col], errors="coerce") if high_col else df_raw[close_col]
    clean_df["Low"] = pd.to_numeric(df_raw[low_col], errors="coerce") if low_col else df_raw[close_col]
    clean_df["Close"] = pd.to_numeric(df_raw[close_col], errors="coerce")
    clean_df["Volume"] = pd.to_numeric(df_raw[vol_col], errors="coerce").fillna(0) if vol_col else 0.0

    clean_df = clean_df.dropna(subset=["Date", "Close"]).drop_duplicates(subset=["Date"]).sort_values(by="Date").reset_index(drop=True)
    clean_df.to_csv(target_out, index=False)
    return target_out


def ingest_india_vix_history(
    raw_dir: Path = DIR_RAW_NSE,
    output_dir: Path = DIR_PROCESSED,
) -> Optional[Path]:
    """Ingests India VIX historical data and produces data/processed/INDIAVIX.csv."""
    output_dir.mkdir(parents=True, exist_ok=True)
    target_out = output_dir / "INDIAVIX.csv"

    candidate_files = list(raw_dir.glob("*vix*.csv"))
    if not candidate_files:
        return None

    df_raw = pd.read_csv(candidate_files[0])
    col_map = {c.strip().upper(): c for c in df_raw.columns}

    date_col = next((col_map[c] for c in ["DATE", "HISTORICALDATE"] if c in col_map), None)
    open_col = next((col_map[c] for c in ["OPEN", "OPEN PRICE"] if c in col_map), None)
    high_col = next((col_map[c] for c in ["HIGH", "HIGH PRICE"] if c in col_map), None)
    low_col = next((col_map[c] for c in ["LOW", "LOW PRICE"] if c in col_map), None)
    close_col = next((col_map[c] for c in ["CLOSE", "CLOSE PRICE", "VIX"] if c in col_map), None)

    if not (date_col and close_col):
        return None

    clean_df = pd.DataFrame()
    clean_df["Date"] = df_raw[date_col].astype(str).apply(parse_date_string)
    clean_df["Open"] = pd.to_numeric(df_raw[open_col], errors="coerce") if open_col else df_raw[close_col]
    clean_df["High"] = pd.to_numeric(df_raw[high_col], errors="coerce") if high_col else df_raw[close_col]
    clean_df["Low"] = pd.to_numeric(df_raw[low_col], errors="coerce") if low_col else df_raw[close_col]
    clean_df["Close"] = pd.to_numeric(df_raw[close_col], errors="coerce")

    clean_df = clean_df.dropna(subset=["Date", "Close"]).drop_duplicates(subset=["Date"]).sort_values(by="Date").reset_index(drop=True)
    clean_df.to_csv(target_out, index=False)
    return target_out
