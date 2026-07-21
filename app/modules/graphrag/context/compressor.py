"""compressor.py — Context Compressor."""

from app.modules.graphrag.ranking.fusion import FusedEvidence


def compress_context_evidence(evidence_items: list[FusedEvidence], max_items: int = 8) -> list[FusedEvidence]:
    """Compress context evidence list to fit token limit by selecting top items."""
    return evidence_items[:max_items]
