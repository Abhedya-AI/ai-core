"""propagation.py — Graph Intelligence Risk Propagation Integration."""

from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.graph_intelligence import IntelligenceService

log = get_logger("agents.risk.propagation")


class RiskPropagationEngine:
    """Uses Graph Intelligence Engine to calculate multi-hop risk decay and affected entities."""

    @staticmethod
    def propagate(target_id: str, graph_adj: dict[str, list[str]], initial_risk: float = 90.0) -> tuple[list[str], dict[str, float]]:
        """
        Execute risk propagation over target asset graph.

        Returns:
            tuple[affected_node_ids, propagated_scores_dict]
        """
        if not target_id or not graph_adj:
            log.debug("Target ID or Graph Adjacency empty for risk propagation")
            return [target_id] if target_id else [], {target_id: initial_risk} if target_id else {}

        report = IntelligenceService.analyze_risk_propagation(
            root_hazard_id=target_id,
            graph_adj_list=graph_adj,
            initial_risk=initial_risk,
        )
        return report.affected_node_ids, report.propagated_risk_scores
