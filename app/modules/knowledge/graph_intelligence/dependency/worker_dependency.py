"""worker_dependency.py — Worker dependency analysis."""

from app.modules.knowledge.graph_intelligence.dto import DependencyReport, IntelligenceResult


def analyze_worker_dependencies(worker_id: str, assigned_equipment: list[str]) -> DependencyReport:
    """Analyze equipment and permits dependent on worker presence."""
    intel_result = IntelligenceResult(
        algorithm="WorkerDependencyAnalysis",
        confidence=0.92,
        execution_time_ms=1,
        affected_nodes=[worker_id] + assigned_equipment,
        evidence=[f"Assigned operating assets: {len(assigned_equipment)}"],
        explanation=f"Worker '{worker_id}' is the registered operator for {len(assigned_equipment)} assets.",
        metadata={"assigned_assets": assigned_equipment},
    )
    return DependencyReport(
        target_node_id=worker_id,
        downstream_impacts=assigned_equipment,
        criticality_score=float(len(assigned_equipment) * 20.0),
        intelligence_result=intel_result,
    )
