import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from app.core.logging import get_logger
from app.modules.incidents.models import Incident, IncidentTimelineEvent, IncidentState

log = get_logger("app.modules.incidents.incident_timeline")

class IncidentTimelineTracker:
    """
    Records chronological incident events and state changes.
    """

    async def record_event(self, incident: Incident, event_type: str, description: str, metadata: Dict[str, Any] = None) -> IncidentTimelineEvent:
        """
        Record a generic event on the incident timeline.
        """
        event = IncidentTimelineEvent(
            event_id=str(uuid.uuid4()),
            incident_id=incident.incident_id,
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            description=description,
            metadata=metadata or {}
        )
        incident.timeline.append(event)
        incident.updated_at = datetime.now(timezone.utc)
        log.info(f"Recorded event {event_type} for incident {incident.incident_id}")
        return event

    async def record_state_change(self, incident: Incident, old_state: IncidentState, new_state: IncidentState, reason: str = "") -> IncidentTimelineEvent:
        """
        Record a state change event.
        """
        description = f"State changed from {old_state.value} to {new_state.value}"
        if reason:
            description += f": {reason}"
            
        metadata = {
            "old_state": old_state.value,
            "new_state": new_state.value,
            "reason": reason
        }
        
        return await self.record_event(
            incident=incident,
            event_type="STATE_CHANGE",
            description=description,
            metadata=metadata
        )
