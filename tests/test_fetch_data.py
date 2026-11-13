"""
Unit tests for scripts/fetch_data.py (Offline Data Fetch & Validation Helper)
ASTRAQUANT X 2026
"""

import csv
import io
import sys
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error

import pytest

# Ensure scripts folder is importable for test runner
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import fetch_data


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_compute_sha256(temp_dir: Path):
    test_file = temp_dir / "test_hash.txt"
    test_file.write_text("AlphaWatch AI Deterministic SHA256", encoding="utf-8")
    
    # Pre-calculated SHA-256 for this exact string
    digest = fetch_data.compute_sha256(test_file)
    assert isinstance(digest, str)
    assert len(digest) == 64


def test_safe_extract_zip_legitimate(temp_dir: Path):
    zip_path = temp_dir / "legit.zip"
    extract_target = temp_dir / "extracted"
    
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("data/sample.csv", "Date,Close\n2026-10-30,2800.00\n")
    
    extracted = fetch_data.safe_extract_zip(zip_path, extract_target)
    assert len(extracted) == 1
    assert extracted[0].exists()
    assert extracted[0].read_text(encoding="utf-8").startswith("Date,Close")


def test_safe_extract_zip_path_traversal_rejection(temp_dir: Path):
    zip_path = temp_dir / "malicious.zip"
    extract_target = temp_dir / "safe_box"
    
    with zipfile.ZipFile(zip_path, "w") as zf:
        # Zip slip attack path
        zf.writestr("../escaped.txt", "Pwned")
    
    with pytest.raises(ValueError, match="Path traversal attempt detected"):
        fetch_data.safe_extract_zip(zip_path, extract_target)


def test_safe_extract_zip_executable_rejection(temp_dir: Path):
    zip_path = temp_dir / "executable.zip"
    extract_target = temp_dir / "safe_box"
    
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("trojan.exe", "MZ...")
    
    with pytest.raises(ValueError, match="Executable content .* rejected"):
        fetch_data.safe_extract_zip(zip_path, extract_target)


def test_validate_csv_file_empty(temp_dir: Path):
    empty_file = temp_dir / "empty.csv"
    empty_file.write_text("", encoding="utf-8")
    
    res = fetch_data.validate_file(empty_file)
    assert not res.is_valid
    assert "0 bytes" in (res.error_message or "")


def test_validate_csv_bhavcopy_udiff(temp_dir: Path):
    bhav_file = temp_dir / "SAMPLE_bhavcopy.csv"
    content = (
        "TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,OpnPric,HghPric,LwPric,ClsPric,LastPric,PrvsClsgPric,TtlTradgVol,TtlTrfVal,TtlNbOfTxsExctd\n"
        "2026-10-30,2026-10-30,CM,NSE,STK,1,INE002A01018,RELIANCE,EQ,2800.00,2850.00,2790.00,2835.50,2836.00,2795.00,5200000,14700000000,150000\n"
    )
    bhav_file.write_text(content, encoding="utf-8")
    
    res = fetch_data.validate_file(bhav_file)
    assert res.is_valid
    assert res.row_count == 1
    assert "Bhavcopy" in (res.report_type or "")
    assert res.date_range == "2026-10-30"


def test_validate_csv_nifty50_history(temp_dir: Path):
    nifty_file = temp_dir / "SAMPLE_nifty50.csv"
    content = (
        "Date,Open,High,Low,Close,Shares Traded,Turnover (₹ Cr)\n"
        "2026-10-28,24200.00,24350.00,24150.00,24300.00,280000000,25000.00\n"
        "2026-10-29,24320.00,24410.00,24280.00,24380.00,295000000,26500.00\n"
    )
    nifty_file.write_text(content, encoding="utf-8")
    
    res = fetch_data.validate_file(nifty_file)
    assert res.is_valid
    assert res.row_count == 2
    assert res.date_range == "2026-10-28 to 2026-10-29"


def test_validate_excel_valid_and_invalid(temp_dir: Path):
    # Invalid excel (corrupted text)
    bad_xlsx = temp_dir / "bad.xlsx"
    bad_xlsx.write_text("Not an openxml archive", encoding="utf-8")
    bad_res = fetch_data.validate_file(bad_xlsx)
    assert not bad_res.is_valid
    assert "Not a valid OpenXML Excel workbook" in (bad_res.error_message or "")

    # Valid openxml zip container
    good_xlsx = temp_dir / "SAMPLE_stock.xlsx"
    with zipfile.ZipFile(good_xlsx, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types/>')
        zf.writestr("xl/workbook.xml", '<workbook><sheets><sheet name="Data Sheet" sheetId="1"/></sheets></workbook>')
    
    good_res = fetch_data.validate_file(good_xlsx)
    assert good_res.is_valid
    assert good_res.report_type == "Screener.in Financial Workbook"


def test_manifest_recording_and_deduplication(temp_dir: Path):
    manifest_path = temp_dir / "data_manifest.csv"
    
    # First write
    fetch_data.append_to_manifest(
        source="NSE India",
        url="https://example.com/file1.csv",
        report_name="Bhavcopy",
        file_name="file1.csv",
        rows=100,
        date_range="2026-10-01 to 2026-10-30",
        sha256_hash="abcdef123456",
        manifest_path=manifest_path,
    )
    
    # Second write for same file_name (update/deduplicate)
    fetch_data.append_to_manifest(
        source="NSE India",
        url="https://example.com/file1.csv",
        report_name="Bhavcopy Final",
        file_name="file1.csv",
        rows=150,
        date_range="2026-10-01 to 2026-10-31",
        sha256_hash="fedcba654321",
        manifest_path=manifest_path,
    )
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 1
        assert reader[0]["file_name"] == "file1.csv"
        assert reader[0]["rows"] == "150"
        assert reader[0]["sha256"] == "fedcba654321"


def test_polite_download_stops_on_403(temp_dir: Path):
    destination = temp_dir / "out.csv"
    
    # Mock urlopen to raise HTTP 403 Forbidden
    err = urllib.error.HTTPError(
        url="https://example.com/blocked",
        code=403,
        msg="Forbidden",
        hdrs=MagicMock(),
        fp=io.BytesIO(b"Access Denied"),
    )
    
    with patch("urllib.request.urlopen", side_effect=err):
        success = fetch_data.polite_download(
            url="https://example.com/blocked",
            destination=destination,
            max_retries=3,
            min_delay=0.01,
        )
        assert success is False
        assert not destination.exists()


def test_create_sample_files(temp_dir: Path, monkeypatch):
    # Redirect global directories to temp_dir
    monkeypatch.setattr(fetch_data, "DIR_RAW_NSE", temp_dir / "nse")
    monkeypatch.setattr(fetch_data, "DIR_RAW_SCREENER", temp_dir / "screener")
    monkeypatch.setattr(fetch_data, "DIR_PROCESSED", temp_dir / "processed")
    monkeypatch.setattr(fetch_data, "MANIFEST_PATH", temp_dir / "processed" / "data_manifest.csv")
    
    fetch_data.create_sample_files()
    
    assert (temp_dir / "nse" / "SAMPLE_bhavcopy_udiff.csv").exists()
    assert (temp_dir / "nse" / "SAMPLE_NIFTY50_historical.csv").exists()
    assert (temp_dir / "nse" / "SAMPLE_India_VIX_historical.csv").exists()
    assert (temp_dir / "nse" / "SAMPLE_delivery_data.csv").exists()
    assert (temp_dir / "screener" / "SAMPLE_RELIANCE.xlsx").exists()
    assert (temp_dir / "processed" / "data_manifest.csv").exists()
