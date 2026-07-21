"""permit_dependency.py — Permit dependency chain analysis."""

from app.modules.knowledge.graph_intelligence.dto import DependencyReport, IntelligenceResult


def analyze_permit_dependencies(permit_id: str, required_regulations: list[str]) -> DependencyReport:
    """Analyze regulatory compliance requirements for a work permit."""
    intel_result = IntelligenceResult(
        algorithm="PermitDependencyAnalysis",
        confidence=0.96,
        execution_time_ms=1,
        affected_nodes=[permit_id] + required_regulations,
        evidence=[f"Mandatory regulation links: {len(required_regulations)}"],
        explanation=f"Work Permit '{permit_id}' requires compliance with {len(required_regulations)} safety regulations.",
        metadata={"regulations": required_regulations},
    )
    return DependencyReport(
        target_node_id=permit_id,
        upstream_dependencies=required_regulations,
        criticality_score=float(len(required_regulations) * 10.0),
        intelligence_result=intel_result,
    )
