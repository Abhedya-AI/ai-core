"""
intelligence_service.py — Master Orchestrator for the Graph Intelligence Engine.

Unifies traversal algorithms, risk propagation, causal reasoning, dependency analysis,
and explainability into a single high-level reasoning interface for GraphRAG and AI Agents.
"""

from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.graph_intelligence.algorithms.centrality import compute_centrality
from app.modules.knowledge.graph_intelligence.algorithms.pagerank import compute_pagerank
from app.modules.knowledge.graph_intelligence.causality.root_cause import find_root_causes
from app.modules.knowledge.graph_intelligence.dependency.asset_dependency import analyze_asset_dependencies
from app.modules.knowledge.graph_intelligence.dto import (
    CausalReport,
    DependencyReport,
    IntelligenceResult,
    RiskAnalysisReport,
)
from app.modules.knowledge.graph_intelligence.explainability.explanations import (
    format_causal_explanation,
    format_risk_explanation,
)
from app.modules.knowledge.graph_intelligence.risk.propagation import propagate_risk

log = get_logger("knowledge.graph_intelligence.service")


class IntelligenceService:
    """
    Master orchestrator service for graph intelligence.

    Single point of entry for graph algorithms, risk propagation, root cause analysis,
    dependency tracking, and explainability report generation.
    """

    @staticmethod
    def analyze_incident(
        incident_id: str,
        incoming_causality_adj: dict[str, list[str]],
    ) -> CausalReport:
        """
        Orchestrate comprehensive incident analysis:
        1. Root Cause Search
        2. Causal Path Reconstruction
        3. Human-readable XAI Explanation
        """
        log.info(f"Running incident intelligence analysis for '{incident_id}'")
        report = find_root_causes(incoming_causality_adj, incident_id)

        # Generate human-readable explanation
        explanation = format_causal_explanation(
            incident_id=incident_id,
            root_causes=report.candidate_root_causes,
            causal_path=report.causal_path,
        )
        report.intelligence_result.explanation = explanation
        return report

    @staticmethod
    def analyze_risk_propagation(
        root_hazard_id: str,
        graph_adj_list: dict[str, list[str]],
        initial_risk: float = 100.0,
    ) -> RiskAnalysisReport:
        """
        Orchestrate risk propagation analysis:
        1. Edge risk decay propagation
        2. Affected node extraction
        3. Human-readable XAI Explanation
        """
        log.info(f"Running risk propagation analysis for hazard '{root_hazard_id}'")
        report = propagate_risk(graph_adj_list, root_hazard_id, initial_risk=initial_risk)

        explanation = format_risk_explanation(
            target_node_id=root_hazard_id,
            risk_score=initial_risk,
            root_hazard=root_hazard_id,
            contributing_factors=[f"Propagated to {len(report.affected_node_ids)} connected entities"],
        )
        report.intelligence_result.explanation = explanation
        return report

    @staticmethod
    def analyze_asset_criticality(
        asset_id: str,
        graph_adj_list: dict[str, list[str]],
        downstream_adj: dict[str, list[str]],
        upstream_adj: dict[str, list[str]],
    ) -> DependencyReport:
        """
        Orchestrate industrial asset criticality calculation:
        1. Dependency analysis (upstream & downstream)
        2. PageRank & Centrality metrics
        3. Industrial Criticality Score calculation
        """
        log.info(f"Analyzing asset criticality for '{asset_id}'")

        # 1. Dependency Analysis
        dep_report = analyze_asset_dependencies(downstream_adj, upstream_adj, asset_id)

        # 2. Centrality & PageRank
        centrality_res = compute_centrality(graph_adj_list)
        pagerank_res = compute_pagerank(graph_adj_list)

        deg_map = centrality_res.metadata.get("total_degree", {})
        rank_map = pagerank_res.metadata.get("ranks", {})

        asset_degree = deg_map.get(asset_id, 0)
        asset_rank = rank_map.get(asset_id, 0.0)

        # Combine metrics into Industrial Criticality Score
        industrial_score = min(
            100.0,
            round(dep_report.criticality_score + (asset_degree * 5.0) + (asset_rank * 100.0), 2),
        )

        dep_report.criticality_score = industrial_score
        dep_report.intelligence_result.explanation = (
            f"Asset '{asset_id}' has an Industrial Criticality Score of {industrial_score}/100 "
            f"(Degree: {asset_degree}, PageRank: {asset_rank:.4f}, Downstream Impacts: {len(dep_report.downstream_impacts)})."
        )
        return dep_report
