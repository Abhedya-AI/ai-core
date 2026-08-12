"""
services/graph_sync_service.py — Graph Synchronization Service.

Handles ingestion and synchronization of domain entities and events from
Sensor, Vision, Incident, and Workflow modules into Neo4j using MERGE upserts.

Guarantees:
  - Zero duplicate nodes created (idempotent MERGE operations)
  - Publishes GraphSynchronizedEvent on batch completion
  - Automatic relationship wiring between linked domain entities
"""
from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.application.dto.sync_dto import (
    SyncBatchRequest,
    SyncNodeRequest,
    SyncResult,
)
from app.modules.knowledge.events.graph_events import publish_graph_synced
from app.modules.knowledge.infrastructure.cypher import sync as sync_cypher
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository

log = get_logger("knowledge.service.sync")


class GraphSyncService:
    """Service handling domain data synchronization into the Knowledge Graph."""

    def __init__(self, repo: BaseNeo4jRepository | None = None) -> None:
        self._repo = repo or BaseNeo4jRepository()

    async def sync_node(self, request: SyncNodeRequest) -> SyncResult:
        """Upsert a single node and its relationships into Neo4j."""
        t0 = time.monotonic()
        nodes_created = 0
        nodes_updated = 0
        rels_created = 0
        errors: list[str] = []

        try:
            # Check if node exists to classify created vs updated
            exists = await self._repo.exists(request.node_id)
            if exists:
                nodes_updated += 1
            else:
                nodes_created += 1

            # Select specific Cypher query if available, or fall back to generic
            cypher, params = self._build_upsert_query(request)
            await self._repo.execute_query(cypher, params)

            # Sync attached relationships
            for rel in request.relationships:
                rel_cypher = sync_cypher.UPSERT_RELATIONSHIP_GENERIC.format(rel_type=rel.rel_type)
                rel_params = {
                    "source_id": request.node_id,
                    "target_id": rel.target_id,
                    "properties": rel.properties,
                    "now": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                res = await self._repo.execute_query(rel_cypher, rel_params)
                if res and res[0].get("upserted_count", 0) > 0:
                    rels_created += 1

            elapsed = (time.monotonic() - t0) * 1000
            log.info(f"Synced node {request.node_id} ({request.label}) from {request.source_module} in {elapsed:.1f}ms")

            return SyncResult(
                source_module=request.source_module,
                nodes_created=nodes_created,
                nodes_updated=nodes_updated,
                relationships_created=rels_created,
                duration_ms=elapsed,
                success=True,
            )
        except Exception as exc:
            err = f"Failed to sync node {request.node_id}: {exc}"
            log.error(err)
            errors.append(err)
            elapsed = (time.monotonic() - t0) * 1000
            return SyncResult(
                source_module=request.source_module,
                errors=errors,
                duration_ms=elapsed,
                success=False,
            )

    async def sync_batch(self, batch: SyncBatchRequest) -> SyncResult:
        """Sync a batch of nodes from a domain module."""
        t0 = time.monotonic()
        total_created = 0
        total_updated = 0
        total_rels = 0
        errors: list[str] = []

        for req in batch.nodes:
            res = await self.sync_node(req)
            total_created += res.nodes_created
            total_updated += res.nodes_updated
            total_rels += res.relationships_created
            if res.errors:
                errors.extend(res.errors)

        elapsed = (time.monotonic() - t0) * 1000

        # Publish event
        await publish_graph_synced(
            sync_source=batch.source_module,
            nodes_created=total_created,
            nodes_updated=total_updated,
            rels_created=total_rels,
            duration_ms=elapsed,
        )

        log.info(
            f"Batch sync complete for {batch.source_module}: "
            f"{total_created} created, {total_updated} updated, {total_rels} rels in {elapsed:.1f}ms"
        )

        return SyncResult(
            source_module=batch.source_module,
            nodes_created=total_created,
            nodes_updated=total_updated,
            relationships_created=total_rels,
            errors=errors,
            duration_ms=elapsed,
            success=len(errors) == 0,
        )

    def _build_upsert_query(self, req: SyncNodeRequest) -> tuple[str, dict[str, Any]]:
        """Select Cypher template and parameters for node upsert."""
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        props = dict(req.properties)
        props["id"] = req.node_id
        props["entity_type"] = req.label
        props["source_module"] = req.source_module

        # Generic MERGE query
        cypher = sync_cypher.UPSERT_NODE_GENERIC.format(label=req.label)
        params = {
            "id": req.node_id,
            "label": req.label,
            "properties": props,
            "now": now,
        }
        return cypher, params
