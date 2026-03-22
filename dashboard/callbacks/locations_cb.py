"""
Locations tab callbacks.
"""

import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output

from dashboard.app_instance import app
from analytics.locations import location_ranking, location_heatmap, location_trend, failed_rate
from config import PLOTLY_TEMPLATE, CHART_COLORS, BRAND, CURRENCY

import store


def _dark_layout(**kwargs):
    return dict(
        paper_bgcolor=BRAND["card"], plot_bgcolor=BRAND["card"],
        font_color=BRAND["text"], margin=dict(l=10, r=10, t=40, b=10),
        **kwargs,
    )


@app.callback(
    Output("location-ranking-bar", "figure"),
    Output("failed-rate-chart",    "figure"),
    Output("location-heatmap",     "figure"),
    Output("location-trend-chart", "figure"),
    Input("main-tabs", "active_tab"),
)
def update_locations(_tab):
    df = store.DF

    # 1. Top locations bar
    lr = location_ranking(df, top_n=15)
    fig1 = px.bar(
        lr, x="revenue", y="machine_name", orientation="h",
        color="revenue", color_continuous_scale=["#3E1A00", "#D2691E", "#FFD700"],
        text=lr["revenue"].apply(lambda v: f"{CURRENCY}{v:,.0f}"),
        labels={"revenue": f"Revenue ({CURRENCY})", "machine_name": ""},
    )
    fig1.update_traces(textposition="outside")
    fig1.update_layout(title="Top 15 Locations by Revenue", showlegend=False,
                       coloraxis_showscale=False, template=PLOTLY_TEMPLATE, **_dark_layout())

    # 2. Failed order rate (app orders)
    fr = failed_rate(df).head(12)
    fig2 = px.bar(
        fr[fr["failed"] > 0], x="fail_rate", y="machine_name", orientation="h",
        color="fail_rate",
        color_continuous_scale=["#FFD700", "#E53935"],
        text=fr[fr["failed"] > 0]["fail_rate"].apply(lambda v: f"{v*100:.1f}%"),
        labels={"fail_rate": "Fail Rate", "machine_name": ""},
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(title="App Order Fail Rate by Location", showlegend=False,
                       coloraxis_showscale=False, template=PLOTLY_TEMPLATE, **_dark_layout())

    # 3. Location × day-of-week heatmap
    hm = location_heatmap(df)
    fig3 = go.Figure(go.Heatmap(
        z=hm.values,
        x=hm.columns.tolist(),
        y=hm.index.tolist(),
        colorscale=[[0, "#1A1A1A"], [0.5, "#8B4513"], [1, "#FFD700"]],
        hoverongaps=False,
    ))
    fig3.update_layout(title="Orders: Location × Day of Week",
                       template=PLOTLY_TEMPLATE, height=700,
                       xaxis_side="top", **_dark_layout())

    # 4. Top-10 location trend
    lt = location_trend(df, freq="W", top_n=10)
    fig4 = px.line(
        lt, x="period", y="revenue", color="machine_name",
        color_discrete_sequence=CHART_COLORS,
        labels={"revenue": f"Revenue ({CURRENCY})", "period": "", "machine_name": "Location"},
    )
    fig4.update_layout(title="Top 10 Locations — Weekly Revenue Trend",
                       template=PLOTLY_TEMPLATE, **_dark_layout())

    return fig1, fig2, fig3, fig4
