"""
knowledge_service.py — Knowledge Facade Service.

Orchestrates multi-domain industrial safety workflows spanning Workers, Equipment,
Sensors, Hazards, Incidents, and Permits.
"""

from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.domain.entities.equipment import Equipment
from app.modules.knowledge.domain.entities.hazard import Hazard
from app.modules.knowledge.domain.entities.incident import Incident
from app.modules.knowledge.domain.entities.permit import Permit
from app.modules.knowledge.domain.entities.sensor import Sensor
from app.modules.knowledge.domain.entities.worker import Worker
from app.modules.knowledge.domain.entities.zone import Zone
from app.modules.knowledge.domain.relationships import RelationshipType
from app.modules.knowledge.services.equipment_service import EquipmentService
from app.modules.knowledge.services.graph_service import GraphService
from app.modules.knowledge.services.hazard_service import HazardService
from app.modules.knowledge.services.incident_service import IncidentService
from app.modules.knowledge.services.permit_service import PermitService
from app.modules.knowledge.services.sensor_service import SensorService
from app.modules.knowledge.services.worker_service import WorkerService

log = get_logger("knowledge.services.facade")


class KnowledgeService:
    """
    Facade service orchestrating cross-domain safety workflows.

    Coordinates transactions, validations, and relationship creation
    across domain services without leaking database or repository details.
    """

    def __init__(
        self,
        worker_svc: WorkerService | None = None,
        equipment_svc: EquipmentService | None = None,
        sensor_svc: SensorService | None = None,
        hazard_svc: HazardService | None = None,
        incident_svc: IncidentService | None = None,
        permit_svc: PermitService | None = None,
        graph_svc: GraphService | None = None,
    ) -> None:
        self.workers = worker_svc or WorkerService()
        self.equipment = equipment_svc or EquipmentService()
        self.sensors = sensor_svc or SensorService()
        self.hazards = hazard_svc or HazardService()
        self.incidents = incident_svc or IncidentService()
        self.permits = permit_svc or PermitService()
        self.graph = graph_svc or GraphService()

    async def report_hazard_on_equipment(
        self,
        hazard: Hazard,
        equipment: Equipment,
    ) -> dict[str, Any]:
        """Workflow: Report a hazard, persist it, and link it to the target equipment."""
        # 1. Report hazard
        haz_data = await self.hazards.report_hazard(hazard)
        # 2. Connect (Hazard) -[:CAUSES|AFFECTS]-> (Equipment)
        await self.graph.connect_entities(
            source=hazard,
            target=equipment,
            rel_type=RelationshipType.AFFECTS,
        )
        log.info(f"Workflow: Reported hazard {hazard.id} affecting equipment {equipment.code}")
        return haz_data

    async def register_sensor_on_equipment(
        self,
        equipment: Equipment,
        sensor: Sensor,
    ) -> bool:
        """Workflow: Register a sensor and attach it to equipment."""
        return await self.equipment.attach_sensor_to_equipment(equipment.id, sensor)

    async def report_incident_with_hazard(
        self,
        incident: Incident,
        hazard: Hazard,
        affected_workers: list[Worker] | None = None,
    ) -> dict[str, Any]:
        """Workflow: Report an incident, link originating hazard, and link affected workers."""
        incident.originating_hazard_id = hazard.id
        inc_data = await self.incidents.report_incident(incident)

        # Connect Hazard -> Incident
        await self.graph.connect_entities(
            source=hazard,
            target=incident,
            rel_type=RelationshipType.LEADS_TO,
        )

        # Connect Incident -> Workers
        if affected_workers:
            for w in affected_workers:
                await self.graph.connect_entities(
                    source=incident,
                    target=w,
                    rel_type=RelationshipType.AFFECTS,
                )

        log.info(f"Workflow: Reported incident {incident.id} linked to hazard {hazard.id}")
        return inc_data

    async def issue_work_permit(
        self,
        permit: Permit,
        worker: Worker,
        zone: Zone,
    ) -> dict[str, Any]:
        """Workflow: Issue work permit, validate worker zone access, and assign permit."""
        # 1. Validate worker zone access
        self.workers.assign_worker_to_zone(worker, zone)
        # 2. Issue permit
        permit_data = await self.permits.issue_permit(permit)
        # 3. Connect Permit -> Worker
        await self.graph.connect_entities(
            source=permit,
            target=worker,
            rel_type=RelationshipType.ASSIGNED_TO,
        )
        return permit_data
