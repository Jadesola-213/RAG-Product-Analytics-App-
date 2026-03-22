"""
Product-level analytics.
"""

from __future__ import annotations
import pandas as pd


def product_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue and unit count per product (paid orders only)."""
    paid = df[df["is_paid"]]
    return (
        paid.groupby("product")
        .agg(revenue=("total_price", "sum"), units=("order_id", "count"))
        .assign(aov=lambda x: x["revenue"] / x["units"])
        .sort_values("revenue", ascending=False)
        .reset_index()
    )


def product_volume(df: pd.DataFrame) -> pd.DataFrame:
    """Total cup volume (all orders, including free) per product."""
    return (
        df[df["order_status"] == "completed"]
        .groupby("product")
        .agg(units=("order_id", "count"))
        .sort_values("units", ascending=False)
        .reset_index()
    )


def product_trend(df: pd.DataFrame, freq: str = "W") -> pd.DataFrame:
    """Weekly revenue per product — for stacked-area chart."""
    paid = df[df["is_paid"]].copy()
    paid = paid.set_index("timestamp")
    pivot = (
        paid.groupby([pd.Grouper(freq=freq), "product"])["total_price"]
        .sum()
        .reset_index()
        .rename(columns={"timestamp": "period", "total_price": "revenue"})
    )
    return pivot


def loyalty_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """For each product, break down into paid / loyalty / maintainer counts."""
    def _label(row):
        if row["is_maintainer"]:  return "Maintainer"
        if row["is_loyalty"]:     return "Loyalty"
        return "Paid"

    df = df[df["order_status"] == "completed"].copy()
    df["payment_label"] = df.apply(_label, axis=1)
    return (
        df.groupby(["product", "payment_label"])
        .size()
        .reset_index(name="count")
    )
