"""explanation.py — Evidence-Grounded XAI Explanation Generator."""

from app.modules.agents.risk.models import RiskEvidence, RiskScore


class RiskExplanationGenerator:
    """Generates human-readable XAI explanations from deterministic evidence and risk scores."""

    @staticmethod
    def generate_explanation(target_id: str, score: RiskScore, evidence: RiskEvidence, affected_nodes: list[str]) -> str:
        """
        Build evidence-grounded explanation text.

        Example:
        High Risk (Score: 88.5/100, Severity: CRITICAL) on 'Tank T-12' because:
        - 2 sensor reading(s) exceeded safety thresholds.
        - 1 maintenance log(s) marked overdue.
        - Multi-hop risk propagated across 4 affected assets/zones.
        """
        lines = [
            f"Risk Assessment for '{target_id or 'Facility Asset'}'",
            f"Severity: {score.severity.value} | Priority: {score.priority.value} | Score: {score.score_value}/100",
            "Root Contributing Factors:",
        ]

        if evidence.sensor_readings:
            lines.append(f"  • {len(evidence.sensor_readings)} telemetry sensor reading(s) evaluated.")
        if evidence.maintenance_logs:
            lines.append(f"  • {len(evidence.maintenance_logs)} equipment maintenance log(s) analyzed.")
        if evidence.vision_events:
            lines.append(f"  • {len(evidence.vision_events)} computer vision detection event(s) recorded.")
        if len(affected_nodes) > 1:
            lines.append(f"  • Multi-hop risk propagated across {len(affected_nodes)} downstream assets/zones: {', '.join(affected_nodes[:4])}.")

        return "\n".join(lines)
