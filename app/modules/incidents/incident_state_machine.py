from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.core.logging import get_logger
from app.modules.incidents.models import Incident, IncidentState

log = get_logger("app.modules.incidents.incident_state_machine")

class IncidentStateMachine:
    """
    Manages the lifecycle transitions of an incident.
    """

    # Define valid transitions
    VALID_TRANSITIONS: Dict[IncidentState, List[IncidentState]] = {
        IncidentState.DETECTED: [IncidentState.VALIDATED, IncidentState.ARCHIVED],
        IncidentState.VALIDATED: [IncidentState.INVESTIGATING, IncidentState.EMERGENCY_ACTIVE, IncidentState.RESOLVED],
        IncidentState.INVESTIGATING: [IncidentState.EMERGENCY_ACTIVE, IncidentState.MITIGATION, IncidentState.RESOLVED],
        IncidentState.EMERGENCY_ACTIVE: [IncidentState.MITIGATION, IncidentState.RESOLVED],
        IncidentState.MITIGATION: [IncidentState.RESOLVED, IncidentState.EMERGENCY_ACTIVE],
        IncidentState.RESOLVED: [IncidentState.ARCHIVED, IncidentState.INVESTIGATING],
        IncidentState.ARCHIVED: []
    }

    async def can_transition(self, current_state: IncidentState, target_state: IncidentState) -> bool:
        """
        Check if a transition from current_state to target_state is allowed.
        """
        return target_state in self.VALID_TRANSITIONS.get(current_state, [])

    async def transition(self, incident: Incident, target_state: IncidentState) -> Incident:
        """
        Transition the incident to the target state if valid.
        """
        current_state = incident.state
        if not await self.can_transition(current_state, target_state):
            log.warning(f"Invalid transition from {current_state} to {target_state} for incident {incident.incident_id}")
            raise ValueError(f"Cannot transition from {current_state} to {target_state}")

        log.info(f"Transitioning incident {incident.incident_id} from {current_state} to {target_state}")
        incident.state = target_state
        incident.updated_at = datetime.now(timezone.utc)
        return incident
