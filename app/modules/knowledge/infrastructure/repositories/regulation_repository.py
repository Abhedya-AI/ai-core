"""regulation_repository.py — Domain repository for Regulation operations."""

from typing import Any

from app.modules.knowledge.domain.entities.regulation import Regulation
from app.modules.knowledge.infrastructure.cypher import regulations as cypher
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository


class RegulationRepository(BaseNeo4jRepository):
    """Domain repository for Regulation operations."""

    async def create_regulation(self, regulation: Regulation) -> dict[str, Any]:
        """Create or merge a Regulation node."""
        props = regulation.to_graph_properties()
        records = await self.execute_query(
            cypher.CREATE_REGULATION,
            {
                "id": regulation.id,
                "code": regulation.code,
                "properties": props,
            },
        )
        return records[0].get("r", props) if records else props

    async def get_regulations_for_hazard(self, hazard_id: str) -> list[dict[str, Any]]:
        """Fetch regulations referenced by or mitigating a hazard."""
        records = await self.execute_query(cypher.REGULATIONS_FOR_HAZARD, {"hazard_id": hazard_id})
        return [dict(r["r"]._properties) if hasattr(r["r"], "_properties") else dict(r["r"]) for r in records if "r" in r]
