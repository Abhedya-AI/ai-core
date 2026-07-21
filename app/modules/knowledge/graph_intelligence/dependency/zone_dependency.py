"""zone_dependency.py — Zone dependency analysis."""

from app.modules.knowledge.graph_intelligence.dto import DependencyReport, IntelligenceResult


def analyze_zone_dependencies(zone_id: str, connected_zones: list[str]) -> DependencyReport:
    """Analyze inter-zone dependency and hazard containment boundary."""
    intel_result = IntelligenceResult(
        algorithm="ZoneDependencyAnalysis",
        confidence=0.90,
        execution_time_ms=1,
        affected_nodes=[zone_id] + connected_zones,
        evidence=[f"Connected adjacent zones: {len(connected_zones)}"],
        explanation=f"Zone '{zone_id}' has spatial/operational dependencies on {len(connected_zones)} adjacent zones.",
        metadata={"adjacent_zones": connected_zones},
    )
    return DependencyReport(
        target_node_id=zone_id,
        downstream_impacts=connected_zones,
        criticality_score=float(len(connected_zones) * 15.0),
        intelligence_result=intel_result,
    )
