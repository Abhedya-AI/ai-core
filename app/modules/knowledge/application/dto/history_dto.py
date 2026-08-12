"""
dto/history_dto.py — DTOs for Temporal Node History and Versioning.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HistoryRequest(BaseModel):
    """Request to retrieve version history for a graph node."""

    node_id: str
    limit: int = Field(default=20, ge=1, le=100)
    since: datetime | None = Field(default=None, description="Only return versions after this timestamp")
    until: datetime | None = Field(default=None, description="Only return versions before this timestamp")
    include_diffs: bool = Field(default=True, description="Include property-level diffs between versions")


class GraphSnapshot(BaseModel):
    """A complete snapshot of a node's properties at a point in time."""

    snapshot_id: str
    node_id: str
    node_label: str
    version_number: int
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    created_by: str | None = None
    change_summary: str | None = None


class PropertyDiff(BaseModel):
    """A single property change between two versions of a node."""

    property_name: str
    old_value: Any
    new_value: Any

    @property
    def changed(self) -> bool:
        return self.old_value != self.new_value


class HistoryEntry(BaseModel):
    """A single entry in a node's change history."""

    snapshot: GraphSnapshot
    changes: list[PropertyDiff] = Field(default_factory=list)

    @property
    def change_count(self) -> int:
        return len(self.changes)


class HistoryResult(BaseModel):
    """Result of a node history query."""

    node_id: str
    node_label: str
    total_versions: int
    entries: list[HistoryEntry]
    oldest_version_at: str | None = None
    latest_version_at: str | None = None


class RestoreRequest(BaseModel):
    """Request to restore a node from a specific snapshot version."""

    node_id: str
    snapshot_id: str
    restored_by: str | None = Field(default=None, description="User or system triggering the restore")
    create_pre_restore_snapshot: bool = Field(
        default=True,
        description="Snapshot the current state before restoring",
    )
