"""severity.py — Severity scoring module."""

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def calculate_severity_score(hazard_level: str, likelihood: float) -> IntelligenceResult:
    """Calculate combined severity score."""
    base_scores = {"LOW": 25.0, "MEDIUM": 50.0, "HIGH": 75.0, "CRITICAL": 100.0}
    base = base_scores.get(hazard_level.upper(), 50.0)
    score = min(100.0, round(base * likelihood, 2))
    return IntelligenceResult(
        algorithm="SeverityScoring",
        confidence=1.0,
        execution_time_ms=1,
        evidence=[f"Hazard Level: {hazard_level}", f"Likelihood: {likelihood}"],
        explanation=f"Combined severity score is {score}/100 based on level '{hazard_level}' and likelihood {likelihood}.",
        metadata={"severity_score": score},
    )
