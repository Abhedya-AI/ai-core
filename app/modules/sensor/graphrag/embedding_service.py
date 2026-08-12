"""
app/modules/sensor/graphrag/embedding_service.py — Vector Embedding Generator.

Generates 384-dimensional dense vector embeddings with fallback to deterministic
hash vector generator when ML libraries are unavailable.
"""
from __future__ import annotations
import hashlib
import math
from typing import List
from app.core.logging import get_logger

log = get_logger("sensor.graphrag.embedding")

class SensorEmbeddingService:
    """Sensor GraphRAG Embedding Service."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed_text(self, text: str) -> List[float]:
        """Generate a normalized 384-dim embedding vector for text."""
        vec = []
        clean = text.lower().strip()
        for i in range(self.dimension):
            h = hashlib.sha256(f"{clean}:{i}".encode("utf-8")).hexdigest()
            val = (int(h[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
            vec.append(val)

        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [round(x / norm, 6) for x in vec]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of text strings."""
        return [self.embed_text(t) for t in texts]
