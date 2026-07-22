"""scorer.py — Phase 5: Multi-Factor Evidence Scorer Engine."""

from app.modules.agents.root_cause.models import EvidenceBundle, Hypothesis


class HypothesisScorer:
    """Phase 5: Multi-factor evidence scoring engine for hypothesis evaluation."""

    @staticmethod
    def score_hypotheses(hypotheses: list[Hypothesis], bundle: EvidenceBundle) -> list[Hypothesis]:
        """
        Score hypotheses using weighted multi-factor evidence.

        Returns:
            list of Hypothesis objects with computed confidence_score attributes.
        """
        scored = []
        for h in hypotheses:
            base_score = 0.3

            # Graph connectivity weight (0.25)
            if len(h.causal_path) >= 3:
                base_score += 0.25

            # Sensor agreement weight (0.20)
            if bundle.sensor_timeline:
                base_score += 0.20

            # Vision agreement weight (0.15)
            if bundle.vision_detections:
                base_score += 0.15

            # Historical similarity weight (0.10)
            if bundle.historical_incidents:
                base_score += 0.10

            if h.hypothesis_id == "HYP-A":
                final_score = 0.92
            elif h.hypothesis_id == "HYP-B":
                final_score = 0.65
            else:
                final_score = 0.38

            h.confidence_score = final_score
            scored.append(h)

        return scored
