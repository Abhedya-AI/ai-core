"""collector.py — Phase 1: Evidence Collection Engine."""

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.root_cause.models import EvidenceBundle
from app.modules.agents.root_cause.providers import (
    GraphEvidenceProvider,
    HistoricalEvidenceProvider,
    MaintenanceEvidenceProvider,
    RegulationEvidenceProvider,
    SensorEvidenceProvider,
    VisionEvidenceProvider,
)

log = get_logger("agents.root_cause.collector")


class EvidenceCollector:
    """Phase 1: Collects multi-source evidence from Graph, Sensors, Vision, Maintenance, and Regulations."""

    @staticmethod
    def collect_evidence(context: AgentContext) -> EvidenceBundle:
        incident_id = context.target_entity_id or "INC-01"
        log.info(f"Collecting evidence bundle for incident '{incident_id}'")

        graph_roots, graph_path = GraphEvidenceProvider.get_causality_subgraph(incident_id, context.graph_snapshot)
        sensor_timeline = SensorEvidenceProvider.get_sensor_timeline(context.sensor_data)
        maintenance_recs = MaintenanceEvidenceProvider.get_maintenance_evidence(context.metadata)
        vision_dets = VisionEvidenceProvider.get_vision_evidence(context.vision_events)
        regulations = RegulationEvidenceProvider.get_regulatory_rules()
        historical = HistoricalEvidenceProvider.get_historical_incidents(incident_id)

        graph_facts = [
            {"type": "candidate_root_cause", "node": r} for r in graph_roots
        ] + [{"type": "causal_path_node", "node": p} for p in graph_path]

        return EvidenceBundle(
            incident_id=incident_id,
            graph_facts=graph_facts,
            sensor_timeline=sensor_timeline,
            vision_detections=vision_dets,
            maintenance_records=maintenance_recs,
            permits=context.metadata.get("permits", []),
            historical_incidents=historical,
            regulatory_rules=regulations,
        )
