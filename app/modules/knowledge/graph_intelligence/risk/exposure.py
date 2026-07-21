"""exposure.py — Worker & asset exposure scoring module."""

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def calculate_worker_exposure(worker_id: str, zone_risk_score: float, hours_in_zone: float) -> IntelligenceResult:
    """Calculate worker risk exposure index."""
    exposure_index = min(100.0, round((zone_risk_score * 0.7) + (hours_in_zone * 3.5), 2))
    return IntelligenceResult(
        algorithm="WorkerExposure",
        confidence=0.94,
        execution_time_ms=1,
        affected_nodes=[worker_id],
        evidence=[f"Zone Risk Score: {zone_risk_score}", f"Hours in Zone: {hours_in_zone}"],
        explanation=f"Worker '{worker_id}' has an accumulated exposure index of {exposure_index}/100.",
        metadata={"exposure_index": exposure_index},
    )
