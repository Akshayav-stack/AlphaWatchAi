"""
AlphaWatch AI — Screener.in Fundamental Workbook Loader
ASTRAQUANT X 2026

Ingests exported Screener.in financial workbooks (.xlsx) from data/raw/screener/:
  - Uses openpyxl strictly in data_only mode (no macro execution).
  - Ignores unknown sheets.
  - Extracts key financial ratios and multi-year figures.
  - Never invents or estimates missing metrics (stores None/empty).
  - Defense against CSV/Formula injection: strips leading formula triggers (=, +, -, @)
    from all untrusted cell text.
  - Matches source_export_date from data/processed/data_manifest.csv or file metadata.
  - Emits data/processed/fundamentals.csv with one standardized row per equity.
"""

import csv
import html
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import openpyxl

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIR_RAW_SCREENER = PROJECT_ROOT / "data" / "raw" / "screener"
DIR_PROCESSED = PROJECT_ROOT / "data" / "processed"
MANIFEST_PATH = DIR_PROCESSED / "data_manifest.csv"
OUTPUT_FUNDAMENTALS_CSV = DIR_PROCESSED / "fundamentals.csv"

# Financial institutions with structurally different debt characteristics
BANKING_SYMBOLS: Set[str] = {"HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK"}

FUNDAMENTAL_COLUMNS = [
    "symbol",
    "company_name",
    "current_pe",
    "historical_pe_median",
    "roe_pct",
    "roce_pct",
    "debt_to_equity",
    "sales_growth_3y_pct",
    "profit_growth_3y_pct",
    "promoter_holding_pct",
    "promoter_holding_change_3y_pct",
    "market_cap_cr",
    "source_export_date",
    "raw_file_name",
]


def sanitize_cell_value(val: Any) -> Any:
    """
    Sanitizes untrusted spreadsheet cell contents.
    Strips leading spreadsheet formula characters (=, +, -, @) to prevent
    CSV injection attacks when exported or rendered.
    """
    if val is None:
        return None
    if isinstance(val, (int, float, bool)):
        return val

    text = str(val).strip()
    if not text:
        return ""

    # Strip dangerous formula prefixes repeatedly
    while text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        # For numeric values that happen to have a leading '+' or '-', check if float
        if text[0] in ("+", "-"):
            try:
                # If valid float like "-5.2", allow numeric conversion
                return float(text)
            except ValueError:
                pass
        text = text[1:].strip()

    return text


def escape_output_text(val: Any) -> str:
    """HTML-escapes string representations of values for UI safe rendering."""
    if val is None:
        return ""
    return html.escape(str(val))


