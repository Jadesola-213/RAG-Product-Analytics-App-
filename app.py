"""
Jade Coffee Analytics — entry point.

Run with:  python app.py
Then open: http://localhost:8050
"""

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ── 1. Load and prepare data ──────────────────────────────────────────────────
logger.info("Loading and processing data…")
from data import build_dataframe
import store

store.DF = build_dataframe()
logger.info("DataFrame ready: %d rows, %d columns.", *store.DF.shape)

# ── 2. Build RAG knowledge base and retriever ─────────────────────────────────
logger.info("Building RAG knowledge base…")
from rag.knowledge_base import build_knowledge_base
from rag.retriever import RAGRetriever

docs = build_knowledge_base(store.DF)
logger.info("Knowledge base: %d chunks.", len(docs))
store.RETRIEVER = RAGRetriever(docs)
logger.info("FAISS index ready.")

# ── 3. Create Dash app and register all callbacks ─────────────────────────────
from dashboard.app_instance import app   # noqa: E402
import dashboard.layout                  # sets app.layout
import dashboard.callbacks               # registers all @app.callback decorators

# ── 4. Run ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Starting Jade Coffee Analytics at http://localhost:8050")
    app.run(debug=False, host="0.0.0.0", port=8050)
