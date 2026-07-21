"""
vectorstore/embeddings.py — Embedding service wrapper.

Wraps sentence-transformers so the rest of the application never imports
from sentence_transformers directly.

Usage:
    from app.infrastructure.vectorstore.embeddings import EmbeddingService

    svc = EmbeddingService()
    vectors = svc.encode(["text A", "text B"])  # shape (2, 1024)
"""

from __future__ import annotations

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("vectorstore.embeddings")


class EmbeddingService:
    """
    Lazy-loaded sentence embedding service.

    The model is loaded on first call to encode() to avoid startup overhead.
    BGE-M3 supports 1024-dimensional embeddings and multilingual text.
    """

    _instance: EmbeddingService | None = None

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or settings.llm.embedding_model
        self._model = None

    @classmethod
    def get(cls) -> EmbeddingService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            log.info(f"Loading embedding model: {self._model_name}")
            self._model = SentenceTransformer(self._model_name)
            log.info(f"Embedding model loaded (dim={self.dimension})")
        except ImportError:
            raise RuntimeError(
                "sentence-transformers is not installed."
            )

    def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Encode texts into dense embedding vectors.

        Args:
            texts:      List of strings to embed.
            batch_size: Inference batch size.
            normalize:  Normalise to unit length (required for cosine search).

        Returns:
            2-D float32 array of shape (len(texts), dimension).
        """
        self._load()
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=False,
        )
        return embeddings.astype(np.float32)

    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single string. Returns 1-D array of shape (dimension,)."""
        return self.encode([text])[0]

    @property
    def dimension(self) -> int:
        """Embedding vector dimension."""
        self._load()
        return self._model.get_sentence_embedding_dimension()
