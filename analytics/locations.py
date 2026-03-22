"""
Location-level analytics.
"""

from __future__ import annotations
import pandas as pd


def location_ranking(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Top-N locations by paid revenue and order count."""
    paid = df[df["is_paid"]]
    return (
        paid.groupby("machine_name")
        .agg(revenue=("total_price", "sum"), orders=("order_id", "count"))
        .assign(aov=lambda x: x["revenue"] / x["orders"])
        .sort_values("revenue", ascending=False)
        .head(top_n)
        .reset_index()
    )


def location_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot: machine_name × day_name → total orders.
    Used for a location × day-of-week heatmap.
    """
    completed = df[df["order_status"] == "completed"]
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = (
        completed.groupby(["machine_name", "day_name"])
        .size()
        .reset_index(name="orders")
        .pivot(index="machine_name", columns="day_name", values="orders")
        .fillna(0)
        .reindex(columns=day_order)
    )
    return pivot


def location_trend(df: pd.DataFrame, freq: str = "W", top_n: int = 10) -> pd.DataFrame:
    """Weekly order volume for the top-N locations."""
    top_locations = (
        df[df["is_paid"]]
        .groupby("machine_name")["total_price"]
        .sum()
        .nlargest(top_n)
        .index.tolist()
    )
    sub = df[df["machine_name"].isin(top_locations) & df["is_paid"]].copy()
    sub = sub.set_index("timestamp")
    trend = (
        sub.groupby([pd.Grouper(freq=freq), "machine_name"])["total_price"]
        .sum()
        .reset_index()
        .rename(columns={"timestamp": "period", "total_price": "revenue"})
    )
    return trend


def failed_rate(df: pd.DataFrame) -> pd.DataFrame:
    """Failed order rate per location (app orders only, where failures can occur)."""
    app_df = df[df["order_type"] == "app"]
    total = app_df.groupby("machine_name").size().rename("total")
    failed = (
        app_df[app_df["order_status"] == "failed"]
        .groupby("machine_name")
        .size()
        .rename("failed")
    )
    result = pd.concat([total, failed], axis=1).fillna(0)
    result["fail_rate"] = result["failed"] / result["total"]
    return result.sort_values("fail_rate", ascending=False).reset_index()
