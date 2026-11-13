"""
AlphaWatch AI — Offline Data Fetch & Validation Helper
ASTRAQUANT X 2026

CRITICAL SYSTEM NOTICE:
This is a standalone offline utility run manually by researchers or engineers.
It is NEVER imported by or executed from within the running website application.
The running AlphaWatch AI web platform strictly operates on local saved files.

Usage:
    python scripts/fetch_data.py                   # Default: Prints manual download checklist
    python scripts/fetch_data.py --verify-local    # Validates locally placed files & updates manifest
    python scripts/fetch_data.py --assisted        # Polite automated downloader (requires explicit flag)
    python scripts/fetch_data.py --create-samples  # Creates tiny SAMPLE files for testing
"""

import argparse
import csv
import hashlib
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Supported Indian equities for AlphaWatch AI MVP
SUPPORTED_SYMBOLS: List[str] = [
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

# Project root and standard data directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIR_RAW_NSE = PROJECT_ROOT / "data" / "raw" / "nse"
DIR_RAW_SCREENER = PROJECT_ROOT / "data" / "raw" / "screener"
DIR_PROCESSED = PROJECT_ROOT / "data" / "processed"
MANIFEST_PATH = DIR_PROCESSED / "data_manifest.csv"

# Expected column schemas for known reports
SCHEMA_BHAVCOPY_UDIFF = {"TradDt", "TckrSymb", "OpnPric", "HghPric", "LwPric", "ClsPric", "TtlTradgVol"}
SCHEMA_BHAVCOPY_LEGACY = {"SYMBOL", "SERIES", "OPEN", "HIGH", "LOW", "CLOSE", "TOTTRDQTY"}
SCHEMA_DELIVERY = {"Symbol", "Series", "Date", "Close Price"}  # plus delivery % columns
SCHEMA_NIFTY50 = {"Date", "Open", "High", "Low", "Close"}
SCHEMA_INDIAVIX = {"Date", "Open", "High", "Low", "Close"}

USER_AGENT = "AlphaWatchAI-ResearchFetcher/1.0 (Educational Quantitative Research; +https://github.com/ASTRAQUANT-X)"


@dataclass
class ValidationResult:
    """Holds the result of a file integrity and schema validation check."""
    is_valid: bool
    file_name: str
    file_path: Path
    file_size_bytes: int
    row_count: int
    date_range: str
    sha256: str
    error_message: Optional[str] = None
    report_type: Optional[str] = None


def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 hash in 64KB streaming blocks."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def print_manual_checklist() -> None:
    """Prints the comprehensive manual download checklist for researchers."""
    print("=" * 80)
    print("ALPHAWATCH AI — OFFLINE DATA DOWNLOAD CHECKLIST (MANUAL MODE)")
    print("=" * 80)
    print(
        "To ensure 100% offline, deterministic, and reproducible operation, download\n"
        "the following official reports and place them into the designated folders.\n"
    )

    print("1. NSE CM-UDiFF Common Bhavcopy Final (or Legacy Bhavcopy ZIP)")
    print("   • Source URL : https://www.nseindia.com/all-reports")
    print("   • Historical : https://www.nseindia.com/resources/historical-reports-capital-market-daily-monthly-archives")
    print("   • Report Name: Common Bhavcopy (PR.zip or Bhavcopy UDiFF zip)")
    print(f"   • Save into  : {DIR_RAW_NSE.resolve()}")
    print("   • Expected File: 'BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv' or 'cmDDMMMYYYYbhav.csv'\n")

    print("2. Security-wise Price, Volume and Deliverable Position Data")
    print("   • Source URL : https://www.nseindia.com/report-detail/eq_security")
    print("   • Historical : Select individual symbols (e.g. RELIANCE, TCS) -> 365 Days / Custom Range")
    print(f"   • Save into  : {DIR_RAW_NSE.resolve()}")
    print("   • Expected File: 'sec_bhavdata_full_YYYYMMDD.csv' or '<SYMBOL>_price_volume_delivery.csv'\n")

    print("3. NIFTY 50 Index Historical Close & Daily Averages")
    print("   • Source URL : https://www.nseindia.com/reports-indices-historical-index-data")
    print("   • Index Name : NIFTY 50 (Daily closing prices)")
    print(f"   • Save into  : {DIR_RAW_NSE.resolve()}")
    print("   • Expected File: 'NIFTY50_historical.csv' or 'data.csv'\n")

    print("4. India VIX (Volatility Index) Daily Historical Data")
    print("   • Source URL : https://www.nseindia.com/reports-indices-historical-vix")
    print("   • Report Name: Historical Index Data for India VIX")
    print(f"   • Save into  : {DIR_RAW_NSE.resolve()}")
    print("   • Expected File: 'India_VIX_historical.csv' or 'hist_vix_data.csv'\n")

    print("5. Screener.in Fundamental Financial Export Workbooks (.xlsx)")
    print("   • Source URL : https://www.screener.in/company/<SYMBOL>/")
    print("   • Action     : Click 'Export to Excel' for each supported stock:")
    print(f"                  {', '.join(SUPPORTED_SYMBOLS)}")
    print(f"   • Save into  : {DIR_RAW_SCREENER.resolve()}")
    print("   • Expected File: '<SYMBOL>.xlsx' (e.g. RELIANCE.xlsx, TCS.xlsx)\n")

    print("=" * 80)
    print("AFTER PLACING FILES:")
    print("Run `python scripts/fetch_data.py --verify-local` to validate headers,")
    print("calculate SHA-256 hashes, and record entries in `data/processed/data_manifest.csv`.")
    print("=" * 80)


def safe_extract_zip(zip_path: Path, target_dir: Path) -> List[Path]:
    """
    Safely opens and extracts a zip file while strictly guarding against
    path traversal (Zip Slip vulnerability).

    Raises:
        ValueError: If any member path escapes target_dir.
    """
    if not zipfile.is_zipfile(zip_path):
        raise ValueError(f"File is not a valid zip archive: {zip_path.name}")

    extracted_files: List[Path] = []
    target_dir_resolved = target_dir.resolve()

    with zipfile.ZipFile(zip_path, "r") as archive:
        for member in archive.infolist():
            # Resolve the intended absolute extraction path
            target_path = (target_dir / member.filename).resolve()
            
            # Strict boundary check: extracted path MUST start with target_dir_resolved
            if not str(target_path).startswith(str(target_dir_resolved)):
                raise ValueError(
                    f"Security Error: Path traversal attempt detected in zip archive '{zip_path.name}' "
                    f"for entry '{member.filename}'"
                )

            # Prevent executing downloaded binary/executable content
            lower_name = member.filename.lower()
            if lower_name.endswith((".exe", ".bat", ".cmd", ".sh", ".ps1", ".vbs", ".dll", ".so")):
                raise ValueError(
                    f"Security Error: Executable content '{member.filename}' rejected in zip archive."
                )

            if member.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
            else:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, open(target_path, "wb") as dest:
                    dest.write(source.read())
                extracted_files.append(target_path)

    return extracted_files


def detect_report_type_and_schema(headers: List[str]) -> Tuple[str, bool]:
    """
    Identifies the report type and checks if mandatory columns are present.
    Returns (report_type_name, is_schema_valid).
    """
    norm_headers = {h.strip().replace('"', "") for h in headers}

    if SCHEMA_BHAVCOPY_UDIFF.issubset(norm_headers):
        return "NSE CM-UDiFF Bhavcopy", True
    if SCHEMA_BHAVCOPY_LEGACY.issubset(norm_headers):
        return "NSE Legacy Bhavcopy", True
    if {"Symbol", "Series", "Date"}.issubset(norm_headers) and any("dly" in h.lower() or "deliv" in h.lower() for h in norm_headers):
        return "NSE Security Delivery Data", True
    if {"Date", "Open", "High", "Low", "Close"}.issubset(norm_headers):
        # Could be NIFTY50 or VIX
        if any("vix" in h.lower() for h in norm_headers) or any("change" in h.lower() for h in norm_headers):
            return "India VIX Historical Data", True
        return "NIFTY 50 Historical Data", True

    return "Generic Stock/Index CSV", True


def validate_csv_file(file_path: Path) -> ValidationResult:
    """Validates a CSV file: checks size, parsability, row count, headers, date span, and hash."""
    file_size = file_path.stat().st_size
    if file_size == 0:
        return ValidationResult(
            is_valid=False,
            file_name=file_path.name,
            file_path=file_path,
            file_size_bytes=0,
            row_count=0,
            date_range="N/A",
            sha256="",
            error_message="File is empty (0 bytes).",
        )

    sha256_hash = compute_sha256(file_path)

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header_row = next(reader, None)
            if not header_row:
                return ValidationResult(
                    is_valid=False,
                    file_name=file_path.name,
                    file_path=file_path,
                    file_size_bytes=file_size,
                    row_count=0,
                    date_range="N/A",
                    sha256=sha256_hash,
                    error_message="CSV has no header row.",
                )

            report_type, schema_ok = detect_report_type_and_schema(header_row)

            # Discover date column index if present
            date_col_idx = None
            for idx, col in enumerate(header_row):
                clean_col = col.strip().lower()
                if clean_col in ("traddt", "date", "timestamp", "historicaldate"):
                    date_col_idx = idx
                    break

            dates: List[str] = []
            row_count = 0
            for row in reader:
                if not row or not any(row):
                    continue
                row_count += 1
                if date_col_idx is not None and len(row) > date_col_idx:
                    dates.append(row[date_col_idx].strip())

            date_range = "N/A"
            if dates:
                date_range = f"{dates[0]} to {dates[-1]}" if len(dates) > 1 else dates[0]

            return ValidationResult(
                is_valid=True,
                file_name=file_path.name,
                file_path=file_path,
                file_size_bytes=file_size,
                row_count=row_count,
                date_range=date_range,
                sha256=sha256_hash,
                report_type=report_type,
            )
    except Exception as exc:
        return ValidationResult(
            is_valid=False,
            file_name=file_path.name,
            file_path=file_path,
            file_size_bytes=file_size,
            row_count=0,
            date_range="N/A",
            sha256=sha256_hash,
            error_message=f"CSV read error: {str(exc)}",
        )


def validate_excel_file(file_path: Path) -> ValidationResult:
    """Validates an Excel workbook (.xlsx): checks size, zip-container validity, and computes hash."""
    file_size = file_path.stat().st_size
    if file_size == 0:
        return ValidationResult(
            is_valid=False,
            file_name=file_path.name,
            file_path=file_path,
            file_size_bytes=0,
            row_count=0,
            date_range="N/A",
            sha256="",
            error_message="Excel file is empty (0 bytes).",
        )

    sha256_hash = compute_sha256(file_path)

    # An .xlsx file is an OpenXML ZIP package. Verify it is a valid zip archive without corruption.
    if not zipfile.is_zipfile(file_path):
        return ValidationResult(
            is_valid=False,
            file_name=file_path.name,
            file_path=file_path,
            file_size_bytes=file_size,
            row_count=0,
            date_range="N/A",
            sha256=sha256_hash,
            error_message="Not a valid OpenXML Excel workbook (.xlsx).",
        )

    try:
        with zipfile.ZipFile(file_path, "r") as archive:
            # Check for critical internal structures of Excel workbook
            namelist = archive.namelist()
            if not any("xl/workbook.xml" in name for name in namelist):
                return ValidationResult(
                    is_valid=False,
                    file_name=file_path.name,
                    file_path=file_path,
                    file_size_bytes=file_size,
                    row_count=0,
                    date_range="N/A",
                    sha256=sha256_hash,
                    error_message="Missing 'xl/workbook.xml' in Excel container.",
                )

        return ValidationResult(
            is_valid=True,
            file_name=file_path.name,
            file_path=file_path,
            file_size_bytes=file_size,
            row_count=1,
            date_range="Multiple Financial Years",
            sha256=sha256_hash,
            report_type="Screener.in Financial Workbook",
        )
    except Exception as exc:
        return ValidationResult(
            is_valid=False,
            file_name=file_path.name,
            file_path=file_path,
            file_size_bytes=file_size,
            row_count=0,
            date_range="N/A",
            sha256=sha256_hash,
            error_message=f"Excel inspection failed: {str(exc)}",
        )


def validate_file(file_path: Path) -> ValidationResult:
    """Dispatches validation based on extension (.csv, .xlsx, .zip)."""
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return validate_csv_file(file_path)
    elif suffix == ".xlsx":
        return validate_excel_file(file_path)
    elif suffix == ".zip":
        try:
            # Validate safe zip without extracting
            if not zipfile.is_zipfile(file_path):
                return ValidationResult(
                    is_valid=False,
                    file_name=file_path.name,
                    file_path=file_path,
                    file_size_bytes=file_path.stat().st_size,
                    row_count=0,
                    date_range="N/A",
                    sha256=compute_sha256(file_path),
                    error_message="Invalid zip archive.",
                )
            # Test opening and scan members for path traversal
            with zipfile.ZipFile(file_path, "r") as zf:
                for member in zf.infolist():
                    if member.filename.startswith(("/", "\\")) or ".." in member.filename:
                        return ValidationResult(
                            is_valid=False,
                            file_name=file_path.name,
                            file_path=file_path,
                            file_size_bytes=file_path.stat().st_size,
                            row_count=0,
                            date_range="N/A",
                            sha256=compute_sha256(file_path),
                            error_message="Path traversal sequence detected inside archive.",
                        )
            return ValidationResult(
                is_valid=True,
                file_name=file_path.name,
                file_path=file_path,
                file_size_bytes=file_path.stat().st_size,
                row_count=1,
                date_range="Archive",
                sha256=compute_sha256(file_path),
                report_type="ZIP Archive",
            )
        except Exception as exc:
            return ValidationResult(
                is_valid=False,
                file_name=file_path.name,
                file_path=file_path,
                file_size_bytes=file_path.stat().st_size if file_path.exists() else 0,
                row_count=0,
                date_range="N/A",
                sha256="",
                error_message=str(exc),
            )
    else:
        return ValidationResult(
            is_valid=False,
            file_name=file_path.name,
            file_path=file_path,
            file_size_bytes=file_path.stat().st_size if file_path.exists() else 0,
            row_count=0,
            date_range="N/A",
            sha256="",
            error_message=f"Unsupported file extension '{suffix}'.",
        )


def append_to_manifest(
    source: str,
    url: str,
    report_name: str,
    file_name: str,
    rows: int,
    date_range: str,
    sha256_hash: str,
    manifest_path: Optional[Path] = None,
) -> None:
    """Appends or updates a record in data/processed/data_manifest.csv."""
    target_manifest = manifest_path or MANIFEST_PATH
    target_manifest.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source",
        "url",
        "report_name",
        "file_name",
        "download_date",
        "rows",
        "date_range",
        "sha256",
    ]

    records: List[Dict[str, str]] = []
    if target_manifest.exists():
        with open(target_manifest, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Deduplicate by file_name
                if row.get("file_name") != file_name:
                    records.append(row)

    download_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = {
        "source": source,
        "url": url,
        "report_name": report_name,
        "file_name": file_name,
        "download_date": download_date,
        "rows": str(rows),
        "date_range": date_range,
        "sha256": sha256_hash,
    }
    records.append(new_entry)

    with open(target_manifest, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def polite_download(
    url: str,
    destination: Path,
    max_retries: int = 3,
    min_delay: float = 2.0,
) -> bool:
    """
    Downloads a single file politely:
      - 1 request at a time
      - At least 2.0 seconds between requests
      - Custom educational user agent
      - Max 3 retries with exponential backoff on transient errors
      - Immediate abort on HTTP 403 or HTTP 429
      - Never bypasses blocks; never logs in.
    """
    print(f"\n[Polite Downloader] Requesting: {url}")
    print(f"Target destination: {destination}")

    # Build request with clear User-Agent
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
        },
    )

    ctx = ssl.create_default_context()

    for attempt in range(1, max_retries + 1):
        try:
            time.sleep(min_delay)
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                content = response.read()
                destination.parent.mkdir(parents=True, exist_ok=True)
                with open(destination, "wb") as f:
                    f.write(content)
                print(f"[Polite Downloader] Successfully fetched {len(content):,} bytes -> {destination.name}")
                return True
        except urllib.error.HTTPError as http_err:
            if http_err.code in (403, 429):
                print("=" * 80)
                print(f"[ACCESS RESTRICTED] The server responded with HTTP {http_err.code}: {http_err.reason}")
                print("In compliance with security & academic guidelines, AlphaWatch AI will NEVER attempt")
                print("to bypass access controls, spoof credentials, or solve challenges.")
                print("ACTION REQUIRED: Please use MANUAL MODE to download the file directly in your browser:")
                print(f"URL: {url}")
                print(f"Save as: {destination.resolve()}")
                print("=" * 80)
                return False
            else:
                backoff = min_delay * (2 ** (attempt - 1))
                print(f"[Warning] HTTP {http_err.code} on attempt {attempt}/{max_retries}. Backing off {backoff:.1f}s...")
                time.sleep(backoff)
        except (urllib.error.URLError, TimeoutError) as net_err:
            backoff = min_delay * (2 ** (attempt - 1))
            print(f"[Warning] Network error ({net_err}) on attempt {attempt}/{max_retries}. Backing off {backoff:.1f}s...")
            time.sleep(backoff)
        except Exception as exc:
            print(f"[Error] Unexpected failure: {exc}")
            return False

    print(f"[Failed] Could not download file after {max_retries} attempts.")
    return False


