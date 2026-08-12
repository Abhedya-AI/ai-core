"""
services/graph_history_service.py — Graph Temporal History and Versioning Service.

Provides time-travel capabilities for graph entities:
  - Snapshots node properties before updates
  - Lists version history with property-level diffs
  - Restores nodes to historical states
  - Purges old snapshots based on retention policies
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.application.dto.history_dto import (
    GraphSnapshot,
    HistoryEntry,
    HistoryRequest,
    HistoryResult,
    PropertyDiff,
)
from app.modules.knowledge.infrastructure.repositories.history_repository import HistoryRepository

log = get_logger("knowledge.service.history")


class GraphHistoryService:
    """Service managing temporal node snapshots, history retrieval, and time travel."""

    def __init__(self, history_repo: HistoryRepository | None = None) -> None:
        self._repo = history_repo or HistoryRepository()

    async def record_snapshot(
        self,
        node_id: str,
        node_label: str,
        properties: dict[str, Any],
        change_summary: str | None = None,
        created_by: str | None = None,
    ) -> GraphSnapshot:
        """Create a versioned snapshot of a node's properties."""
        snap_dict = await self._repo.create_snapshot(
            node_id=node_id,
            node_label=node_label,
            properties=properties,
            change_summary=change_summary,
            created_by=created_by,
        )
        return GraphSnapshot(
            snapshot_id=snap_dict.get("id", snap_dict.get("snapshot_id", "")),
            node_id=node_id,
            node_label=node_label,
            version_number=snap_dict.get("version_number", 1),
            properties=snap_dict.get("properties", properties),
            created_at=snap_dict.get("created_at", ""),
            created_by=snap_dict.get("created_by", created_by),
            change_summary=snap_dict.get("change_summary", change_summary),
        )

    async def get_history(self, request: HistoryRequest) -> HistoryResult:
        """Retrieve node history with version entries and property diffs."""
        snapshots = await self._repo.list_snapshots(
            node_id=request.node_id,
            limit=request.limit,
            since=request.since,
            until=request.until,
        )
        total_count = await self._repo.get_version_count(request.node_id)

        entries: list[HistoryEntry] = []
        for i, snap_dict in enumerate(snapshots):
            snap = GraphSnapshot(
                snapshot_id=snap_dict.get("id", snap_dict.get("snapshot_id", "")),
                node_id=request.node_id,
                node_label=snap_dict.get("node_label", "GraphEntity"),
                version_number=snap_dict.get("version_number", 1),
                properties=snap_dict.get("properties", {}),
                created_at=snap_dict.get("created_at", ""),
                created_by=snap_dict.get("created_by"),
                change_summary=snap_dict.get("change_summary"),
            )

            diffs: list[PropertyDiff] = []
            if request.include_diffs and i < len(snapshots) - 1:
                older_props = snapshots[i + 1].get("properties", {})
                raw_diffs = HistoryRepository.compute_diff(older_props, snap.properties)
                diffs = [PropertyDiff(**d) for d in raw_diffs]

            entries.append(HistoryEntry(snapshot=snap, changes=diffs))

        node_label = snapshots[0].get("node_label", "GraphEntity") if snapshots else "GraphEntity"
        oldest_ts = snapshots[-1].get("created_at") if snapshots else None
        latest_ts = snapshots[0].get("created_at") if snapshots else None

        return HistoryResult(
            node_id=request.node_id,
            node_label=node_label,
            total_versions=total_count,
            entries=entries,
            oldest_version_at=oldest_ts,
            latest_version_at=latest_ts,
        )

    async def get_state_at(self, node_id: str, timestamp: datetime) -> dict[str, Any] | None:
        """Get historical state of node at a given point in time."""
        snap_dict = await self._repo.get_snapshot_at(node_id, timestamp)
        if not snap_dict:
            return None
        return snap_dict.get("properties", {})

    async def restore_version(self, node_id: str, snapshot_id: str) -> dict[str, Any]:
        """Restore node to state captured in snapshot_id."""
        return await self._repo.restore_from_snapshot(node_id, snapshot_id)

    async def cleanup(self, older_than_days: int = 90) -> int:
        """Purge snapshots older than specified retention days."""
        return await self._repo.purge_old_snapshots(older_than_days=older_than_days)
