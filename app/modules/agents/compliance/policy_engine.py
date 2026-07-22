"""policy_engine.py — High-Level Policy Evaluation Engine."""

from app.modules.agents.compliance.models import ComplianceScore, ComplianceViolation


class PolicyEngine:
    """Evaluates high-level compliance policies and operational authorization."""

    @staticmethod
    def evaluate_authorization(score: ComplianceScore, violations: list[ComplianceViolation]) -> bool:
        """Determine if operation is authorized to proceed."""
        if score.critical_violations_count > 0:
            return False
        return score.overall_score >= 75.0
