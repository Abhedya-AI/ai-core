import uuid
from typing import List, Optional, Union
from app.core.logging import get_logger
from app.modules.incidents.models import Incident, IncidentState, IncidentSeverity
from app.modules.incidents.incident_repository import IncidentRepository
from app.modules.incidents.incident_state_machine import IncidentStateMachine
from app.modules.incidents.incident_timeline import IncidentTimelineTracker
from app.modules.incidents.incident_report_generator import IncidentReportGenerator
from app.api.exceptions import ValidationError

log = get_logger("app.modules.incidents.incident_service")

class IncidentService:
    """
    High-level domain service for incident management.
    """

    def __init__(
        self,
        repository: IncidentRepository,
        state_machine: IncidentStateMachine,
        timeline_tracker: IncidentTimelineTracker,
        report_generator: IncidentReportGenerator
    ):
        self.repository = repository
        self.state_machine = state_machine
        self.timeline_tracker = timeline_tracker
        self.report_generator = report_generator

    async def create_incident(self, title: str, description: str, severity: IncidentSeverity = IncidentSeverity.LOW) -> Incident:
        """
        Create a new incident and persist it.
        """
        incident_id = str(uuid.uuid4())
        incident = Incident(
            incident_id=incident_id,
            title=title,
            description=description,
            state=IncidentState.DETECTED,
            severity=severity
        )
        
        await self.timeline_tracker.record_event(
            incident=incident,
            event_type="INCIDENT_CREATED",
            description=f"Incident '{title}' detected."
        )
        
        await self.repository.save(incident)
        log.info(f"Created new incident {incident_id}")
        return incident

    async def transition_incident_state(self, incident_id: str, new_state: IncidentState, reason: str = "") -> Incident:
        """
        Transition an incident's state and record the event.
        """
        incident = await self.repository.get_by_id_or_raise(incident_id)
        old_state = incident.state
        
        try:
            incident = await self.state_machine.transition(incident, new_state)
        except ValueError as e:
            raise ValidationError(str(e))
            
        await self.timeline_tracker.record_state_change(
            incident=incident,
            old_state=old_state,
            new_state=new_state,
            reason=reason
        )
        
        await self.repository.save(incident)
        return incident
        
    async def add_note(self, incident_id: str, note: str, author: str) -> Incident:
        """
        Add a note to the incident timeline.
        """
        incident = await self.repository.get_by_id_or_raise(incident_id)
        await self.timeline_tracker.record_event(
            incident=incident,
            event_type="NOTE_ADDED",
            description=note,
            metadata={"author": author}
        )
        await self.repository.save(incident)
        return incident

    async def generate_report(self, incident_id: str, format: str = "markdown") -> Union[str, bytes]:
        """
        Generate a report for the incident in the specified format.
        """
        incident = await self.repository.get_by_id_or_raise(incident_id)
        if format.lower() == "pdf":
            return await self.report_generator.generate_pdf_report(incident)
        return await self.report_generator.generate_markdown_report(incident)
        
    async def get_incident(self, incident_id: str) -> Incident:
        """
        Get an incident by ID.
        """
        return await self.repository.get_by_id_or_raise(incident_id)

    async def list_incidents(self) -> List[Incident]:
        """
        List all incidents.
        """
        return await self.repository.list_all()
