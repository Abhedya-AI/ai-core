"""
vectorstore/faiss.py — FAISS vector store wrapper.

Provides a clean interface for storing and searching dense embeddings.
GraphRAG builds on top of this during its own milestone.

Usage:
    store = FAISSVectorStore(dimension=1024)
    store.add(ids=["doc1", "doc2"], vectors=np.array([[...], [...]]))
    results = store.search(query_vector=embedding, top_k=5)
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import NamedTuple

import numpy as np

from app.core.logging import get_logger

log = get_logger("vectorstore.faiss")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    log.warning("faiss-cpu not installed — VectorStore unavailable")


class SearchResult(NamedTuple):
    """A single nearest-neighbour result."""
    id: str
    score: float
    index: int


class FAISSVectorStore:
    """
    In-memory FAISS vector store with persistence.

    All vectors must have the same dimension.
    Uses IndexFlatIP (inner product / cosine similarity for normalised vectors).
    """

    def __init__(self, dimension: int, index_path: str | None = None) -> None:
        if not FAISS_AVAILABLE:
            raise RuntimeError(
                "faiss-cpu is not installed. Run: uv add faiss-cpu"
            )
        self._dimension = dimension
        self._index_path = Path(index_path) if index_path else None
        self._index = faiss.IndexFlatIP(dimension)
        self._id_map: list[str] = []   # maps FAISS integer index → document ID
        log.info(f"FAISSVectorStore created (dim={dimension})")

    # ── Add ───────────────────────────────────────────────────────────────────

    def add(self, ids: list[str], vectors: np.ndarray) -> None:
        """
        Add vectors to the index.

        Args:
            ids:     List of document IDs (strings). Must match len(vectors).
            vectors: 2-D float32 array of shape (n, dimension).
        """
        if len(ids) != len(vectors):
            raise ValueError("ids and vectors must have the same length")
        vectors = vectors.astype(np.float32)
        faiss.normalize_L2(vectors)       # normalise for cosine similarity
        self._index.add(vectors)
        self._id_map.extend(ids)
        log.debug(f"Added {len(ids)} vectors. Total: {self._index.ntotal}")

    # ── Search ─────────────────────────────────────────────────────────────────

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """
        Search for the top-k nearest neighbours.

        Args:
            query_vector: 1-D float32 array of shape (dimension,).
            top_k:        Number of results to return.

        Returns:
            List of SearchResult(id, score, index) sorted by descending score.
        """
        if self._index.ntotal == 0:
            return []
        q = query_vector.astype(np.float32).reshape(1, -1)
        faiss.normalize_L2(q)
        scores, indices = self._index.search(q, min(top_k, self._index.ntotal))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append(SearchResult(
                id=self._id_map[idx],
                score=float(score),
                index=int(idx),
            ))
        return results

    # ── Persistence ────────────────────────────────────────────────────────────

    def save(self, path: str | None = None) -> None:
        """Persist the index and ID map to disk."""
        target = Path(path or self._index_path or "faiss_index")
        target.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(target / "index.faiss"))
        with open(target / "id_map.pkl", "wb") as f:
            pickle.dump(self._id_map, f)
        log.info(f"Index saved → {target}")

    def load(self, path: str | None = None) -> None:
        """Load a persisted index from disk."""
        target = Path(path or self._index_path or "faiss_index")
        self._index = faiss.read_index(str(target / "index.faiss"))
        with open(target / "id_map.pkl", "rb") as f:
            self._id_map = pickle.load(f)
        log.info(f"Index loaded ← {target} ({self._index.ntotal} vectors)")

    @property
    def size(self) -> int:
        """Number of vectors in the index."""
        return self._index.ntotal
