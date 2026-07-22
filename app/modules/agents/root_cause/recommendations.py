"""recommendations.py — Categorized Corrective Action Recommendation Engine."""

from app.modules.agents.root_cause.models import Hypothesis


class CorrectiveRecommendationEngine:
    """Generates categorized corrective recommendations (Immediate, Preventive, Strategic)."""

    @staticmethod
    def generate_recommendations(primary_hypothesis: Hypothesis) -> tuple[list[str], dict[str, list[str]]]:
        """
        Generate categorized corrective actions.

        Returns:
            tuple[flattened_actions_list, categorized_dict]
        """
        cause = primary_hypothesis.root_cause_candidate
        immediate = [
            f"Replace faulty component '{cause}'",
            "Inspect adjacent connected piping and valves",
            "Verify sensor telemetry calibration",
        ]

        preventive = [
            "Reduce preventive maintenance interval by 25%",
            "Increase weekly automated diagnostic inspection frequency",
            "Update operating procedures for high-pressure zones",
        ]

        strategic = [
            "Install redundant pressure sensors across critical assets",
            "Revise facility emergency response drills",
            "Review long-term maintenance planning and procurement policies",
        ]

        categorized = {
            "Immediate": immediate,
            "Preventive": preventive,
            "Strategic": strategic,
        }

        flattened = immediate + preventive + strategic
        return flattened, categorized
