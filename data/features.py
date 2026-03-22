"""
Feature engineering layer.

Adds time-based, ordinal and rolling features to the cleaned
DataFrame so that both the analytics layer and forecasting models
can consume a single enriched DataFrame.
"""

from __future__ import annotations
import pandas as pd
import numpy as np

# UK bank holidays 2024-2025 (approximate — extend as needed)
UK_BANK_HOLIDAYS = {
    "2024-01-01", "2024-03-29", "2024-04-01", "2024-05-06",
    "2024-05-27", "2024-08-26", "2024-12-25", "2024-12-26",
    "2025-01-01", "2025-04-18", "2025-04-21", "2025-05-05",
    "2025-05-26", "2025-08-25", "2025-12-25", "2025-12-26",
}


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    ts = df["timestamp"]

    # ── Basic temporal ────────────────────────────────────────────────────────
    df["date"]         = ts.dt.normalize()
    df["hour"]         = ts.dt.hour
    df["day_of_week"]  = ts.dt.dayofweek          # 0=Mon … 6=Sun
    df["day_name"]     = ts.dt.day_name()
    df["week"]         = ts.dt.isocalendar().week.astype(int)
    df["month"]        = ts.dt.month
    df["month_name"]   = ts.dt.month_name()
    df["quarter"]      = ts.dt.quarter
    df["year"]         = ts.dt.year

    df["is_weekend"]   = df["day_of_week"] >= 5
    df["is_holiday"]   = ts.dt.date.astype(str).isin(UK_BANK_HOLIDAYS)
    df["is_peak_hour"] = df["hour"].between(7, 10) | df["hour"].between(12, 14)

    # ── Revenue / price bucket ────────────────────────────────────────────────
    df["revenue"] = df["total_price"].where(df["is_paid"], 0.0)

    bins   = [-0.01, 0.0, 2.5, 3.0, 3.5, np.inf]
    labels = ["Free", "≤£2.50", "£2.50-£3", "£3-£3.50", ">£3.50"]
    df["price_band"] = pd.cut(
        df["total_price"], bins=bins, labels=labels, right=True
    )

    # ── Session label ─────────────────────────────────────────────────────────
    def _session(h):
        if 5 <= h < 11:  return "Morning"
        if 11 <= h < 14: return "Midday"
        if 14 <= h < 18: return "Afternoon"
        if 18 <= h < 22: return "Evening"
        return "Night"

    df["session"] = df["hour"].apply(_session)

    # ── Daily rollup (convenience join key) ───────────────────────────────────
    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")

    return df
