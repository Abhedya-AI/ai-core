from typing import Dict, List, Optional
from app.core.logging import get_logger
from app.modules.incidents.models import Incident
from app.api.exceptions import NotFoundError

log = get_logger("app.modules.incidents.incident_repository")

class IncidentRepository:
    """
    Persists incidents and timeline events (In-memory implementation for demonstration).
    """

    def __init__(self):
        self._storage: Dict[str, Incident] = {}

    async def save(self, incident: Incident) -> Incident:
        """
        Save an incident to the repository.
        """
        self._storage[incident.incident_id] = incident
        log.debug(f"Saved incident {incident.incident_id}")
        return incident

    async def get_by_id(self, incident_id: str) -> Optional[Incident]:
        """
        Retrieve an incident by ID.
        """
        return self._storage.get(incident_id)

    async def get_by_id_or_raise(self, incident_id: str) -> Incident:
        """
        Retrieve an incident by ID or raise NotFoundError.
        """
        incident = await self.get_by_id(incident_id)
        if not incident:
            log.warning(f"Incident not found: {incident_id}")
            raise NotFoundError(f"Incident {incident_id} not found")
        return incident

    async def list_all(self) -> List[Incident]:
        """
        List all incidents.
        """
        return list(self._storage.values())
        
    async def list_by_state(self, state: str) -> List[Incident]:
        """
        List incidents by state.
        """
        return [inc for inc in self._storage.values() if inc.state.value == state]
