"""citations.py — Evidence and Citation Assembler."""

from pydantic import BaseModel, Field

from app.modules.graphrag.ranking.fusion import FusedEvidence


class Citation(BaseModel):
    """Structured citation item."""

    citation_id: int
    source_type: str
    source_id: str
    summary: str
    confidence_score: float


def assemble_citations(evidence_items: list[FusedEvidence]) -> list[Citation]:
    """Assemble structured citations from evidence items."""
    citations = []
    for idx, item in enumerate(evidence_items, 1):
        citations.append(
            Citation(
                citation_id=idx,
                source_type=item.source_type,
                source_id=item.source_id,
                summary=item.content,
                confidence_score=item.fusion_score,
            )
        )
    return citations
