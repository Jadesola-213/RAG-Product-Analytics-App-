"""
Overview tab callbacks: KPI cards, revenue trend, channel split, order volume.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from dash import Input, Output, html
import dash_bootstrap_components as dbc

from dashboard.app_instance import app
from dashboard.components import kpi_card
from analytics.overview import compute_kpis, revenue_trend, channel_split
from config import CURRENCY, PLOTLY_TEMPLATE, CHART_COLORS, BRAND

import store  # module-level DF


def _dark_layout(**kwargs):
    return dict(
        paper_bgcolor=BRAND["card"],
        plot_bgcolor=BRAND["card"],
        font_color=BRAND["text"],
        margin=dict(l=10, r=10, t=40, b=10),
        **kwargs,
    )


@app.callback(
    Output("kpi-row", "children"),
    Input("main-tabs", "active_tab"),
)
def update_kpis(_tab):
    df   = store.DF
    kpis = compute_kpis(df)

    def fmt_secs(s):
        if s is None: return "N/A"
        return f"{s/60:.1f} min"

    cards = [
        kpi_card("Total Revenue",    f"{CURRENCY}{kpis['total_revenue']:,.2f}",
                 f"{kpis['date_range_days']} day period"),
        kpi_card("Total Orders",     f"{kpis['total_orders']:,}",
                 f"{kpis['paid_orders']:,} paid"),
        kpi_card("Avg Order Value",  f"{CURRENCY}{kpis['aov']:.2f}",
                 "paid orders"),
        kpi_card("Locations",        str(kpis['unique_locations']),
                 f"{kpis['unique_products']} products", icon="📍"),
        kpi_card("Loyalty Orders",   f"{kpis['loyalty_orders']:,}",
                 "free cups dispensed", icon="💚"),
        kpi_card("Avg Fulfillment",  fmt_secs(kpis['avg_fulfillment_sec']),
                 "app orders only", icon="⚡"),
    ]

    return [
        dbc.Col(card, xs=12, sm=6, md=4, lg=2)
        for card in cards
    ]


@app.callback(
    Output("revenue-trend-chart", "figure"),
    Output("order-volume-chart",  "figure"),
    Input("overview-freq", "value"),
)
def update_revenue_trend(freq):
    df   = store.DF
    trend = revenue_trend(df, freq)

    # Revenue
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=trend["period"], y=trend["revenue"],
        mode="lines+markers",
        line=dict(color=BRAND["secondary"], width=2.5),
        marker=dict(size=4),
        fill="tozeroy",
        fillcolor="rgba(210,105,30,0.15)",
        name="Revenue",
    ))
    fig1.update_layout(
        title="Revenue Over Time",
        xaxis_title="", yaxis_title=f"Revenue ({CURRENCY})",
        template=PLOTLY_TEMPLATE,
        **_dark_layout(),
    )

    # Volume
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=trend["period"], y=trend["orders"],
        marker_color=BRAND["primary"],
        name="Orders",
    ))
    fig2.update_layout(
        title="Order Volume Over Time",
        xaxis_title="", yaxis_title="Number of Orders",
        template=PLOTLY_TEMPLATE,
        **_dark_layout(),
    )

    return fig1, fig2


@app.callback(
    Output("channel-split-chart", "figure"),
    Input("main-tabs", "active_tab"),
)
def update_channel_split(_tab):
    df  = store.DF
    ch  = channel_split(df)
    fig = px.pie(
        ch, names="order_type", values="revenue",
        color_discrete_sequence=[BRAND["secondary"], BRAND["primary"]],
        hole=0.45,
    )
    fig.update_layout(
        title="Revenue by Channel",
        template=PLOTLY_TEMPLATE,
        **_dark_layout(),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    return fig
