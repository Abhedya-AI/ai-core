"""graph_service.py — Graph-wide topology service."""

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.infrastructure.kafka.registry import Topics
from app.modules.knowledge.application.dto import CreateRelationshipRequest
from app.modules.knowledge.domain.entities.base import GraphEntity
from app.modules.knowledge.domain.ontology import validate_graph_edge
from app.modules.knowledge.domain.relationships import RelationshipType
from app.modules.knowledge.infrastructure.exceptions import OntologyValidationError
from app.modules.knowledge.infrastructure.repositories.graph_repository import Neo4jGraphRepository

log = get_logger("knowledge.services.graph")


class GraphService:
    """Service managing graph-wide topology, relationship edge creation, and entity connectivity."""

    def __init__(self, repository: Neo4jGraphRepository | None = None) -> None:
        self._repo = repository or Neo4jGraphRepository()
        self._event_bus = EventBus.get()

    async def connect_entities(
        self,
        source: GraphEntity,
        target: GraphEntity,
        rel_type: RelationshipType,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Connect two entities with a directed relationship after validating ontology edge rules."""
        if not validate_graph_edge(rel_type.value, source, target):
            raise OntologyValidationError(
                f"Relationship '{rel_type.value}' is not permitted between "
                f"source '{source.entity_type}' and target '{target.entity_type}'"
            )

        req = CreateRelationshipRequest(
            source_id=source.id,
            target_id=target.id,
            rel_type=rel_type,
            properties=properties or {},
        )
        success = await self._repo.create_relationship(req)
        if success:
            log.info(f"Connected ({source.entity_type}:{source.id}) -[:{rel_type.value}]-> ({target.entity_type}:{target.id})")
            await self._event_bus.publish(
                topic=Topics.GRAPH_RELATIONSHIP_CREATED,
                payload={
                    "rel_type": rel_type.value,
                    "source_id": source.id,
                    "target_id": target.id,
                },
                key=source.id,
            )
        return success

    async def get_neighbors(self, node_id: str) -> list[dict[str, Any]]:
        """Retrieve 1-hop connected neighbor entities."""
        return await self._repo.get_neighbors(node_id)

    async def get_node_degree(self, node_id: str) -> int:
        """Calculate total edge degree of a node."""
        return await self._repo.node_degree(node_id)

    async def get_graph_summary() -> dict[str, Any]:
        """Return total node count and connectivity status."""
        total_nodes = await self._repo.count()
        return {"total_nodes": total_nodes}
