"""
Data ingestion: discover all Excel files in DATA_DIR,
parse Kiosk Orders + App Orders sheets, and return a single
merged raw DataFrame with a unified column schema.
"""

from __future__ import annotations
import glob
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# ── Unified output columns ────────────────────────────────────────────────────
UNIFIED_COLS = [
    "order_id", "timestamp", "machine_name", "machine_number",
    "product", "order_type", "total_price", "order_status",
    "payment_complete",
    # App-only (NaN for kiosk)
    "sent_to_machine", "completion_time", "product_price_raw",
]


def _parse_kiosk(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["order_id"]          = df["Order Number"].astype(str)
    out["timestamp"]         = pd.to_datetime(df["Order Time"], dayfirst=True, errors="coerce")
    out["machine_name"]      = df["Machine Name"].astype(str).str.strip()
    out["machine_number"]    = pd.to_numeric(df["Machine Number"], errors="coerce")
    out["product"]           = df["Products"].astype(str).str.strip()
    out["order_type"]        = "kiosk"
    out["total_price"]       = pd.to_numeric(df["Total Price"], errors="coerce")
    out["order_status"]      = df["Order Status"].astype(str).str.lower().str.strip()
    out["payment_complete"]  = df["Payment Complete"].astype(bool)
    out["sent_to_machine"]   = pd.NaT
    out["completion_time"]   = pd.NaT
    out["product_price_raw"] = pd.NA
    return out


def _parse_app(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["order_id"]          = df["Order Number"].astype(str)
    out["timestamp"]         = pd.to_datetime(df["Order Time"], dayfirst=True, errors="coerce")
    out["machine_name"]      = df["Machine Name"].astype(str).str.strip()
    out["machine_number"]    = pd.to_numeric(df["Machine Number"], errors="coerce")
    out["product"]           = df["Products"].astype(str).str.strip()
    out["order_type"]        = "app"
    out["total_price"]       = pd.to_numeric(df["Total Price"], errors="coerce")
    out["order_status"]      = df["Order Status"].astype(str).str.lower().str.strip()
    out["payment_complete"]  = df["Payment Complete"].astype(bool)
    out["sent_to_machine"]   = pd.to_datetime(
        df["Order Sent To Machine"], dayfirst=True, errors="coerce"
    )
    out["completion_time"]   = pd.to_datetime(
        df["Order Completion Time"], dayfirst=True, errors="coerce"
    )
    out["product_price_raw"] = df["Product Price"].astype(str)
    return out


def load_data(data_dir: Path) -> pd.DataFrame:
    """
    Scan *data_dir* for *.xlsx files, parse every file's
    'Kiosk Orders' and 'App Orders' sheets, and return a
    single concatenated DataFrame.
    """
    files = sorted(f for f in Path(data_dir).glob("*.xlsx") if not f.name.startswith("~$"))
    if not files:
        raise FileNotFoundError(f"No Excel files found in {data_dir}")

    frames: list[pd.DataFrame] = []
    for path in files:
        logger.info("Loading %s", path.name)
        try:
            sheets = pd.read_excel(path, sheet_name=None)
        except Exception as exc:
            logger.warning("Skipping %s — %s", path.name, exc)
            continue

        if "Kiosk Orders" in sheets:
            frames.append(_parse_kiosk(sheets["Kiosk Orders"]))
        if "App Orders" in sheets:
            frames.append(_parse_app(sheets["App Orders"]))

    if not frames:
        raise ValueError("No parseable sheets found across all files.")

    combined = pd.concat(frames, ignore_index=True)
    logger.info("Loaded %d raw rows from %d file(s).", len(combined), len(files))
    return combined
