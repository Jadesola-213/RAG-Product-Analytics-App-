"""
Generate a list of plain-English text chunks from the orders DataFrame.
These chunks become the knowledge base embedded by the RAG retriever.
"""

from __future__ import annotations
import pandas as pd
from config import CHUNK_SIZE, CURRENCY


def _chunk(text: str, max_len: int = CHUNK_SIZE) -> list[str]:
    """Split long text into sub-chunks of at most max_len characters."""
    if len(text) <= max_len:
        return [text.strip()]
    # naive sentence-level split
    sentences = text.replace("\n", " ").split(". ")
    chunks, current = [], ""
    for s in sentences:
        if len(current) + len(s) + 2 <= max_len:
            current += s + ". "
        else:
            if current:
                chunks.append(current.strip())
            current = s + ". "
    if current:
        chunks.append(current.strip())
    return chunks


def build_knowledge_base(df: pd.DataFrame) -> list[str]:
    """Return a list of grounded text chunks derived from *df*."""
    docs: list[str] = []

    paid      = df[df["is_paid"]]
    completed = df[df["order_status"] == "completed"]

    # 1. Overall summary
    total_rev   = paid["total_price"].sum()
    total_units = len(completed)
    date_min    = df["timestamp"].min().strftime("%d %b %Y")
    date_max    = df["timestamp"].max().strftime("%d %b %Y")
    n_locations = df["machine_name"].nunique()
    n_products  = df["product"].nunique()
    avg_daily_rev = total_rev / max(df["date"].nunique(), 1)

    docs.append(
        f"Jade Coffee overall summary: {total_units:,} orders between {date_min} and {date_max} "
        f"across {n_locations} machine locations. "
        f"Total revenue: {CURRENCY}{total_rev:,.2f}. "
        f"Average daily revenue: {CURRENCY}{avg_daily_rev:,.2f}. "
        f"{df['is_loyalty'].sum()} loyalty orders and {df['is_maintainer'].sum()} maintainer (free) orders. "
        f"{n_products} different products sold."
    )

    # 2. Channel split
    kiosk_cnt = (df["order_type"] == "kiosk").sum()
    app_cnt   = (df["order_type"] == "app").sum()
    kiosk_rev = paid[paid["order_type"] == "kiosk"]["total_price"].sum()
    app_rev   = paid[paid["order_type"] == "app"]["total_price"].sum()
    docs.append(
        f"Order channel breakdown: {kiosk_cnt:,} kiosk orders ({CURRENCY}{kiosk_rev:,.2f} revenue) "
        f"and {app_cnt:,} app orders ({CURRENCY}{app_rev:,.2f} revenue). "
        f"Kiosk accounts for {kiosk_cnt/(kiosk_cnt+app_cnt)*100:.1f}% of all orders."
    )

    # 3. Product summaries
    prod_stats = (
        paid.groupby("product")
        .agg(revenue=("total_price", "sum"), units=("order_id", "count"))
        .assign(aov=lambda x: x["revenue"] / x["units"])
        .sort_values("revenue", ascending=False)
    )
    for product, row in prod_stats.iterrows():
        docs.append(
            f"Product '{product}': {int(row['units']):,} paid orders, "
            f"total revenue {CURRENCY}{row['revenue']:,.2f}, "
            f"average price {CURRENCY}{row['aov']:.2f}."
        )

    # 4. Location summaries
    loc_stats = (
        paid.groupby("machine_name")
        .agg(revenue=("total_price", "sum"), orders=("order_id", "count"))
        .sort_values("revenue", ascending=False)
    )

    # Ranking summary (key for "top location" queries)
    top5 = loc_stats.head(5)
    top5_text = "; ".join(
        f"#{i+1} {loc} ({CURRENCY}{row['revenue']:,.2f})"
        for i, (loc, row) in enumerate(top5.iterrows())
    )
    bottom5 = loc_stats.tail(5)
    bot5_text = "; ".join(
        f"{loc} ({CURRENCY}{row['revenue']:,.2f})"
        for loc, row in bottom5.iterrows()
    )
    docs.append(
        f"Top 5 locations by revenue: {top5_text}. "
        f"Lowest 5 locations by revenue: {bot5_text}."
    )
    docs.append(
        f"The highest-revenue location is '{loc_stats.index[0]}' with "
        f"{CURRENCY}{loc_stats.iloc[0]['revenue']:,.2f} from {int(loc_stats.iloc[0]['orders']):,} orders. "
        f"The lowest-revenue location is '{loc_stats.index[-1]}' with "
        f"{CURRENCY}{loc_stats.iloc[-1]['revenue']:,.2f} from {int(loc_stats.iloc[-1]['orders']):,} orders."
    )

    for loc, row in loc_stats.iterrows():
        docs.append(
            f"Location '{loc}': {int(row['orders']):,} paid orders, "
            f"revenue {CURRENCY}{row['revenue']:,.2f}."
        )

    # 5. Weekly aggregates
    weekly = (
        paid.groupby(paid["timestamp"].dt.to_period("W"))["total_price"].sum()
    )
    weekly_texts = []
    for period, rev in weekly.items():
        weekly_texts.append(f"week of {period.start_time.strftime('%d %b %Y')}: {CURRENCY}{rev:,.2f} revenue")
    docs.extend(_chunk("Weekly revenue breakdown — " + "; ".join(weekly_texts) + "."))

    # 6. Daily summaries
    daily_rev = paid.groupby("date")["total_price"].sum()
    daily_cnt = completed.groupby("date").size()
    top_prod  = (
        paid.groupby(["date", "product"]).size()
        .reset_index(name="cnt")
        .sort_values("cnt", ascending=False)
        .groupby("date")
        .first()["product"]
    )
    for date in daily_rev.index:
        rev  = daily_rev.get(date, 0)
        cnt  = daily_cnt.get(date, 0)
        prod = top_prod.get(date, "unknown")
        docs.append(
            f"On {pd.Timestamp(date).strftime('%A %d %b %Y')}: "
            f"{int(cnt)} orders, {CURRENCY}{rev:.2f} revenue, top product: {prod}."
        )

    # 7. Time-of-day patterns
    session_rev = (
        paid.groupby("session")["total_price"].sum().sort_values(ascending=False)
    )
    session_text = "; ".join(
        f"{s}: {CURRENCY}{r:,.2f}" for s, r in session_rev.items()
    )
    docs.append(f"Revenue by time of day session — {session_text}.")

    hour_cnt = completed.groupby("hour").size().sort_values(ascending=False)
    peak_hours = hour_cnt.head(3).index.tolist()
    docs.append(
        f"Peak order hours are {peak_hours} (24h clock). "
        f"Hour {peak_hours[0]}:00 is the busiest with {hour_cnt.iloc[0]:,} total orders."
    )

    # 8. Day-of-week patterns
    dow_rev = paid.groupby("day_name")["total_price"].sum().sort_values(ascending=False)
    dow_text = "; ".join(f"{d}: {CURRENCY}{r:,.2f}" for d, r in dow_rev.items())
    docs.append(f"Revenue by day of week — {dow_text}.")

    # 9. Failed / cancelled orders
    failed_cnt    = (df["order_status"] == "failed").sum()
    cancelled_cnt = (df["order_status"] == "cancelled").sum()
    docs.append(
        f"Order reliability: {failed_cnt} failed orders and {cancelled_cnt} cancelled orders "
        f"out of {len(df):,} total ({(failed_cnt+cancelled_cnt)/len(df)*100:.1f}% failure/cancel rate)."
    )

    # 10. App fulfillment time
    app_df = df[(df["order_type"] == "app") & df["fulfillment_seconds"].notna() & (df["fulfillment_seconds"] > 0)]
    if len(app_df) > 0:
        avg_secs = app_df["fulfillment_seconds"].mean()
        docs.append(
            f"App order fulfillment: average time from order to completion is "
            f"{avg_secs/60:.1f} minutes ({int(avg_secs)} seconds)."
        )

    return docs
