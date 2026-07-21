"""worker_repository.py — Domain repository for Worker operations."""

from datetime import datetime, timezone
from typing import Any

from app.modules.knowledge.domain.entities.worker import Worker
from app.modules.knowledge.domain.relationships import RelationshipType
from app.modules.knowledge.infrastructure.cypher import workers as cypher
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository


class WorkerRepository(BaseNeo4jRepository):
    """Domain repository for Worker operations."""

    async def create_worker(self, worker: Worker) -> dict[str, Any]:
        """Create or merge a Worker entity."""
        props = worker.to_graph_properties()
        records = await self.execute_query(
            cypher.CREATE_WORKER,
            {
                "id": worker.id,
                "badge_number": worker.badge_number,
                "properties": props,
            },
        )
        return records[0].get("w", props) if records else props

    async def find_by_badge(self, badge_number: str) -> dict[str, Any] | None:
        """Find a Worker node by badge number."""
        records = await self.execute_query(cypher.GET_WORKER_BY_BADGE, {"badge_number": badge_number})
        if records and "w" in records[0]:
            w = records[0]["w"]
            return dict(w._properties) if hasattr(w, "_properties") else dict(w)
        return None

    async def get_workers_in_zone(self, zone_id: str) -> list[dict[str, Any]]:
        """Get all workers currently assigned to or working in a zone."""
        records = await self.execute_query(cypher.WORKERS_IN_ZONE, {"zone_id": zone_id})
        return [dict(r["w"]._properties) if hasattr(r["w"], "_properties") else dict(r["w"]) for r in records if "w" in r]

    async def assign_zone(self, worker_id: str, zone_id: str) -> bool:
        """Create a WORKS_IN relationship from Worker to Zone."""
        records = await self.execute_query(
            cypher.ASSIGN_WORKER_ZONE,
            {
                "worker_id": worker_id,
                "zone_id": zone_id,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            },
        )
        return bool(records)
