"""
Time-based analytics: hourly, daily, weekly patterns and session breakdowns.
"""

from __future__ import annotations
import pandas as pd


def hourly_pattern(df: pd.DataFrame) -> pd.DataFrame:
    """Average orders per hour-of-day."""
    completed = df[df["order_status"] == "completed"]
    total_days = completed["date"].nunique()
    hourly = (
        completed.groupby("hour")
        .size()
        .reset_index(name="total_orders")
    )
    hourly["avg_per_day"] = hourly["total_orders"] / max(total_days, 1)
    return hourly.sort_values("hour")


def dow_pattern(df: pd.DataFrame) -> pd.DataFrame:
    """Average orders per day-of-week."""
    completed = df[df["order_status"] == "completed"]
    day_order  = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    dow = (
        completed.groupby(["day_of_week", "day_name"])
        .agg(orders=("order_id", "count"), revenue=("revenue", "sum"))
        .reset_index()
        .sort_values("day_of_week")
    )
    # average per occurrence of each weekday
    weeks_seen = completed.groupby("day_of_week")["date"].nunique().reset_index(name="n_days")
    dow = dow.merge(weeks_seen, on="day_of_week")
    dow["avg_orders"]  = dow["orders"]  / dow["n_days"]
    dow["avg_revenue"] = dow["revenue"] / dow["n_days"]
    dow["day_name"] = pd.Categorical(dow["day_name"], categories=day_order, ordered=True)
    return dow.sort_values("day_name")


def hour_dow_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot: hour (0-23) × day_name → total orders.
    Used for a 2D heatmap chart.
    """
    completed = df[df["order_status"] == "completed"]
    day_order  = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    pivot = (
        completed.groupby(["hour", "day_name"])
        .size()
        .reset_index(name="orders")
        .pivot(index="hour", columns="day_name", values="orders")
        .fillna(0)
        .reindex(columns=day_order)
        .reindex(range(24))
        .fillna(0)
    )
    return pivot


def session_split(df: pd.DataFrame) -> pd.DataFrame:
    """Order count and revenue per time-of-day session."""
    completed = df[df["order_status"] == "completed"]
    session_order = ["Morning", "Midday", "Afternoon", "Evening", "Night"]
    result = (
        completed.groupby("session")
        .agg(orders=("order_id", "count"), revenue=("revenue", "sum"))
        .reindex(session_order)
        .fillna(0)
        .reset_index()
    )
    return result
