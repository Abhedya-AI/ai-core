"""collector.py — Phase 1: Compliance Evidence Collection Engine."""

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.compliance.models import ComplianceEvidence
from app.modules.agents.compliance.providers import (
    GraphComplianceProvider,
    MaintenanceComplianceProvider,
    PermitProvider,
    RegulationProvider,
    SOPProvider,
    VisionComplianceProvider,
)

log = get_logger("agents.compliance.collector")


class ComplianceCollector:
    """Phase 1: Collects compliance evidence across permits, SOPs, regulations, certifications, and observations."""

    @staticmethod
    def collect_evidence(context: AgentContext) -> ComplianceEvidence:
        log.info(f"Collecting compliance evidence bundle for task '{context.task_id}'")

        permits = PermitProvider.get_permits(context.metadata)
        sops = SOPProvider.get_sops(context.metadata)
        regulations = RegulationProvider.get_regulations()
        maintenance = MaintenanceComplianceProvider.get_maintenance(context.metadata)
        vision_obs = VisionComplianceProvider.get_vision_observations(context.vision_events)
        graph_ctx = GraphComplianceProvider.get_graph_context(context.graph_snapshot)

        worker_certs = context.metadata.get(
            "worker_certifications",
            [
                {"worker_id": "W-101", "certification": "CONFINED_SPACE", "valid": False},
                {"worker_id": "W-102", "certification": "HOT_WORK_SAFETY", "valid": True},
            ],
        )

        return ComplianceEvidence(
            permits=permits,
            sops=sops,
            regulations=regulations,
            worker_certifications=worker_certs,
            maintenance_records=maintenance,
            vision_observations=vision_obs,
            graph_context=graph_ctx,
        )
