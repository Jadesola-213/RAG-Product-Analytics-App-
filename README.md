# ☕ Coffee Business Analytics

A full-stack analytics and forecasting dashboard for a UK-based automated coffee machine company. Built with Python, Plotly Dash, and a local RAG (Retrieval-Augmented Generation) Q&A engine, this application turns raw Excel order exports into actionable business intelligence.

## Features

| Tab | What it does |
|---|---|
|  **Overview** | KPI cards, revenue trend, order volume, channel split (kiosk vs app) |
|  **Products** | Revenue and unit breakdown per product, loyalty vs paid analysis |
|  **Locations** | Top locations by revenue, app fail rates, day-of-week heatmap |
|  **Time Analysis** | Hourly patterns, day-of-week patterns, session breakdowns |
|  **Forecasting** | Prophet, ARIMA/SARIMA, XGBoost and LSTM multi-model forecasting with backtest metrics |
|  **Ask Jade** | Natural language Q&A grounded in real order data via local RAG (Ollama + FAISS) |

## Project Structure

-coffee-analytics/
├── app.py                        # Entry point — loads data, builds RAG, starts Dash
├── store.py                      # Module-level singletons (DataFrame, Retriever)
├── config.py                     # All tuneable config (paths, branding, model params)
├── setup.sh                      # One-command setup + launch script
├── requirements.txt
│
├── data/                         # ETL pipeline
│   ├── ingestion.py              # Load & parse Excel sheets (Kiosk + App Orders)
│   ├── cleaning.py               # Deduplication, flags, fulfillment time
│   └── features.py               # Time features, session labels, price bands
│
├── analytics/                    # Pure analytics functions (no Dash)
│   ├── overview.py               # KPIs, revenue trend, channel split
│   ├── products.py               # Product revenue, volume, loyalty ratio
│   ├── locations.py              # Location ranking, heatmap, fail rate
│   └── time_analysis.py          # Hourly, day-of-week, session patterns
│
├── forecasting/                  # Multi-model time series forecasting
│   ├── base.py                   # Abstract BaseForecaster
│   ├── data_prep.py              # Prepare daily series (revenue / units / location)
│   ├── evaluator.py              # Backtest engine + forecast runner
│   ├── prophet_model.py          # Prophet with UK bank holidays
│   ├── arima_model.py            # ARIMA/SARIMA via pmdarima.auto_arima
│   ├── xgboost_model.py          # XGBoost with lag + rolling features
│   └── lstm_model.py             # 2-layer stacked LSTM (PyTorch)
│
├── rag/                          # Retrieval-Augmented Generation Q&A
│   ├── knowledge_base.py         # Generate text chunks from DataFrame
│   ├── retriever.py              # Sentence-transformer + FAISS index
│   └── qa.py                     # Ollama-backed answer generation
│
├── dashboard/                    # Dash UI
│   ├── app_instance.py           # Dash app singleton
│   ├── layout.py                 # Full page layout (navbar + 6 tabs)
│   ├── components/
│   │   └── kpi_card.py           # Reusable KPI card component
│   └── callbacks/
│       ├── overview_cb.py
│       ├── products_cb.py
│       ├── locations_cb.py
│       ├── time_cb.py
│       ├── forecasting_cb.py
│       └── rag_cb.py
│
└── assets/
    └── style.css                 # Brand CSS (dark theme, coffee palette)
```

##  Requirements

- Python 3.9+
- macOS / Linux (Windows via WSL)
- [Anaconda](https://www.anaconda.com/) recommended (bundles `libomp` for XGBoost)
- [Ollama](https://ollama.com/) (optional — only required for the Ask RAG tab)

---

##  Quick Start

**### Option A — Automated setup **

```bash
git clone https://github.com/YOURUSERNAME/jade-coffee-analytics.git
cd jade-coffee-analytics
bash setup.sh
```

`setup.sh` installs all dependencies and launches the app automatically.

### Option B — Manual setup

```bash
# 1. Clone the repo
git clone https://github.com/YOURUSERNAME/jade-coffee-analytics.git
cd jade-coffee-analytics

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your data path (see Configuration below)

# 5. Run
python app.py
```

Then open **http://localhost:8050** in your browser.

---

##  Data

The app expects one or more `.xlsx` files in the directory configured in `config.py`. Each file must contain at least one of these sheets:

| Sheet name | Description |
|---|---|
| `Kiosk Orders` | Orders placed directly at the machine |
| `App Orders` | Orders placed via the mobile app |

### Required columns

**Kiosk Orders:** `Order Number`, `Order Time`, `Machine Name`, `Machine Number`, `Products`, `Total Price`, `Order Status`, `Payment Complete`

**App Orders:** all of the above, plus `Order Sent To Machine`, `Order Completion Time`, `Product Price`


##  Configuration

All settings are in `config.py`. The key values to update before first run:

```python
# Path to your Excel data files
DATA_DIR = Path("/path/to/your/data/folder")

# Currency symbol
CURRENCY = "£"

# Forecasting models to show in the UI
FORECAST_MODELS = ["Prophet", "ARIMA/SARIMA", "XGBoost", "LSTM"]

# RAG: local Ollama model to use
OLLAMA_MODEL = "llama3.2"
```

---

##  Ask  (RAG Setup)

The **Ask ** tab uses a local LLM via [Ollama](https://ollama.com/) to answer natural language questions grounded in your order data. To enable it:

```bash
# 1. Install Ollama (macOS)
brew install ollama

# 2. Pull a model
ollama pull llama3.2

# 3. Start the Ollama server (keep this running in a separate terminal)
ollama serve
```

The dashboard works fully without Ollama — only the Ask tab will show setup instructions instead of answers.

Example questions you can ask:
- *"Which location had the most revenue last month?"*
- *"What is the most popular product?"*
- *"How does app performance compare to kiosk?"*
- *"What are the peak ordering hours?"*

---

##  Forecasting Models

| Model | Best for | Notes |
|---|---|---|
| **Prophet** | Weekly seasonality, holiday effects | Recommended for general use |
| **ARIMA/SARIMA** | Stable, low-noise series | Auto-selects order via AIC |
| **XGBoost** | Capturing non-linear patterns | Uses lag + rolling features |
| **LSTM** | Complex temporal patterns | Higher variance on short data |

Backtest metrics (MAE, RMSE, MAPE) are computed by holding out the last 14 days of data and comparing each model's predictions to actual values.

>  With ~104 days of historical data, LSTM results carry higher variance than statistical models. Interpret with caution.

---

##  macOS Notes

XGBoost requires OpenMP. If you see a `libxgboost.dylib` error:

```bash
# Option A (recommended) — use Anaconda Python which ships with libomp
/opt/anaconda3/bin/python app.py

# Option B — install libomp via Homebrew
brew install libomp
```

---

## Key Dependencies

| Package | Purpose |
|---|---|
| `dash` + `dash-bootstrap-components` | Web dashboard framework |
| `plotly` | Interactive charts |
| `pandas` / `numpy` | Data manipulation |
| `prophet` | Time series forecasting |
| `pmdarima` | Auto ARIMA/SARIMA |
| `xgboost` | Gradient boosted forecasting |
| `torch` | LSTM neural network |
| `sentence-transformers` | Text embeddings for RAG |
| `faiss-cpu` | Vector similarity search |
| `requests` | Ollama API communication |

---

##  Licence

MIT — free to use, modify, and distribute.
