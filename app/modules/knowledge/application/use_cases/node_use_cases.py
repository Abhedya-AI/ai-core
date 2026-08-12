"""
use_cases/node_use_cases.py — Node Management Use Cases.

Implements Clean Architecture use cases for creating, updating, deleting,
and finding Knowledge Graph nodes with automatic event publishing and snapshotting.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.application.dto.create_node import CreateNodeRequest
from app.modules.knowledge.application.dto.update_node import UpdateNodeRequest
from app.modules.knowledge.events.graph_events import (
    publish_node_created,
    publish_node_deleted,
    publish_node_updated,
)
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository
from app.modules.knowledge.services.graph_cache_service import GraphCacheService
from app.modules.knowledge.services.graph_history_service import GraphHistoryService

log = get_logger("knowledge.use_case.nodes")


class CreateNodeUseCase:
    """Use case: Create a new node in the Knowledge Graph with ontology validation."""

    def __init__(
        self,
        repo: BaseNeo4jRepository | None = None,
        cache: GraphCacheService | None = None,
    ) -> None:
        self._repo = repo or BaseNeo4jRepository()
        self._cache = cache or GraphCacheService()

    async def execute(self, request: CreateNodeRequest) -> dict[str, Any]:
        """Create node, publish event, and return created properties."""
        node_data = await self._repo.create_node(request)
        node_id = node_data.get("id", request.node_id or "")

        # Cache node
        if node_id:
            await self._cache.set_node(node_id, node_data)

        # Publish event
        await publish_node_created(node_id=node_id, label=request.label, properties=node_data)

        log.info(f"CreateNodeUseCase: Created node '{node_id}' [{request.label}]")
        return node_data


class UpdateNodeUseCase:
    """Use case: Update node properties, create a temporal snapshot, and publish event."""

    def __init__(
        self,
        repo: BaseNeo4jRepository | None = None,
        history: GraphHistoryService | None = None,
        cache: GraphCacheService | None = None,
    ) -> None:
        self._repo = repo or BaseNeo4jRepository()
        self._history = history or GraphHistoryService()
        self._cache = cache or GraphCacheService()

    async def execute(self, request: UpdateNodeRequest) -> dict[str, Any]:
        """Snapshot current state, update node, invalidate cache, publish event."""
        # Fetch current node state for snapshotting
        existing = await self._repo.find_by_id(request.node_id)
        if existing:
            label = existing.get("entity_type", request.label or "GraphEntity")
            await self._history.record_snapshot(
                node_id=request.node_id,
                node_label=label,
                properties=existing,
                change_summary="Pre-update snapshot",
            )

        updated_data = await self._repo.update_node(request)

        # Invalidate cache
        await self._cache.invalidate_node(request.node_id)

        # Publish event
        label = updated_data.get("entity_type", request.label or "GraphEntity")
        await publish_node_updated(
            node_id=request.node_id,
            label=label,
            changes=request.properties,
        )

        log.info(f"UpdateNodeUseCase: Updated node '{request.node_id}'")
        return updated_data


class DeleteNodeUseCase:
    """Use case: Detach and delete a node from the Knowledge Graph."""

    def __init__(
        self,
        repo: BaseNeo4jRepository | None = None,
        cache: GraphCacheService | None = None,
    ) -> None:
        self._repo = repo or BaseNeo4jRepository()
        self._cache = cache or GraphCacheService()

    async def execute(self, node_id: str, label: str = "GraphEntity", deleted_by: str = "user") -> bool:
        """Delete node, invalidate cache, publish event."""
        deleted = await self._repo.delete_node(node_id)

        if deleted:
            await self._cache.invalidate_node(node_id)
            await publish_node_deleted(node_id=node_id, label=label, deleted_by=deleted_by)
            log.info(f"DeleteNodeUseCase: Deleted node '{node_id}'")

        return deleted


class FindNodeUseCase:
    """Use case: Find a node by ID (checks cache first)."""

    def __init__(
        self,
        repo: BaseNeo4jRepository | None = None,
        cache: GraphCacheService | None = None,
    ) -> None:
        self._repo = repo or BaseNeo4jRepository()
        self._cache = cache or GraphCacheService()

    async def execute(self, node_id: str, label: str | None = None) -> dict[str, Any] | None:
        """Find node by ID."""
        # Check cache
        cached = await self._cache.get_node(node_id)
        if cached:
            return cached

        node_data = await self._repo.find_by_id(node_id, label=label)
        if node_data:
            await self._cache.set_node(node_id, node_data)

        return node_data