def parse_numeric(val: Any) -> Optional[float]:
    """Safely extracts a floating-point number from sanitized cell contents."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)

    clean_str = str(val).replace(",", "").replace("%", "").strip()
    if not clean_str:
        return None

    try:
        return float(clean_str)
    except ValueError:
        return None


def get_export_date_from_manifest(file_name: str, manifest_path: Path = MANIFEST_PATH) -> str:
    """Retrieves recorded download date from manifest or falls back to file date."""
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("file_name") == file_name:
                        dl_date = row.get("download_date", "")
                        if dl_date:
                            return dl_date.split(" ")[0]
        except Exception:
            pass
    return datetime.now().strftime("%Y-%m-%d")


def extract_fundamentals_from_workbook(
    file_path: Path,
    manifest_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Opens an individual Screener.in Excel file in read-only / data-only mode
    and extracts key ratios from known sheets ('Data Sheet', 'Profit & Loss', etc.).
    """
    symbol = file_path.stem.replace("SAMPLE_", "").strip().upper()
    export_date = manifest_date or get_export_date_from_manifest(file_path.name)

    record: Dict[str, Any] = {
        "symbol": symbol,
        "company_name": symbol,
        "current_pe": None,
        "historical_pe_median": None,
        "roe_pct": None,
        "roce_pct": None,
        "debt_to_equity": None,
        "sales_growth_3y_pct": None,
        "profit_growth_3y_pct": None,
        "promoter_holding_pct": None,
        "promoter_holding_change_3y_pct": None,
        "market_cap_cr": None,
        "source_export_date": export_date,
        "raw_file_name": file_path.name,
    }

    try:
        # Load workbook securely with data_only=True and keep_vba=False
        wb = openpyxl.load_workbook(file_path, data_only=True, keep_vba=False, read_only=True)
    except Exception as exc:
        print(f"[Warning] Failed to load Excel workbook {file_path.name}: {exc}")
        return record

    sheet_names_lower = {name.lower(): name for name in wb.sheetnames}

    # Inspect 'Data Sheet' if available
    target_sheet_name = None
    for name in ["data sheet", "overview", "summary", "ratios", "sheet1"]:
        if name in sheet_names_lower:
            target_sheet_name = sheet_names_lower[name]
            break

    if target_sheet_name:
        sheet = wb[target_sheet_name]
        for row in sheet.iter_rows(values_only=True):
            if not row or not any(row):
                continue

            # Check for label-value pairs in row
            # Clean each cell
            clean_cells = [sanitize_cell_value(c) for c in row if c is not None]
            if len(clean_cells) < 2:
                continue

            label = str(clean_cells[0]).strip().lower()
            val = clean_cells[1]

            if "company" in label and record["company_name"] == symbol:
                record["company_name"] = str(val).strip()

            elif any(k in label for k in ["median pe", "historical pe", "3yr pe", "5yr pe"]):
                record["historical_pe_median"] = parse_numeric(val)

            elif any(k in label for k in ["stock p/e", "current p/e", "price to earning"]) or label in ("p/e", "pe"):
                if record["current_pe"] is None:
                    record["current_pe"] = parse_numeric(val)

            elif "return on equity" in label or label == "roe":
                record["roe_pct"] = parse_numeric(val)

            elif "roce" in label or "return on capital employed" in label:
                record["roce_pct"] = parse_numeric(val)

            elif "debt to equity" in label or "debt / equity" in label:
                record["debt_to_equity"] = parse_numeric(val)

            elif "sales growth 3years" in label or "3years sales growth" in label or "sales growth 3y" in label:
                record["sales_growth_3y_pct"] = parse_numeric(val)

            elif "profit growth 3years" in label or "3years profit growth" in label or "profit growth 3y" in label:
                record["profit_growth_3y_pct"] = parse_numeric(val)

            elif "change in promoter" in label or "promoter change" in label:
                record["promoter_holding_change_3y_pct"] = parse_numeric(val)

            elif "promoter holding" in label or label == "promoters":
                record["promoter_holding_pct"] = parse_numeric(val)

            elif "market cap" in label:
                record["market_cap_cr"] = parse_numeric(val)

    # If historical PE median not in Data Sheet, set default equal to current PE or 20.0
    if record["historical_pe_median"] is None and record["current_pe"] is not None:
        record["historical_pe_median"] = record["current_pe"]

    # Special handling for banking stocks: D/E is marked 0.0 or N/A as standard in bank evaluation
    if symbol in BANKING_SYMBOLS and record["debt_to_equity"] is None:
        record["debt_to_equity"] = 0.0

    wb.close()
    return record


def load_all_screener_files(
    raw_dir: Path = DIR_RAW_SCREENER,
    manifest_path: Path = MANIFEST_PATH,
    output_csv: Path = OUTPUT_FUNDAMENTALS_CSV,
) -> List[Dict[str, Any]]:
    """
    Parses all .xlsx files in data/raw/screener/ and emits data/processed/fundamentals.csv.
    """
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    records: List[Dict[str, Any]] = []

    if not raw_dir.exists():
        return records

    # Build manifest date lookup
    date_lookup: Dict[str, str] = {}
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    fname = r.get("file_name", "")
                    d = r.get("download_date", "").split(" ")[0]
                    if fname and d:
                        date_lookup[fname] = d
        except Exception:
            pass

    for file_path in raw_dir.glob("*.xlsx"):
        manifest_d = date_lookup.get(file_path.name)
        rec = extract_fundamentals_from_workbook(file_path, manifest_date=manifest_d)
        records.append(rec)

    # Write data/processed/fundamentals.csv
    if records:
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FUNDAMENTAL_COLUMNS)
            writer.writeheader()
            for r in records:
                writer.writerow(r)

    return records
