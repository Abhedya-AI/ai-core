"""confidence_engine.py — Evidence Confidence Scoring Engine."""
from __future__ import annotations
import math
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.root_cause.domain.models import (
    Evidence, EvidenceScore, EvidenceWeight, EvidenceSource,
)

log = get_logger("root_cause.evidence.confidence")

# Source-specific reliability weights
_SOURCE_WEIGHTS: dict[EvidenceSource, float] = {
    EvidenceSource.SENSOR_INTELLIGENCE: 0.90,
    EvidenceSource.VISION_INTELLIGENCE: 0.92,
    EvidenceSource.KNOWLEDGE_GRAPH: 0.80,
    EvidenceSource.GRAPHRAG: 0.75,
    EvidenceSource.WORKFLOW_ENGINE: 0.70,
    EvidenceSource.INCIDENT_MANAGEMENT: 0.85,
    EvidenceSource.AUDIT_FRAMEWORK: 1.00,
    EvidenceSource.NOTIFICATION_FRAMEWORK: 0.60,
    EvidenceSource.SUPERVISOR: 0.95,
    EvidenceSource.EXTERNAL: 0.50,
}

_SEVERITY_BOOST: dict[str, float] = {
    "CRITICAL": 0.15,
    "HIGH": 0.10,
    "MEDIUM": 0.05,
    "LOW": 0.0,
    "INFO": 0.0,
}


class ConfidenceEngine:
    """Computes explainable confidence scores for investigation evidence."""

    def compute_evidence_score(self, evidence: Evidence) -> EvidenceScore:
        log.debug(f"Computing score for evidence {evidence.id}")
        source_weight = _SOURCE_WEIGHTS.get(evidence.source, 0.5)

        # Map source to the correct weight dimension
        breakdown = EvidenceWeight(
            sensor_confidence=evidence.confidence if evidence.source == EvidenceSource.SENSOR_INTELLIGENCE else 0.0,
            vision_confidence=evidence.confidence if evidence.source == EvidenceSource.VISION_INTELLIGENCE else 0.0,
            graph_confidence=evidence.confidence if evidence.source == EvidenceSource.KNOWLEDGE_GRAPH else 0.0,
            graphrag_confidence=evidence.confidence if evidence.source == EvidenceSource.GRAPHRAG else 0.0,
            historical_similarity=0.0,
            evidence_reliability=evidence.reliability,
            time_consistency=self._time_consistency(evidence.timestamp),
        )

        severity_boost = _SEVERITY_BOOST.get(evidence.severity.upper(), 0.0)
        raw = (source_weight * evidence.confidence * evidence.reliability
               * breakdown.time_consistency) + severity_boost
        overall = min(1.0, max(0.0, raw))

        explanation = (
            f"Score {overall:.3f}: source_weight={source_weight:.2f}, "
            f"confidence={evidence.confidence:.2f}, reliability={evidence.reliability:.2f}, "
            f"time_consistency={breakdown.time_consistency:.2f}, severity_boost={severity_boost:.2f}"
        )
        return EvidenceScore(overall_score=overall, breakdown=breakdown, explanation=explanation)

    def compute_investigation_confidence(
        self,
        evidence_list: list[Evidence],
        hypothesis_scores: list[float],
    ) -> float:
        if not evidence_list:
            return 0.0
        ev_scores = [self.compute_evidence_score(e).overall_score for e in evidence_list]
        avg_evidence = sum(ev_scores) / len(ev_scores)
        avg_hypothesis = (sum(hypothesis_scores) / len(hypothesis_scores)) if hypothesis_scores else 0.0
        return min(1.0, max(0.0, avg_evidence * 0.6 + avg_hypothesis * 0.4))

    def explain_confidence(self, score: EvidenceScore) -> str:
        return score.explanation or f"Overall confidence: {score.overall_score:.3f}"

    @staticmethod
    def _time_consistency(timestamp_str: str) -> float:
        try:
            ts = datetime.fromisoformat(timestamp_str)
            age_seconds = (datetime.now(timezone.utc) - ts).total_seconds()
            return max(0.1, math.exp(-max(0, age_seconds) / (86400 * 7)))
        except (ValueError, TypeError):
            return 0.5
