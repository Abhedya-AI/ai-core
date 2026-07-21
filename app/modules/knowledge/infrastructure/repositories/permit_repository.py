"""permit_repository.py — Domain repository for Permit operations."""

from typing import Any

from app.modules.knowledge.domain.entities.permit import Permit
from app.modules.knowledge.infrastructure.cypher import permits as cypher
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository


class PermitRepository(BaseNeo4jRepository):
    """Domain repository for Permit operations."""

    async def create_permit(self, permit: Permit) -> dict[str, Any]:
        """Create a new Permit node."""
        props = permit.to_graph_properties()
        records = await self.execute_query(
            cypher.CREATE_PERMIT,
            {"properties": props},
        )
        return records[0].get("p", props) if records else props

    async def get_permits_in_zone(self, zone_id: str) -> list[dict[str, Any]]:
        """Fetch all permits issued for a zone."""
        records = await self.execute_query(cypher.PERMITS_IN_ZONE, {"zone_id": zone_id})
        return [dict(r["p"]._properties) if hasattr(r["p"], "_properties") else dict(r["p"]) for r in records if "p" in r]

    async def get_active_permits_for_worker(self, worker_id: str) -> list[dict[str, Any]]:
        """Fetch all active permits assigned to a worker."""
        records = await self.execute_query(cypher.ACTIVE_PERMITS_FOR_WORKER, {"worker_id": worker_id})
        return [dict(r["p"]._properties) if hasattr(r["p"], "_properties") else dict(r["p"]) for r in records if "p" in r]
