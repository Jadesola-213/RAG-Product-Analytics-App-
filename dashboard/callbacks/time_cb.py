"""
Time Analysis tab callbacks.
"""

import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output

from dashboard.app_instance import app
from analytics.time_analysis import hourly_pattern, dow_pattern, hour_dow_heatmap, session_split
from config import PLOTLY_TEMPLATE, CHART_COLORS, BRAND, CURRENCY

import store


def _dark_layout(**kwargs):
    return dict(
        paper_bgcolor=BRAND["card"], plot_bgcolor=BRAND["card"],
        font_color=BRAND["text"], margin=dict(l=10, r=10, t=40, b=10),
        **kwargs,
    )


@app.callback(
    Output("hourly-bar",       "figure"),
    Output("dow-bar",          "figure"),
    Output("hour-dow-heatmap", "figure"),
    Output("session-pie",      "figure"),
    Input("main-tabs", "active_tab"),
)
def update_time(_tab):
    df = store.DF

    # 1. Hourly pattern
    hp = hourly_pattern(df)
    fig1 = px.bar(
        hp, x="hour", y="avg_per_day",
        color="avg_per_day",
        color_continuous_scale=["#1A1A1A", "#8B4513", "#FFD700"],
        labels={"hour": "Hour of Day", "avg_per_day": "Avg Orders / Day"},
    )
    fig1.update_layout(title="Average Orders by Hour of Day", showlegend=False,
                       coloraxis_showscale=False, template=PLOTLY_TEMPLATE, **_dark_layout())

    # 2. Day-of-week
    dp = dow_pattern(df)
    fig2 = px.bar(
        dp, x="day_name", y="avg_orders",
        color="avg_revenue",
        color_continuous_scale=["#1A1A1A", "#8B4513", "#FFD700"],
        labels={"day_name": "", "avg_orders": "Avg Orders", "avg_revenue": f"Avg Revenue ({CURRENCY})"},
    )
    fig2.update_layout(title="Average Orders by Day of Week",
                       template=PLOTLY_TEMPLATE, **_dark_layout())

    # 3. Hour × day heatmap
    hdh = hour_dow_heatmap(df)
    fig3 = go.Figure(go.Heatmap(
        z=hdh.values,
        x=hdh.columns.tolist(),
        y=[f"{h:02d}:00" for h in hdh.index.tolist()],
        colorscale=[[0, "#0D0D0D"], [0.5, "#8B4513"], [1, "#FFD700"]],
        hoverongaps=False,
    ))
    fig3.update_layout(title="Order Heatmap: Hour × Day of Week",
                       template=PLOTLY_TEMPLATE, height=600,
                       xaxis_side="top", **_dark_layout())

    # 4. Session split pie
    ss = session_split(df)
    fig4 = px.pie(
        ss, names="session", values="orders",
        color_discrete_sequence=CHART_COLORS, hole=0.4,
    )
    fig4.update_layout(title="Orders by Session", template=PLOTLY_TEMPLATE, **_dark_layout())

    return fig1, fig2, fig3, fig4
