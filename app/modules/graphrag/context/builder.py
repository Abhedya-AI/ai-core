"""builder.py — Master Context Builder."""

from app.modules.graphrag.context.compressor import compress_context_evidence
from app.modules.graphrag.context.deduplicator import deduplicate_evidence
from app.modules.graphrag.context.formatter import format_context_block
from app.modules.graphrag.ranking.fusion import FusedEvidence


class ContextBuilder:
    """Master context builder deduplicating, compressing, and formatting evidence into LLM prompts."""

    @staticmethod
    def build_context(evidence_items: list[FusedEvidence], max_items: int = 8) -> str:
        """Deduplicate, compress, and format context block for LLM prompt."""
        deduped = deduplicate_evidence(evidence_items)
        compressed = compress_context_evidence(deduped, max_items=max_items)
        return format_context_block(compressed)
