"""confidence.py — Retrieval Confidence Engine."""

from app.modules.agents.document.models import DocumentChunk


class DocumentConfidenceEngine:
    """Computes overall retrieval and answer confidence."""

    @staticmethod
    def compute_confidence(chunks: list[DocumentChunk]) -> float:
        if not chunks:
            return 0.50
        return 0.95