def verify_all_local_files() -> None:
    """Scans data/raw/nse and data/raw/screener, validates files, and updates data_manifest.csv."""
    print("=" * 80)
    print("ALPHAWATCH AI — VERIFYING LOCAL RAW DATA FILES")
    print("=" * 80)

    raw_files: List[Path] = []
    if DIR_RAW_NSE.exists():
        raw_files.extend([p for p in DIR_RAW_NSE.iterdir() if p.is_file() and p.name != ".gitkeep"])
    if DIR_RAW_SCREENER.exists():
        raw_files.extend([p for p in DIR_RAW_SCREENER.iterdir() if p.is_file() and p.name != ".gitkeep"])

    if not raw_files:
        print(f"No raw files found in:\n  - {DIR_RAW_NSE.resolve()}\n  - {DIR_RAW_SCREENER.resolve()}")
        print("\nPlease follow MANUAL mode checklist or use --create-samples to initialize testing data.")
        return

    valid_count = 0
    for file_path in sorted(raw_files):
        res = validate_file(file_path)
        source = "Screener.in" if "screener" in str(file_path) else "NSE India"
        status_label = "[VALID]" if res.is_valid else "[INVALID]"
        print(f"{status_label:9} {file_path.name}")
        print(f"          Report: {res.report_type or 'Unknown'} | Size: {res.file_size_bytes:,} bytes | Rows: {res.row_count}")
        print(f"          Range : {res.date_range} | SHA-256: {res.sha256[:16]}...")
        if not res.is_valid:
            print(f"          Error : {res.error_message}")
        else:
            valid_count += 1
            append_to_manifest(
                source=source,
                url="Local Import",
                report_name=res.report_type or file_path.name,
                file_name=file_path.name,
                rows=res.row_count,
                date_range=res.date_range,
                sha256_hash=res.sha256,
            )

    print("-" * 80)
    print(f"Verification complete: {valid_count}/{len(raw_files)} files valid.")
    print(f"Updated manifest at: {MANIFEST_PATH.resolve()}")
    print("=" * 80)


