"""explanation.py — Phase 7: Grounded XAI Explanation Generator."""

from app.modules.agents.root_cause.models import EvidenceBundle, Hypothesis


class RootCauseExplanationGenerator:
    """Phase 7: Generates evidence-grounded human-readable XAI explanations."""

    @staticmethod
    def generate_explanation(primary_hypothesis: Hypothesis, bundle: EvidenceBundle) -> str:
        """
        Build evidence-grounded explanation text.

        Example:
        The investigation indicates Valve V-12 as the most likely root cause (Confidence: 92%).
        Supporting evidence:
        • Pressure exceeded operating threshold 5 mins before incident.
        • Maintenance overdue by 34 days.
        • Similar failures occurred twice during previous year.
        """
        lines = [
            f"Root Cause Investigation Report for '{bundle.incident_id}'",
            f"Primary Discovered Cause: {primary_hypothesis.root_cause_candidate} (Confidence: {round(primary_hypothesis.confidence_score*100, 1)}%)",
            "Description: " + primary_hypothesis.description,
            "Supporting Evidence:",
        ]

        for ev in primary_hypothesis.supporting_evidence:
            lines.append(f"  • {ev}")

        if bundle.historical_incidents:
            lines.append(f"  • {len(bundle.historical_incidents)} similar historical incident(s) correlated in Knowledge Graph.")

        return "\n".join(lines)
