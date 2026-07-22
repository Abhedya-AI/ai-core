"""explanation.py — Phase 8: Evidence-Grounded XAI Explanation Generator."""

from app.modules.agents.compliance.models import ComplianceScore, ComplianceViolation


class ComplianceExplanationGenerator:
    """Phase 8: Generates evidence-grounded human-readable XAI explanations."""

    @staticmethod
    def generate_explanation(
        score: ComplianceScore,
        violations: list[ComplianceViolation],
        regulations: list[str],
    ) -> str:
        """
        Build evidence-grounded explanation text.

        Example:
        Operation is partially compliant (Overall Score: 70.0/100).
        Critical findings:
        • Hot work permit EXPIRED (FS-17).
        • Worker W-101 lacks valid CONFINED_SPACE certification (HS-04).
        • Emergency exit in ZONE-C obstructed (OSHA-1910.37).
        Relevant regulations: OSHA-1910.147, FS-17, HS-04
        """
        status_str = "FULLY COMPLIANT" if score.overall_score == 100.0 else "NON-COMPLIANT" if score.critical_violations_count > 0 else "PARTIALLY COMPLIANT"

        lines = [
            f"Compliance Audit Report — Status: {status_str} (Overall Score: {score.overall_score}/100)",
            f"Violations Summary: {score.critical_violations_count} Critical, {score.major_violations_count} Major, {score.minor_violations_count} Minor",
            "Critical Findings:",
        ]

        if not violations:
            lines.append("  • No compliance violations detected. Operational adherence confirmed.")
        else:
            for v in violations:
                lines.append(f"  • [{v.severity.value}] {v.evidence_summary} (Ref: {v.regulation_reference})")

        lines.append("Referenced Regulatory Standards: " + ", ".join(regulations))
        return "\n".join(lines)
