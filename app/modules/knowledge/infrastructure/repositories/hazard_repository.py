"""hazard_repository.py — Domain repository for Hazard operations."""

from typing import Any

from app.modules.knowledge.domain.entities.hazard import Hazard
from app.modules.knowledge.infrastructure.cypher import hazards as cypher
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository


class HazardRepository(BaseNeo4jRepository):
    """Domain repository for Hazard operations."""

    async def create_hazard(self, hazard: Hazard) -> dict[str, Any]:
        """Create a new Hazard node."""
        props = hazard.to_graph_properties()
        records = await self.execute_query(
            cypher.CREATE_HAZARD,
            {"properties": props},
        )
        return records[0].get("h", props) if records else props

    async def get_active_hazards(self) -> list[dict[str, Any]]:
        """Fetch all unmitigated active hazards."""
        records = await self.execute_query(cypher.GET_ACTIVE_HAZARDS)
        return [dict(r["h"]._properties) if hasattr(r["h"], "_properties") else dict(r["h"]) for r in records if "h" in r]

    async def get_hazards_in_zone(self, zone_id: str) -> list[dict[str, Any]]:
        """Fetch all unmitigated hazards in a zone."""
        records = await self.execute_query(cypher.HAZARDS_IN_ZONE, {"zone_id": zone_id})
        return [dict(r["h"]._properties) if hasattr(r["h"], "_properties") else dict(r["h"]) for r in records if "h" in r]

    async def get_critical_hazards(self) -> list[dict[str, Any]]:
        """Fetch all unmitigated CRITICAL hazards."""
        records = await self.execute_query(cypher.CRITICAL_HAZARDS)
        return [dict(r["h"]._properties) if hasattr(r["h"], "_properties") else dict(r["h"]) for r in records if "h" in r]
