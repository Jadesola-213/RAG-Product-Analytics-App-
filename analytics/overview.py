"""
Overview analytics: top-level KPIs and trend data consumed by the Overview tab.
"""

from __future__ import annotations
import pandas as pd
from config import CURRENCY


def compute_kpis(df: pd.DataFrame) -> dict:
    """Return a dict of scalar KPIs for the KPI card row."""
    paid = df[df["is_paid"]]
    completed = df[df["order_status"] == "completed"]

    total_revenue   = paid["total_price"].sum()
    total_orders    = len(completed)
    paid_orders     = len(paid)
    aov             = paid["total_price"].mean() if paid_orders else 0
    loyalty_orders  = df["is_loyalty"].sum()
    maintainer_orders = df["is_maintainer"].sum()
    failed_orders   = (df["order_status"] == "failed").sum()
    cancelled_orders = (df["order_status"] == "cancelled").sum()
    kiosk_orders    = (df["order_type"] == "kiosk").sum()
    app_orders      = (df["order_type"] == "app").sum()
    unique_locations = df["machine_name"].nunique()
    unique_products  = df["product"].nunique()
    date_range_days  = (df["timestamp"].max() - df["timestamp"].min()).days

    # App-specific: avg fulfillment time
    app_df = df[(df["order_type"] == "app") & df["fulfillment_seconds"].notna()]
    avg_fulfillment = app_df["fulfillment_seconds"].mean() if len(app_df) else None

    return {
        "total_revenue":      total_revenue,
        "total_orders":       total_orders,
        "paid_orders":        paid_orders,
        "aov":                aov,
        "loyalty_orders":     int(loyalty_orders),
        "maintainer_orders":  int(maintainer_orders),
        "failed_orders":      int(failed_orders),
        "cancelled_orders":   int(cancelled_orders),
        "kiosk_orders":       int(kiosk_orders),
        "app_orders":         int(app_orders),
        "unique_locations":   int(unique_locations),
        "unique_products":    int(unique_products),
        "date_range_days":    int(date_range_days),
        "avg_fulfillment_sec": avg_fulfillment,
    }


def revenue_trend(df: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    """
    Aggregate paid revenue by *freq* ('D' = daily, 'W' = weekly, 'ME' = monthly).
    Returns a DataFrame with columns [period, revenue, orders].
    """
    paid = df[df["is_paid"]].copy()
    paid = paid.set_index("timestamp")
    agg = paid.resample(freq).agg(
        revenue=("total_price", "sum"),
        orders=("order_id", "count"),
    ).reset_index()
    agg = agg.rename(columns={"timestamp": "period"})
    return agg


def channel_split(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue and order count split by kiosk vs app."""
    paid = df[df["is_paid"]]
    return (
        paid.groupby("order_type")
        .agg(revenue=("total_price", "sum"), orders=("order_id", "count"))
        .reset_index()
    )
