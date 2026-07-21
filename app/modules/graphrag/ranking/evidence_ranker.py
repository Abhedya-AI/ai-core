"""evidence_ranker.py — Master Evidence Ranker."""

from typing import Any

from app.modules.graphrag.ranking.fusion import FusedEvidence, FusionWeights, fuse_evidence


class EvidenceRanker:
    """Master evidence ranker applying multi-factor evidence fusion."""

    def __init__(self, weights: FusionWeights | None = None) -> None:
        self.weights = weights or FusionWeights()

    def rank_evidence(
        self,
        graph_facts: list[dict[str, Any]],
        vector_docs: list[dict[str, Any]],
        top_n: int = 10,
    ) -> list[FusedEvidence]:
        """Rank and return top_n fused evidence items."""
        fused = fuse_evidence(graph_facts, vector_docs, self.weights)
        return fused[:top_n]
