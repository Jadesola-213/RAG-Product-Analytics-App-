"""
Reusable KPI card component for the Overview tab.
"""

import dash_bootstrap_components as dbc
from dash import html


def kpi_card(title: str, value: str, subtitle: str = "", icon: str = "☕", color: str = "#D2691E") -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Span(icon, className="kpi-icon", style={"fontSize": "2rem"}),
                html.Div([
                    html.P(title, className="kpi-title mb-0"),
                    html.H3(value, className="kpi-value mb-0", style={"color": color}),
                    html.P(subtitle, className="kpi-subtitle text-muted mb-0") if subtitle else None,
                ], className="ms-3 flex-grow-1"),
            ], className="d-flex align-items-center"),
        ]),
        className="kpi-card h-100",
    )
