"""
Ollama-backed Q&A chain.

ask_jade(question, retriever) → (answer: str, sources: list[str])

If Ollama is not running, returns a friendly error with setup instructions.
"""

from __future__ import annotations
import json
import logging
import requests

from config import OLLAMA_URL, OLLAMA_MODEL
from .retriever import RAGRetriever

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are Jade, an expert data analyst for Jade Coffee — a UK-based automated coffee machine company.
You answer questions about the company's sales data accurately and concisely.
You ONLY use the provided context to answer. If the context does not contain the answer, say so honestly.
Always cite specific numbers and dates from the context. Keep answers under 150 words unless more detail is needed.
"""

_PROMPT_TEMPLATE = """\
### Context (data-backed facts)
{context}

### Question
{question}

### Answer
"""


def _is_ollama_running() -> bool:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def ask_jade(question: str, retriever: RAGRetriever) -> tuple[str, list[str]]:
    """
    Parameters
    ----------
    question  : the user's natural-language question
    retriever : built RAGRetriever with embedded knowledge base

    Returns
    -------
    answer  : LLM-generated answer grounded in the retrieved context
    sources : list of retrieved chunk texts shown as citations
    """
    if not _is_ollama_running():
        return (
            "⚠️ **Ollama is not running.**\n\n"
            "To enable Ask Jade, start Ollama:\n"
            "```\n"
            "# Install (macOS)\n"
            "brew install ollama\n\n"
            "# Pull a model\n"
            "ollama pull llama3.2\n\n"
            "# Start the server\n"
            "ollama serve\n"
            "```\n"
            "Then refresh this page.",
            [],
        )

    # Retrieve relevant chunks
    hits    = retriever.retrieve(question)
    sources = [h["text"] for h in hits]
    context = "\n\n".join(f"[{i+1}] {s}" for i, s in enumerate(sources))

    prompt = _PROMPT_TEMPLATE.format(context=context, question=question)

    payload = {
        "model":  OLLAMA_MODEL,
        "system": _SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 400},
    }

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        answer = data.get("response", "").strip()
    except requests.exceptions.Timeout:
        answer = "⏱️ Ollama timed out. The model may still be loading — try again in a moment."
    except Exception as exc:
        logger.error("Ollama error: %s", exc)
        answer = f"❌ Error contacting Ollama: {exc}"

    return answer, sources
