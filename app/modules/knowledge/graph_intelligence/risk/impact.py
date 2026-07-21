"""impact.py — Asset risk impact scoring."""

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def calculate_risk_impact(node_id: str, connected_nodes_count: int, criticality_weight: float = 1.5) -> IntelligenceResult:
    """Calculate overall risk impact score for a node."""
    impact_score = min(100.0, round(connected_nodes_count * 12.5 * criticality_weight, 2))
    return IntelligenceResult(
        algorithm="RiskImpact",
        confidence=0.95,
        execution_time_ms=1,
        affected_nodes=[node_id],
        evidence=[f"Connected count: {connected_nodes_count}", f"Weight: {criticality_weight}"],
        explanation=f"Node '{node_id}' has a calculated risk impact score of {impact_score}/100.",
        metadata={"impact_score": impact_score},
    )
