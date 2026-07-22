"""confidence.py — Root Cause Confidence Engine."""

from app.modules.agents.root_cause.models import EvidenceBundle, Hypothesis


class RootCauseConfidenceEngine:
    """Computes overall confidence for root cause analysis results."""

    @staticmethod
    def compute_confidence(ranked_hypotheses: list[Hypothesis], bundle: EvidenceBundle) -> float:
        if not ranked_hypotheses:
            return 0.5
        top_h = ranked_hypotheses[0]
        return round(top_h.confidence_score, 2)
