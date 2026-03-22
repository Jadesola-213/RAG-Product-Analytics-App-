"""
Products tab callbacks.
"""

import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output

from dashboard.app_instance import app
from analytics.products import product_revenue, product_volume, product_trend, loyalty_ratio
from config import PLOTLY_TEMPLATE, CHART_COLORS, BRAND, CURRENCY

import store


def _dark_layout(**kwargs):
    return dict(
        paper_bgcolor=BRAND["card"], plot_bgcolor=BRAND["card"],
        font_color=BRAND["text"], margin=dict(l=10, r=10, t=40, b=10),
        **kwargs,
    )


@app.callback(
    Output("product-revenue-bar", "figure"),
    Output("product-volume-pie",  "figure"),
    Output("product-trend-area",  "figure"),
    Output("loyalty-ratio-chart", "figure"),
    Input("main-tabs", "active_tab"),
)
def update_products(_tab):
    df = store.DF

    # 1. Revenue bar
    pr = product_revenue(df)
    fig1 = px.bar(
        pr, x="revenue", y="product", orientation="h",
        color="revenue", color_continuous_scale=["#3E1A00", "#D2691E", "#FFD700"],
        text=pr["revenue"].apply(lambda v: f"{CURRENCY}{v:,.0f}"),
        labels={"revenue": f"Revenue ({CURRENCY})", "product": ""},
    )
    fig1.update_traces(textposition="outside")
    fig1.update_layout(title="Revenue by Product", showlegend=False,
                       coloraxis_showscale=False, template=PLOTLY_TEMPLATE, **_dark_layout())

    # 2. Volume pie
    pv = product_volume(df)
    fig2 = px.pie(
        pv, names="product", values="units",
        color_discrete_sequence=CHART_COLORS, hole=0.4,
    )
    fig2.update_layout(title="Unit Volume by Product", template=PLOTLY_TEMPLATE, **_dark_layout())

    # 3. Trend stacked area (weekly)
    pt = product_trend(df, freq="W")
    fig3 = px.area(
        pt, x="period", y="revenue", color="product",
        color_discrete_sequence=CHART_COLORS,
        labels={"revenue": f"Revenue ({CURRENCY})", "period": ""},
    )
    fig3.update_layout(title="Weekly Revenue Trend by Product",
                       template=PLOTLY_TEMPLATE, **_dark_layout())

    # 4. Loyalty ratio stacked bar
    lr = loyalty_ratio(df)
    fig4 = px.bar(
        lr, x="product", y="count", color="payment_label",
        color_discrete_map={"Paid": BRAND["secondary"], "Loyalty": BRAND["success"], "Maintainer": BRAND["accent"]},
        barmode="stack",
        labels={"count": "Orders", "product": "", "payment_label": "Type"},
    )
    fig4.update_layout(title="Paid vs Loyalty vs Maintainer", template=PLOTLY_TEMPLATE,
                       **_dark_layout(), xaxis_tickangle=-30)

    return fig1, fig2, fig3, fig4
