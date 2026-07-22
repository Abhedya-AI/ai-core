"""recommendation.py — Predictive Action Recommendation Engine."""

from app.modules.agents.prediction.models import PredictionOutput


class PredictiveRecommendationEngine:
    """Generates categorized predictive action recommendations across time horizons."""

    @staticmethod
    def generate_recommendations(predictions: list[PredictionOutput]) -> dict[str, list[str]]:
        """
        Generate recommendations categorized by horizon.

        Returns:
            dict containing lists of actions under 'Immediate', 'Within 12 Hours', 'Within 24 Hours', 'Within 7 Days'.
        """
        immediate = []
        within_12h = []
        within_24h = []
        within_7d = []

        for p in predictions:
            target = p.target_entity_id
            if p.probability >= 0.75:
                immediate.append(f"Inspect asset '{target}' immediately due to {round(p.probability*100, 1)}% failure probability.")
                within_12h.append(f"Replace high-stress components on '{target}'.")
                within_24h.append(f"Schedule preventive maintenance for '{target}'.")
                within_7d.append(f"Review maintenance policy for '{target}'.")
            elif p.probability >= 0.40:
                within_12h.append(f"Check telemetry and calibration on '{target}'.")
                within_24h.append(f"Schedule routine inspection for '{target}'.")
                within_7d.append(f"Audit operating conditions for '{target}'.")
            else:
                within_7d.append(f"Log routine health status for '{target}'.")

        return {
            "Immediate": list(dict.fromkeys(immediate)),
            "Within 12 Hours": list(dict.fromkeys(within_12h)),
            "Within 24 Hours": list(dict.fromkeys(within_24h)),
            "Within 7 Days": list(dict.fromkeys(within_7d)),
        }
