"""scorer.py — Phase 7: Multi-Dimensional Compliance Scoring Engine."""

from app.modules.agents.compliance.models import ComplianceScore, ComplianceViolation, ViolationSeverity


class ComplianceScorer:
    """Phase 7: Computes multi-dimensional compliance score (Overall Score, Critical, Major, Minor counts)."""

    @staticmethod
    def compute_score(violations: list[ComplianceViolation]) -> ComplianceScore:
        """
        Compute multi-dimensional compliance score.

        Returns:
            ComplianceScore object.
        """
        crit = sum(1 for v in violations if v.severity == ViolationSeverity.CRITICAL)
        maj = sum(1 for v in violations if v.severity == ViolationSeverity.MAJOR)
        min_c = sum(1 for v in violations if v.severity == ViolationSeverity.MINOR)

        # Deduct score: Critical = -20, Major = -10, Minor = -5
        penalty = (crit * 20.0) + (maj * 10.0) + (min_c * 5.0)
        overall = min(100.0, max(0.0, round(100.0 - penalty, 1)))

        return ComplianceScore(
            overall_score=overall,
            critical_violations_count=crit,
            major_violations_count=maj,
            minor_violations_count=min_c,
            confidence=0.96,
        )
