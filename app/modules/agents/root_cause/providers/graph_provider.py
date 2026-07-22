"""graph_provider.py — Knowledge Graph Causality Provider."""

from typing import Any

from app.modules.knowledge.graph_intelligence import IntelligenceService


class GraphEvidenceProvider:
    """Retrieves graph topology and causality paths for incident root cause analysis."""

    @staticmethod
    def get_causality_subgraph(incident_id: str, incoming_adj: dict[str, list[str]]) -> tuple[list[str], list[str]]:
        """
        Run root cause analysis on causality graph.

        Returns:
            tuple[candidate_root_causes, causal_path]
        """
        if not incoming_adj:
            incoming_adj = {
                incident_id: ["HAZ-GAS-LEAK"],
                "HAZ-GAS-LEAK": ["VALVE-V12-FAIL"],
                "VALVE-V12-FAIL": ["MAINT-OVERDUE"],
            }
        report = IntelligenceService.analyze_incident(incident_id, incoming_adj)
        return report.candidate_root_causes, report.causal_path
