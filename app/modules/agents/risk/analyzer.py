"""analyzer.py — Evidence Collection Engine for Risk Assessment."""

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.risk.models import RiskEvidence

log = get_logger("agents.risk.analyzer")


class RiskAnalyzer:
    """Collects multi-source risk evidence from context, graph, sensors, and maintenance logs."""

    @staticmethod
    def gather_evidence(context: AgentContext) -> RiskEvidence:
        """Gather evidence from AgentContext."""
        log.info(f"Gathering risk evidence for task '{context.task_id}'")

        graph_facts = []
        if context.graph_snapshot:
            for k, v in context.graph_snapshot.items():
                graph_facts.append({"node_id": k, "connected_to": v})

        return RiskEvidence(
            graph_facts=graph_facts,
            sensor_readings=context.sensor_data or [],
            maintenance_logs=context.metadata.get("maintenance_logs", []),
            permits=context.metadata.get("permits", []),
            incidents=context.metadata.get("incidents", []),
            vision_events=context.vision_events or [],
        )
