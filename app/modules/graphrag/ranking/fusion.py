"""
fusion.py — Evidence Fusion & Scoring Engine.

Fuses heterogeneous graph facts and vector document chunks into a unified
fused evidence list with configurable weight scoring.
"""

from typing import Any

from pydantic import BaseModel, Field


class FusedEvidence(BaseModel):
    """Unified fused evidence item combining graph and document facts."""

    content: str
    source_type: str = Field(..., description="'GRAPH' or 'DOCUMENT'")
    source_id: str
    fusion_score: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FusionWeights(BaseModel):
    """Configurable weights for evidence fusion scoring."""

    graph_distance: float = 0.30
    semantic_similarity: float = 0.30
    document_freshness: float = 0.15
    source_reliability: float = 0.15
    confidence_score: float = 0.10


def fuse_evidence(
    graph_facts: list[dict[str, Any]],
    vector_docs: list[dict[str, Any]],
    weights: FusionWeights | None = None,
) -> list[FusedEvidence]:
    """
    Fuse graph facts and vector document chunks using weighted scoring.

    Returns:
        list of FusedEvidence items sorted by fusion_score descending.
    """
    w = weights or FusionWeights()
    fused_list: list[FusedEvidence] = []

    # Process Graph Facts
    for idx, fact in enumerate(graph_facts):
        entity_name = fact.get("name") or fact.get("title") or fact.get("id", "Node")
        entity_type = fact.get("entity_type", "Entity")
        status = fact.get("status") or fact.get("severity") or fact.get("role") or ""
        text = f"{entity_type} '{entity_name}' (ID: {fact.get('id', '')})"
        if status:
            text += f" - Status/Severity: {status}"

        # Distance weight: hop distance heuristic
        dist_score = max(0.2, 1.0 - (idx * 0.15))
        score = (
            (dist_score * w.graph_distance)
            + (0.8 * w.semantic_similarity)
            + (1.0 * w.source_reliability)
            + (0.9 * w.confidence_score)
        )

        fused_list.append(
            FusedEvidence(
                content=text,
                source_type="GRAPH",
                source_id=fact.get("id", str(idx)),
                fusion_score=round(min(1.0, score), 3),
                metadata=fact,
            )
        )

    # Process Vector Documents
    for idx, doc in enumerate(vector_docs):
        text = doc.get("text_content") or doc.get("text") or doc.get("summary") or str(doc)
        sim_score = float(doc.get("similarity_score", 0.75))

        score = (
            (0.5 * w.graph_distance)
            + (sim_score * w.semantic_similarity)
            + (0.8 * w.document_freshness)
            + (0.85 * w.source_reliability)
            + (sim_score * w.confidence_score)
        )

        fused_list.append(
            FusedEvidence(
                content=text,
                source_type="DOCUMENT",
                source_id=doc.get("document_id") or doc.get("id") or f"doc_{idx}",
                fusion_score=round(min(1.0, score), 3),
                metadata=doc,
            )
        )

    # Sort descending by fusion_score
    fused_list.sort(key=lambda x: x.fusion_score, reverse=True)
    return fused_list
