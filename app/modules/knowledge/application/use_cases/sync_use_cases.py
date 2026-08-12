"""
use_cases/sync_use_cases.py — Graph Synchronization Use Cases.

Implements Clean Architecture use cases for ingesting domain entity updates
and batch event syncs into Neo4j via MERGE upsert operations.
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.modules.knowledge.application.dto.sync_dto import (
    SyncBatchRequest,
    SyncNodeRequest,
    SyncResult,
)
from app.modules.knowledge.services.graph_sync_service import GraphSyncService

log = get_logger("knowledge.use_case.sync")


class SyncGraphNodeUseCase:
    """Use case: Upsert a single domain node and its relationships into Neo4j."""

    def __init__(self, service: GraphSyncService | None = None) -> None:
        self._service = service or GraphSyncService()

    async def execute(self, request: SyncNodeRequest) -> SyncResult:
        """Upsert single node."""
        return await self._service.sync_node(request)


class SyncGraphBatchUseCase:
    """Use case: Batch upsert domain nodes from a platform module."""

    def __init__(self, service: GraphSyncService | None = None) -> None:
        self._service = service or GraphSyncService()

    async def execute(self, request: SyncBatchRequest) -> SyncResult:
        """Batch upsert nodes."""
        return await self._service.sync_batch(request)
