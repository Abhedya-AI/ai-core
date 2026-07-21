"""asset_dependency.py — Asset dependency & impact analysis engine."""

import time

from app.modules.knowledge.graph_intelligence.dto import DependencyReport, IntelligenceResult


def analyze_asset_dependencies(
    downstream_adj: dict[str, list[str]],
    upstream_adj: dict[str, list[str]],
    target_asset_id: str,
) -> DependencyReport:
    """
    Analyze upstream dependencies and downstream failure impacts of an asset.

    Question: "If Pump A fails, what else breaks?"
    """
    start_time = time.perf_counter()

    downstream_impacts = downstream_adj.get(target_asset_id, [])
    upstream_dependencies = upstream_adj.get(target_asset_id, [])

    criticality_score = min(100.0, round((len(downstream_impacts) * 20.0) + (len(upstream_dependencies) * 10.0), 2))
    exec_time = int((time.perf_counter() - start_time) * 1000)

    intel_result = IntelligenceResult(
        algorithm="AssetDependencyAnalysis",
        confidence=0.95,
        execution_time_ms=exec_time,
        affected_nodes=[target_asset_id] + downstream_impacts + upstream_dependencies,
        evidence=[
            f"Downstream impacted assets: {len(downstream_impacts)}",
            f"Upstream required assets: {len(upstream_dependencies)}",
        ],
        explanation=(
            f"Asset '{target_asset_id}' failure directly impacts {len(downstream_impacts)} downstream assets "
            f"and depends on {len(upstream_dependencies)} upstream components. Criticality score: {criticality_score}/100."
        ),
        metadata={
            "upstream": upstream_dependencies,
            "downstream": downstream_impacts,
            "criticality": criticality_score,
        },
    )

    return DependencyReport(
        target_node_id=target_asset_id,
        upstream_dependencies=upstream_dependencies,
        downstream_impacts=downstream_impacts,
        criticality_score=criticality_score,
        intelligence_result=intel_result,
    )
