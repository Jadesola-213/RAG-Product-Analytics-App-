"""
Full Dash page layout: navbar + 6 tabs.
Sets app.layout — imported once in app.py.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

from .app_instance import app
from config import APP_NAME, APP_TAGLINE, FORECAST_MODELS, CURRENCY

# ── Shared dropdown options ───────────────────────────────────────────────────
FREQ_OPTIONS = [
    {"label": "Daily",   "value": "D"},
    {"label": "Weekly",  "value": "W"},
    {"label": "Monthly", "value": "ME"},
]
HORIZON_OPTIONS = [
    {"label": "7 Days",  "value": 7},
    {"label": "30 Days", "value": 30},
]
TARGET_OPTIONS = [
    {"label": "Daily Revenue",       "value": "revenue"},
    {"label": "Daily Units (orders)","value": "units"},
    {"label": "Units by Location",   "value": "location"},
]

# ── Navbar ────────────────────────────────────────────────────────────────────
navbar = dbc.Navbar(
    dbc.Container([
        html.Div([
            html.Span("☕", style={"fontSize": "1.8rem", "marginRight": "10px"}),
            html.Div([
                html.Span(APP_NAME, className="navbar-brand-name"),
                html.Span(APP_TAGLINE, className="navbar-brand-tagline"),
            ]),
        ], className="d-flex align-items-center"),
        dbc.Badge("LIVE", color="success", className="ms-auto me-2 px-3 py-2"),
    ], fluid=True),
    color="dark",
    dark=True,
    className="jade-navbar mb-0",
)


# ── Tab 1: Overview ───────────────────────────────────────────────────────────
def _overview_tab():
    return dbc.Tab(label="📊 Overview", tab_id="overview", children=[
        dbc.Container([
            # KPI row
            html.Div(id="kpi-row", className="row g-3 my-3"),

            # Controls
            dbc.Row([
                dbc.Col([
                    html.Label("Aggregation", className="text-muted small"),
                    dcc.Dropdown(
                        id="overview-freq",
                        options=FREQ_OPTIONS,
                        value="D",
                        clearable=False,
                        className="dash-dropdown-dark",
                    ),
                ], width=3),
            ], className="mb-3"),

            # Charts
            dbc.Row([
                dbc.Col(dcc.Graph(id="revenue-trend-chart", config={"displayModeBar": False}), md=8),
                dbc.Col(dcc.Graph(id="channel-split-chart", config={"displayModeBar": False}), md=4),
            ], className="g-3"),
            dbc.Row([
                dbc.Col(dcc.Graph(id="order-volume-chart", config={"displayModeBar": False}), md=12),
            ], className="g-3 mt-1"),
        ], fluid=True),
    ])


# ── Tab 2: Products ───────────────────────────────────────────────────────────
def _products_tab():
    return dbc.Tab(label="☕ Products", tab_id="products", children=[
        dbc.Container([
            dbc.Row([
                dbc.Col(dcc.Graph(id="product-revenue-bar",  config={"displayModeBar": False}), md=6),
                dbc.Col(dcc.Graph(id="product-volume-pie",   config={"displayModeBar": False}), md=6),
            ], className="g-3 my-3"),
            dbc.Row([
                dbc.Col(dcc.Graph(id="product-trend-area",   config={"displayModeBar": False}), md=8),
                dbc.Col(dcc.Graph(id="loyalty-ratio-chart",  config={"displayModeBar": False}), md=4),
            ], className="g-3"),
        ], fluid=True),
    ])


# ── Tab 3: Locations ──────────────────────────────────────────────────────────
def _locations_tab():
    return dbc.Tab(label="📍 Locations", tab_id="locations", children=[
        dbc.Container([
            dbc.Row([
                dbc.Col(dcc.Graph(id="location-ranking-bar", config={"displayModeBar": False}), md=6),
                dbc.Col(dcc.Graph(id="failed-rate-chart",    config={"displayModeBar": False}), md=6),
            ], className="g-3 my-3"),
            dbc.Row([
                dbc.Col(dcc.Graph(id="location-heatmap",     config={"displayModeBar": False}), md=12),
            ], className="g-3"),
            dbc.Row([
                dbc.Col(dcc.Graph(id="location-trend-chart", config={"displayModeBar": False}), md=12),
            ], className="g-3 mt-1"),
        ], fluid=True),
    ])


# ── Tab 4: Time Analysis ──────────────────────────────────────────────────────
def _time_tab():
    return dbc.Tab(label="⏰ Time Analysis", tab_id="time", children=[
        dbc.Container([
            dbc.Row([
                dbc.Col(dcc.Graph(id="hourly-bar",       config={"displayModeBar": False}), md=6),
                dbc.Col(dcc.Graph(id="dow-bar",          config={"displayModeBar": False}), md=6),
            ], className="g-3 my-3"),
            dbc.Row([
                dbc.Col(dcc.Graph(id="hour-dow-heatmap", config={"displayModeBar": False}), md=8),
                dbc.Col(dcc.Graph(id="session-pie",      config={"displayModeBar": False}), md=4),
            ], className="g-3"),
        ], fluid=True),
    ])


# ── Tab 5: Forecasting ────────────────────────────────────────────────────────
def _forecasting_tab():
    return dbc.Tab(label="🔮 Forecasting", tab_id="forecasting", children=[
        dbc.Container([
            # Controls row
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Forecast Target", className="text-muted small fw-bold"),
                            dcc.Dropdown(
                                id="fc-target",
                                options=TARGET_OPTIONS,
                                value="revenue",
                                clearable=False,
                            ),
                        ], md=3),
                        dbc.Col([
                            html.Label("Horizon", className="text-muted small fw-bold"),
                            dcc.Dropdown(
                                id="fc-horizon",
                                options=HORIZON_OPTIONS,
                                value=7,
                                clearable=False,
                            ),
                        ], md=2),
                        dbc.Col([
                            html.Label("Location (for location target)", className="text-muted small fw-bold"),
                            dcc.Dropdown(
                                id="fc-location",
                                placeholder="Select location…",
                                clearable=True,
                            ),
                        ], md=3),
                        dbc.Col([
                            html.Label("Models", className="text-muted small fw-bold"),
                            dcc.Checklist(
                                id="fc-models",
                                options=[{"label": f"  {m}", "value": m} for m in FORECAST_MODELS],
                                value=["Prophet", "XGBoost"],
                                inputStyle={"marginRight": "6px"},
                                labelStyle={"display": "block", "color": "#F5F5F5"},
                            ),
                        ], md=2),
                        dbc.Col([
                            html.Label("\u00a0", className="text-muted small fw-bold d-block"),
                            dbc.Button(
                                "Run Forecast",
                                id="fc-run-btn",
                                color="warning",
                                className="w-100 mt-1 fw-bold",
                            ),
                        ], md=2),
                    ]),
                ]),
            ], className="my-3"),

            dcc.Loading(
                id="fc-loading",
                type="circle",
                color="#D2691E",
                children=[
                    dbc.Row([
                        dbc.Col(
                            dbc.Alert(
                                "⚠️ LSTM is trained on ~104 days of data. Results carry higher variance "
                                "than statistical models — interpret with caution.",
                                color="warning", dismissable=True, is_open=True,
                                id="lstm-warning",
                            ),
                            md=12,
                        ),
                    ]),
                    dbc.Row([
                        dbc.Col(dcc.Graph(id="fc-chart", config={"displayModeBar": True}), md=12),
                    ], className="g-3"),
                    dbc.Row([
                        dbc.Col([
                            html.H6("Backtest Metrics (last 14 days held out)", className="text-muted mt-3"),
                            html.Div(id="fc-metrics-table"),
                        ], md=12),
                    ], className="g-3"),
                ],
            ),
        ], fluid=True),
    ])


# ── Tab 6: Ask Jade (RAG) ─────────────────────────────────────────────────────
def _rag_tab():
    return dbc.Tab(label="🤖 Ask Jade", tab_id="rag", children=[
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H4("Ask Jade", className="mt-3 mb-1", style={"color": "#D2691E"}),
                    html.P(
                        "Ask any question about Jade Coffee's sales data. "
                        "Answers are grounded in real order data retrieved from the knowledge base.",
                        className="text-muted mb-3",
                    ),
                    # Chat history
                    html.Div(
                        id="chat-history",
                        className="chat-window mb-3",
                        children=[
                            html.Div([
                                html.Span("🤖 Jade", className="chat-sender"),
                                html.P(
                                    "Hello! I'm Jade, your coffee data analyst. "
                                    "Ask me anything about sales, products, locations, or trends.",
                                    className="chat-bubble assistant-bubble",
                                ),
                            ], className="chat-message"),
                        ],
                    ),
                    # Input row
                    dbc.InputGroup([
                        dbc.Input(
                            id="rag-input",
                            placeholder="e.g. Which location had the most sales last week?",
                            type="text",
                            debounce=False,
                            className="rag-input",
                        ),
                        dbc.Button("Ask ☕", id="rag-submit-btn", color="warning", className="fw-bold"),
                    ]),
                    dcc.Loading(id="rag-loading", type="dot", color="#D2691E",
                                children=html.Div(id="rag-loading-placeholder")),
                    # Sources accordion
                    html.Div(id="rag-sources", className="mt-3"),
                    # Hidden store for chat history
                    dcc.Store(id="chat-store", data=[]),
                ], md=10, lg=8, className="mx-auto"),
            ]),
        ], fluid=True),
    ])


# ── Main layout ───────────────────────────────────────────────────────────────
app.layout = html.Div([
    navbar,
    dbc.Tabs(
        id="main-tabs",
        active_tab="overview",
        className="jade-tabs px-3",
        children=[
            _overview_tab(),
            _products_tab(),
            _locations_tab(),
            _time_tab(),
            _forecasting_tab(),
            _rag_tab(),
        ],
    ),
    # Global data store (populated at startup)
    dcc.Store(id="data-store"),
], className="jade-app")
