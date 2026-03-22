"""
RAG retriever: embeds knowledge base chunks with sentence-transformers,
stores them in a FAISS flat index, and retrieves the top-K most relevant
chunks for any incoming query.
"""

from __future__ import annotations
import logging
import numpy as np

from config import EMBED_MODEL, RAG_TOP_K

logger = logging.getLogger(__name__)


class RAGRetriever:
    """
    Build once at startup:
        retriever = RAGRetriever(docs)
    Then retrieve for each query:
        chunks = retriever.retrieve("Which location sold the most?")
    """

    def __init__(self, docs: list[str], top_k: int = RAG_TOP_K):
        self.docs   = docs
        self.top_k  = top_k
        self._index = None
        self._embeddings = None
        self._embed_model = None
        self._build_index(docs)

    def _embed(self, texts: list[str]) -> np.ndarray:
        if self._embed_model is None:
            logger.info("Loading sentence-transformer: %s", EMBED_MODEL)
            from sentence_transformers import SentenceTransformer
            self._embed_model = SentenceTransformer(EMBED_MODEL)
        return self._embed_model.encode(texts, show_progress_bar=False, normalize_embeddings=True)

    def _build_index(self, docs: list[str]) -> None:
        import faiss

        logger.info("Building FAISS index over %d chunks…", len(docs))
        embeddings = self._embed(docs).astype(np.float32)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)   # inner-product on normalised vecs = cosine sim
        index.add(embeddings)
        self._index      = index
        self._embeddings = embeddings
        logger.info("FAISS index ready (dim=%d).", dim)

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict]:
        """
        Return top-K chunks with their similarity scores.
        Each item: {'text': str, 'score': float}
        """
        k = top_k or self.top_k
        q_emb = self._embed([query]).astype(np.float32)
        scores, indices = self._index.search(q_emb, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.docs):
                results.append({"text": self.docs[idx], "score": float(score)})
        return results
