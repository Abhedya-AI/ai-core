"""recommendation.py — Categorized & Prioritized Action Recommendation Engine."""

from app.modules.agents.risk.models import RiskScore, SeverityEnum


class RiskRecommendationEngine:
    """Generates prioritized recommendations categorized by urgency (Immediate, Within 30 Mins, Within 24 Hours)."""

    @staticmethod
    def generate_recommendations(target_id: str, score: RiskScore, affected_nodes: list[str]) -> tuple[list[str], dict[str, list[str]]]:
        """
        Generate categorized actions.

        Returns:
            tuple[flattened_recommendations_list, categorized_dict]
        """
        target = target_id or "target asset"
        immediate = []
        within_30m = []
        within_24h = []

        if score.severity in (SeverityEnum.CRITICAL, SeverityEnum.HIGH):
            immediate.append(f"Initiate immediate siren evacuation for zone containing '{target}'.")
            immediate.append(f"Isolate fuel/pressure valves feeding '{target}'.")
            within_30m.append(f"Dispatch emergency response team to inspect {target}.")
            within_30m.append("Audit PPE compliance for personnel in evacuation radius.")
            within_24h.append(f"Schedule overhaul maintenance for '{target}'.")
            within_24h.append("File incident report with OSHA compliance officer.")
        else:
            immediate.append(f"Monitor telemetry sensors on '{target}' closely.")
            within_30m.append(f"Conduct routine visual inspection of '{target}'.")
            within_24h.append(f"Log preventative maintenance check for '{target}'.")

        categorized = {
            "Immediate": immediate,
            "Within 30 Minutes": within_30m,
            "Within 24 Hours": within_24h,
        }

        flattened = immediate + within_30m + within_24h
        return flattened, categorized
