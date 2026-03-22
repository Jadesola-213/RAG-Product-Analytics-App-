"""
Data cleaning pipeline.

Steps:
  1. Drop rows with unparseable timestamps.
  2. Normalise product names; remove test/invalid entries.
  3. Filter to completed orders only (configurable).
  4. Derive payment-intent flags: is_paid, is_loyalty, is_maintainer.
  5. Deduplicate by order_id.
  6. Sort chronologically.
"""

from __future__ import annotations
import logging

import pandas as pd

from config import PRODUCT_ALIASES, EXCLUDED_STATUSES

logger = logging.getLogger(__name__)


def _normalise_products(df: pd.DataFrame) -> pd.DataFrame:
    """Apply alias map; drop rows where alias resolves to None."""
    df = df.copy()
    df["product"] = df["product"].replace(PRODUCT_ALIASES)
    before = len(df)
    df = df[df["product"].notna()]
    dropped = before - len(df)
    if dropped:
        logger.info("Dropped %d rows with excluded/invalid products.", dropped)
    return df


def _derive_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Infer loyalty / maintainer / paid flags from price and raw price field."""
    df = df.copy()
    price_raw = df["product_price_raw"].fillna("").astype(str).str.lower()
    df["is_loyalty"]    = price_raw.str.contains("loyalty") | (
        (df["total_price"] == 0) & (df["order_type"] == "kiosk")
    )
    df["is_maintainer"] = price_raw.str.contains("maintainer")
    df["is_paid"]       = (~df["is_loyalty"]) & (~df["is_maintainer"]) & (df["total_price"] > 0)
    return df


def _derive_fulfillment(df: pd.DataFrame) -> pd.DataFrame:
    """Compute order fulfillment seconds for app orders."""
    df = df.copy()
    delta = df["completion_time"] - df["timestamp"]
    df["fulfillment_seconds"] = delta.dt.total_seconds().clip(lower=0)
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    n0 = len(df)

    # 1. Drop rows with no timestamp
    df = df.dropna(subset=["timestamp"])
    logger.info("After timestamp filter: %d / %d rows.", len(df), n0)

    # 2. Normalise product names
    df = _normalise_products(df)

    # 3. Filter to non-failed statuses (keep completed; flag others for metrics)
    df["is_excluded_status"] = df["order_status"].isin(EXCLUDED_STATUSES)

    # 4. Deduplicate
    before = len(df)
    df = df.drop_duplicates(subset=["order_id"])
    if len(df) < before:
        logger.info("Removed %d duplicate order_ids.", before - len(df))

    # 5. Derive flags
    df = _derive_flags(df)
    df = _derive_fulfillment(df)

    # 6. Sort
    df = df.sort_values("timestamp").reset_index(drop=True)

    logger.info("Cleaning complete: %d rows ready.", len(df))
    return df
