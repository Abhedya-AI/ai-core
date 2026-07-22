"""confidence.py — Compliance Confidence Engine."""

from app.modules.agents.compliance.models import ComplianceEvidence


class ComplianceConfidenceEngine:
    """Computes overall audit confidence based on evidence completeness."""

    @staticmethod
    def compute_confidence(evidence: ComplianceEvidence) -> float:
        base = 0.85
        if evidence.permits:
            base += 0.05
        if evidence.sops:
            base += 0.05
        if evidence.regulations:
            base += 0.03
        return min(0.99, round(base, 2))
