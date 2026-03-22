"""
Prepare daily time series DataFrames from the enriched orders DataFrame.

Three targets:
  - 'revenue' : sum of paid revenue per day
  - 'units'   : count of completed orders per day
  - 'location': count of completed orders per day for a specific location
"""

from __future__ import annotations
import pandas as pd


def prepare_daily_series(
    df: pd.DataFrame,
    target: str = "revenue",
    location: str | None = None,
) -> pd.DataFrame:
    """
    Aggregate *df* to a daily time series.

    Parameters
    ----------
    df       : enriched orders DataFrame
    target   : 'revenue' | 'units' | 'location'
    location : machine_name string (required when target == 'location')

    Returns
    -------
    DataFrame with columns ['ds', 'y'] sorted ascending, no gaps.
    Missing dates are forward-filled (or zero-filled for count targets).
    """
    if target == "location":
        if location is None:
            raise ValueError("location must be provided when target='location'")
        sub = df[df["machine_name"] == location]
        daily = (
            sub[sub["order_status"] == "completed"]
            .groupby("date")
            .size()
            .reset_index(name="y")
        )
    elif target == "revenue":
        daily = (
            df[df["is_paid"]]
            .groupby("date")["total_price"]
            .sum()
            .reset_index(name="y")
        )
    elif target == "units":
        daily = (
            df[df["order_status"] == "completed"]
            .groupby("date")
            .size()
            .reset_index(name="y")
        )
    else:
        raise ValueError(f"Unknown target: {target!r}")

    daily = daily.rename(columns={"date": "ds"})
    daily["ds"] = pd.to_datetime(daily["ds"])
    daily = daily.sort_values("ds").reset_index(drop=True)

    # Fill missing dates with 0
    full_range = pd.date_range(daily["ds"].min(), daily["ds"].max(), freq="D")
    daily = (
        daily.set_index("ds")
        .reindex(full_range)
        .rename_axis("ds")
        .reset_index()
    )
    daily["y"] = daily["y"].fillna(0)

    return daily
