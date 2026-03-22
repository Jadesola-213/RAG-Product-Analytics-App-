"""
Forecasting tab callbacks.

On "Run Forecast" click:
  1. Prepare daily time series for the chosen target.
  2. Run run_backtest() for the metrics table.
  3. Run run_forecast() for the forecast chart.
"""

import plotly.graph_objects as go
import pandas as pd
from dash import Input, Output, State, dash_table, html
import dash_bootstrap_components as dbc

from dashboard.app_instance import app
from forecasting import prepare_daily_series, run_backtest
from forecasting.evaluator import run_forecast
from config import PLOTLY_TEMPLATE, CHART_COLORS, BRAND, CURRENCY, FORECAST_MODELS

import store


def _dark_layout(**kwargs):
    return dict(
        paper_bgcolor=BRAND["card"], plot_bgcolor=BRAND["card"],
        font_color=BRAND["text"], margin=dict(l=15, r=15, t=45, b=15),
        **kwargs,
    )


# Populate location dropdown
@app.callback(
    Output("fc-location", "options"),
    Input("main-tabs", "active_tab"),
)
def populate_location_dropdown(_tab):
    df = store.DF
    locs = sorted(df["machine_name"].unique())
    return [{"label": l, "value": l} for l in locs]


# Show/hide LSTM warning
@app.callback(
    Output("lstm-warning", "is_open"),
    Input("fc-models", "value"),
)
def toggle_lstm_warning(models):
    return "LSTM" in (models or [])


# Main forecast callback
@app.callback(
    Output("fc-chart",        "figure"),
    Output("fc-metrics-table","children"),
    Input("fc-run-btn",       "n_clicks"),
    State("fc-target",        "value"),
    State("fc-horizon",       "value"),
    State("fc-location",      "value"),
    State("fc-models",        "value"),
    prevent_initial_call=True,
)
def run_forecast_callback(n_clicks, target, horizon, location, models):
    if not models:
        empty = go.Figure()
        empty.update_layout(title="Select at least one model.", **_dark_layout())
        return empty, html.P("No models selected.", className="text-muted")

    df = store.DF

    # Handle location target
    actual_target = target
    if target == "location":
        if not location:
            fig = go.Figure()
            fig.update_layout(title="Please select a location.", **_dark_layout())
            return fig, html.P("No location selected.", className="text-muted")
        actual_target = "location"

    series = prepare_daily_series(df, target=actual_target, location=location)

    # ── Backtest metrics ──────────────────────────────────────────────────────
    metrics_df = run_backtest(series, models=models)

    # ── Forecast ──────────────────────────────────────────────────────────────
    forecasts = run_forecast(series, horizon=horizon, models=models)

    # ── Build chart ───────────────────────────────────────────────────────────
    y_label = (
        f"Revenue ({CURRENCY})" if target == "revenue"
        else f"Units ({location or 'All'})" if target == "location"
        else "Orders"
    )

    fig = go.Figure()

    # Actual historical data (last 30 days for context)
    hist = series.tail(30)
    fig.add_trace(go.Scatter(
        x=hist["ds"], y=hist["y"],
        mode="lines+markers",
        name="Actual",
        line=dict(color=BRAND["text"], width=2),
        marker=dict(size=4),
    ))

    # Vertical line at last actual date
    last_date = series["ds"].max()
    fig.add_vline(
        x=last_date, line_dash="dash",
        line_color=BRAND["muted"], opacity=0.6,
        annotation_text="Forecast start",
        annotation_font_color=BRAND["muted"],
    )

    model_colors = CHART_COLORS[:]
    for i, (model_name, fc_df) in enumerate(forecasts.items()):
        color = model_colors[i % len(model_colors)]
        fig.add_trace(go.Scatter(
            x=fc_df["ds"], y=fc_df["yhat"],
            mode="lines+markers",
            name=model_name,
            line=dict(color=color, width=2.5, dash="dot"),
            marker=dict(size=5, symbol="diamond"),
        ))

    title_suffix = f" — {location}" if (target == "location" and location) else ""
    fig.update_layout(
        title=f"{horizon}-Day Forecast: {y_label}{title_suffix}",
        xaxis_title="Date",
        yaxis_title=y_label,
        template=PLOTLY_TEMPLATE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        **_dark_layout(),
    )

    # ── Metrics table ─────────────────────────────────────────────────────────
    table = dash_table.DataTable(
        data=metrics_df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in metrics_df.columns],
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": BRAND["primary"],
            "color": BRAND["text"],
            "fontWeight": "bold",
            "textAlign": "center",
        },
        style_cell={
            "backgroundColor": BRAND["card"],
            "color": BRAND["text"],
            "textAlign": "center",
            "border": f"1px solid {BRAND['card_border']}",
            "padding": "8px 16px",
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#242424",
            }
        ],
        sort_action="native",
    )

    return fig, table
