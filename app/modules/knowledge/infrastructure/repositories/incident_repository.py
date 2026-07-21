"""incident_repository.py — Domain repository for Incident operations."""

from typing import Any

from app.modules.knowledge.domain.entities.incident import Incident
from app.modules.knowledge.infrastructure.cypher import incidents as cypher
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository


class IncidentRepository(BaseNeo4jRepository):
    """Domain repository for Incident operations."""

    async def create_incident(self, incident: Incident) -> dict[str, Any]:
        """Create a new Incident node."""
        props = incident.to_graph_properties()
        records = await self.execute_query(
            cypher.CREATE_INCIDENT,
            {"properties": props},
        )
        return records[0].get("i", props) if records else props

    async def get_incident_timeline(self, incident_id: str) -> dict[str, Any] | None:
        """Fetch full graph context and timeline of an incident."""
        records = await self.execute_query(cypher.GET_INCIDENT_TIMELINE, {"incident_id": incident_id})
        if records and "i" in records[0]:
            rec = records[0]
            inc = dict(rec["i"]._properties) if hasattr(rec["i"], "_properties") else dict(rec["i"])
            inc["hazards"] = [dict(h._properties) if hasattr(h, "_properties") else dict(h) for h in rec.get("hazards", [])]
            inc["affected_workers"] = [dict(w._properties) if hasattr(w, "_properties") else dict(w) for w in rec.get("affected_workers", [])]
            return inc
        return None

    async def get_affected_workers(self, incident_id: str) -> list[dict[str, Any]]:
        """Fetch all workers affected by an incident."""
        records = await self.execute_query(cypher.GET_AFFECTED_WORKERS, {"incident_id": incident_id})
        return [dict(r["w"]._properties) if hasattr(r["w"], "_properties") else dict(r["w"]) for r in records if "w" in r]
