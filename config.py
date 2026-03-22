"""
Jade Coffee Analytics — central configuration.
All tuneable values live here; nothing is hardcoded elsewhere.
"""

from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = Path("/Users/jadesolaosinowo/Desktop/Datasets/Carma Coffee Data")
ASSETS_DIR = BASE_DIR / "assets"

# ── Branding ──────────────────────────────────────────────────────────────────
APP_NAME = "Jade Coffee Analytics"
APP_TAGLINE = "Powered by data. Brewed with precision."
CURRENCY = "£"

BRAND = {
    "dark":       "#0D0D0D",
    "card":       "#1A1A1A",
    "card_border":"#2A2A2A",
    "primary":    "#8B4513",   # saddle brown
    "secondary":  "#D2691E",   # chocolate
    "accent":     "#FFD700",   # gold / cream crema
    "success":    "#4CAF50",
    "danger":     "#E53935",
    "text":       "#F5F5F5",
    "muted":      "#9E9E9E",
}

# ── Forecasting ───────────────────────────────────────────────────────────────
FORECAST_HORIZONS   = [7, 30]           # days
FORECAST_TARGETS    = ["Daily Revenue", "Daily Units", "Units by Location"]
FORECAST_MODELS     = ["Prophet", "ARIMA/SARIMA", "XGBoost", "LSTM"]
BACKTEST_WINDOW     = 14                # days held out for backtesting metrics
LSTM_SEQ_LEN        = 14               # look-back window (days)
LSTM_EPOCHS         = 200
LSTM_HIDDEN         = 64
LSTM_LAYERS         = 2
LSTM_DROPOUT        = 0.2
LSTM_LR             = 1e-3

# ── RAG / Ollama ──────────────────────────────────────────────────────────────
OLLAMA_URL          = "http://localhost:11434"
OLLAMA_MODEL        = "llama3.2"        # change to any locally pulled model
EMBED_MODEL         = "all-MiniLM-L6-v2"
RAG_TOP_K           = 5                 # chunks retrieved per query
CHUNK_SIZE          = 400               # characters per knowledge chunk

# ── Data cleaning ─────────────────────────────────────────────────────────────
PRODUCT_ALIASES = {
    "cappuccino": "Cappuccino",
    "test":       None,                  # None → drop row
}
EXCLUDED_STATUSES = {"failed", "cancelled", "pending"}

# ── Plotly theme ──────────────────────────────────────────────────────────────
PLOTLY_TEMPLATE = "plotly_dark"
CHART_COLORS = [
    "#D2691E", "#FFD700", "#8B4513",
    "#4CAF50", "#2196F3", "#E91E63",
    "#9C27B0", "#FF5722", "#00BCD4",
]
