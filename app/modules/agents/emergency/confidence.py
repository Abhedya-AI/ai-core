"""confidence.py — Emergency Decision Confidence Engine."""

from app.modules.agents.emergency.models import SituationModel


class EmergencyConfidenceEngine:
    """Computes overall decision confidence for emergency response plans."""

    @staticmethod
    def compute_confidence(situation: SituationModel) -> float:
        if situation.accessible_exits:
            return 0.96
        return 0.85
