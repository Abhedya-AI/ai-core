"""
use_cases/relationship_use_cases.py — Relationship Management Use Cases.

Implements Clean Architecture use cases for creating and deleting relationship edges.
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.modules.knowledge.application.dto.graph_query import CreateRelationshipRequest
from app.modules.knowledge.events.graph_events import publish_relationship_created
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository

log = get_logger("knowledge.use_case.relationships")


class CreateRelationshipUseCase:
    """Use case: Create a directed relationship edge between two nodes."""

    def __init__(self, repo: BaseNeo4jRepository | None = None) -> None:
        self._repo = repo or BaseNeo4jRepository()

    async def execute(self, request: CreateRelationshipRequest) -> bool:
        """Create relationship edge and publish event."""
        created = await self._repo.create_relationship(request)

        if created:
            rel_type_str = (
                request.rel_type.value if hasattr(request.rel_type, "value") else str(request.rel_type)
            )
            await publish_relationship_created(
                source_id=request.source_id,
                target_id=request.target_id,
                rel_type=rel_type_str,
                properties=request.properties,
            )
            log.info(
                f"CreateRelationshipUseCase: ({request.source_id})-"
                f"[{rel_type_str}]->({request.target_id})"
            )

        return created


class DeleteRelationshipUseCase:
    """Use case: Delete a relationship edge between two nodes."""

    def __init__(self, repo: BaseNeo4jRepository | None = None) -> None:
        self._repo = repo or BaseNeo4jRepository()

    async def execute(self, source_id: str, rel_type: str, target_id: str) -> bool:
        """Delete relationship edge."""
        deleted = await self._repo.delete_relationship(source_id, rel_type, target_id)
        if deleted:
            log.info(f"DeleteRelationshipUseCase: Deleted ({source_id})-[{rel_type}]->({target_id})")
        return deleted