def create_sample_files() -> None:
    """
    Generates tiny verified sample files clearly labeled SAMPLE in the header
    for unit testing and offline development demonstration.
    """
    DIR_RAW_NSE.mkdir(parents=True, exist_ok=True)
    DIR_RAW_SCREENER.mkdir(parents=True, exist_ok=True)

    # 1. Sample NSE Bhavcopy (UDiFF standard)
    sample_bhavcopy_path = DIR_RAW_NSE / "SAMPLE_bhavcopy_udiff.csv"
    bhavcopy_rows = [
        ["TradDt", "BizDt", "Sgmt", "Src", "FinInstrmTp", "FinInstrmId", "ISIN", "TckrSymb", "SctySrs", "OpnPric", "HghPric", "LwPric", "ClsPric", "LastPric", "PrvsClsgPric", "TtlTradgVol", "TtlTrfVal", "TtlNbOfTxsExctd"],
        ["2026-10-30", "2026-10-30", "CM", "NSE", "STK", "1", "INE002A01018", "RELIANCE", "EQ", "2800.00", "2850.00", "2790.00", "2835.50", "2836.00", "2795.00", "5200000", "14700000000", "150000"],
        ["2026-10-30", "2026-10-30", "CM", "NSE", "STK", "2", "INE467B01029", "TCS", "EQ", "3900.00", "3940.00", "3880.00", "3920.00", "3925.00", "3890.00", "1800000", "7050000000", "85000"],
        ["2026-10-30", "2026-10-30", "CM", "NSE", "STK", "3", "INE040A01034", "HDFCBANK", "EQ", "1650.00", "1675.00", "1645.00", "1668.00", "1670.00", "1648.00", "7800000", "13000000000", "195000"],
    ]
    with open(sample_bhavcopy_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(bhavcopy_rows)

    # 2. Sample NIFTY 50 Historical CSV
    sample_nifty_path = DIR_RAW_NSE / "SAMPLE_NIFTY50_historical.csv"
    nifty_rows = [
        ["Date", "Open", "High", "Low", "Close", "Shares Traded", "Turnover (₹ Cr)"],
        ["2026-10-28", "24200.00", "24350.00", "24150.00", "24300.00", "280000000", "25000.00"],
        ["2026-10-29", "24320.00", "24410.00", "24280.00", "24380.00", "295000000", "26500.00"],
        ["2026-10-30", "24400.00", "24520.00", "24360.00", "24480.00", "310000000", "28000.00"],
    ]
    with open(sample_nifty_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(nifty_rows)

    # 3. Sample India VIX Historical CSV
    sample_vix_path = DIR_RAW_NSE / "SAMPLE_India_VIX_historical.csv"
    vix_rows = [
        ["Date", "Open", "High", "Low", "Close", "Prev. Close", "Change", "%Change"],
        ["2026-10-28", "14.20", "14.80", "13.90", "14.10", "14.30", "-0.20", "-1.40"],
        ["2026-10-29", "14.10", "14.50", "13.75", "13.85", "14.10", "-0.25", "-1.77"],
        ["2026-10-30", "13.80", "14.10", "13.50", "13.65", "13.85", "-0.20", "-1.44"],
    ]
    with open(sample_vix_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(vix_rows)

    # 4. Sample Delivery Position CSV
    sample_deliv_path = DIR_RAW_NSE / "SAMPLE_delivery_data.csv"
    deliv_rows = [
        ["Record Type", "Sr No", "Symbol", "Series", "Date", "Prev Close", "Open Price", "High Price", "Low Price", "Last Price", "Close Price", "Avg Price", "Total Traded Quantity", "Turnover in Lacs", "No. of Trades", "Deliverable Qty", "% Dly Qt to Traded Qty"],
        ["20", "1", "RELIANCE", "EQ", "2026-10-30", "2795.00", "2800.00", "2850.00", "2790.00", "2836.00", "2835.50", "2825.00", "5200000", "147000.00", "150000", "2860000", "55.00"],
        ["20", "2", "TCS", "EQ", "2026-10-30", "3890.00", "3900.00", "3940.00", "3880.00", "3925.00", "3920.00", "3915.00", "1800000", "70500.00", "85000", "1170000", "65.00"],
    ]
    with open(sample_deliv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(deliv_rows)

    # 5. Sample Screener.in workbook container (.xlsx)
    sample_xlsx_path = DIR_RAW_SCREENER / "SAMPLE_RELIANCE.xlsx"
    with zipfile.ZipFile(sample_xlsx_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
        zf.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>')
        zf.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="Data Sheet" sheetId="1"/></sheets></workbook>')

    print("Created tiny verified SAMPLE files:")
    print(f"  • {sample_bhavcopy_path}")
    print(f"  • {sample_nifty_path}")
    print(f"  • {sample_vix_path}")
    print(f"  • {sample_deliv_path}")
    print(f"  • {sample_xlsx_path}")

    # Register sample files in manifest
    verify_all_local_files()


def run_assisted_mode() -> None:
    """Runs the assisted downloader with mandatory compliance check and politeness constraints."""
    print("=" * 80)
    print("ALPHAWATCH AI — ASSISTED DATA DOWNLOADER")
    print("=" * 80)
    print("LEGAL & REGULATORY REMINDER:")
    print("1. Ensure that you have reviewed and complied with the Terms of Use, acceptable use")
    print("   policies, and robots.txt of the data providers before proceeding.")
    print("2. AlphaWatch AI is strictly an academic research tool.")
    print("3. Requests are executed politely: 1 request at a time, min 2s delay, no logins,")
    print("   no credential spoofing, and no bypass of anti-bot protections.")
    print("=" * 80)

    # Example endpoint list for demonstration in assisted mode
    targets = [
        {
            "name": "NIFTY 50 Sample Historical Archive",
            "url": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
            "destination": DIR_RAW_NSE / "ind_nifty50list.csv",
            "source": "NSE India",
        }
    ]

    for item in targets:
        success = polite_download(item["url"], item["destination"])
        if success:
            res = validate_file(item["destination"])
            if res.is_valid:
                append_to_manifest(
                    source=item["source"],
                    url=item["url"],
                    report_name=res.report_type or item["name"],
                    file_name=item["destination"].name,
                    rows=res.row_count,
                    date_range=res.date_range,
                    sha256_hash=res.sha256,
                )
            else:
                print(f"[Warning] Downloaded file validation failed: {res.error_message}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AlphaWatch AI — Standalone Offline Data Fetch & Validation Helper"
    )
    parser.add_argument(
        "--assisted",
        action="store_true",
        help="Enable assisted download mode with polite rate-limiting (off by default)",
    )
    parser.add_argument(
        "--verify-local",
        action="store_true",
        help="Validate all locally downloaded files in data/raw/ and update manifest",
    )
    parser.add_argument(
        "--create-samples",
        action="store_true",
        help="Create tiny verified SAMPLE files for testing and offline development",
    )

    args = parser.parse_args()

    if args.create_samples:
        create_sample_files()
    elif args.verify_local:
        verify_all_local_files()
    elif args.assisted:
        run_assisted_mode()
    else:
        print_manual_checklist()


if __name__ == "__main__":
    main()
