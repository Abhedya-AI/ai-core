"""
repositories/history_repository.py — Temporal Node History and Versioning Repository.

Creates versioned snapshots of node states before mutations.
Supports time-travel queries: "What was the state of Zone X at timestamp T?"
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
import uuid

from app.core.logging import get_logger
from app.modules.knowledge.infrastructure.cypher import history as history_cypher
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository

log = get_logger("knowledge.repository.history")


def _snapshot_to_dict(snap: Any) -> dict[str, Any]:
    if snap is None:
        return {}
    if isinstance(snap, dict):
        props = dict(snap)
    elif hasattr(snap, "_properties"):
        props = dict(snap._properties)
    else:
        try:
            props = dict(snap)
        except Exception:
            return {}

    # Parse properties_json if present
    if "properties_json" in props and isinstance(props["properties_json"], str):
        try:
            props["properties"] = json.loads(props["properties_json"])
        except Exception:
            props["properties"] = {}
    elif "properties" not in props:
        props["properties"] = {}

    return props


class HistoryRepository(BaseNeo4jRepository):
    """Repository for temporal node snapshotting, versioning, and diff tracking."""

    async def create_snapshot(
        self,
        node_id: str,
        node_label: str,
        properties: dict[str, Any],
        change_summary: str | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a NodeSnapshot node linked to node_id.
        Increments the version number dynamically.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        snapshot_id = str(uuid.uuid4())

        # Determine next version number
        try:
            version_records = await self.execute_query(
                history_cypher.GET_NEXT_VERSION_NUMBER,
                {"node_id": node_id},
            )
            next_ver = (
                version_records[0].get("next_version", 1) if version_records else 1
            )
        except Exception:
            next_ver = 1

        props_json = json.dumps(properties, default=str)

        params = {
            "node_id": node_id,
            "node_label": node_label,
            "snapshot_id": snapshot_id,
            "version_number": next_ver,
            "properties_json": props_json,
            "change_summary": change_summary or f"Version {next_ver} update",
            "created_by": created_by or "system",
            "created_at": now_iso,
        }

        try:
            records = await self.execute_query(history_cypher.CREATE_NODE_SNAPSHOT, params)
            log.info(f"Created snapshot v{next_ver} for node {node_id} [{node_label}]")
            if records:
                return _snapshot_to_dict(records[0].get("snap"))
            return {
                "snapshot_id": snapshot_id,
                "node_id": node_id,
                "node_label": node_label,
                "version_number": next_ver,
                "created_at": now_iso,
                "change_summary": change_summary,
            }
        except Exception as exc:
            log.error(f"Failed to create snapshot for node {node_id}: {exc}")
            raise self._translate_error(exc) from exc

    async def get_version_count(self, node_id: str) -> int:
        """Return total number of snapshots for a node."""
        try:
            records = await self.execute_query(
                history_cypher.COUNT_SNAPSHOTS_FOR_NODE,
                {"node_id": node_id},
            )
            if records:
                return int(records[0].get("total_versions", 0))
            return 0
        except Exception as exc:
            log.error(f"Failed to count snapshots for node {node_id}: {exc}")
            return 0

    async def list_snapshots(
        self,
        node_id: str,
        limit: int = 20,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """List snapshots for node_id ordered by version DESC."""
        params = {
            "node_id": node_id,
            "limit": limit,
            "since": since.isoformat() if since else None,
            "until": until.isoformat() if until else None,
            "skip": 0,
        }
        try:
            records = await self.execute_query(history_cypher.LIST_SNAPSHOTS_FOR_NODE, params)
            return [_snapshot_to_dict(rec.get("snap")) for rec in records]
        except Exception as exc:
            log.error(f"Failed to list snapshots for node {node_id}: {exc}")
            return []

    async def get_snapshot_at(
        self,
        node_id: str,
        timestamp: datetime,
    ) -> dict[str, Any] | None:
        """Get snapshot closest to (and before/at) timestamp."""
        ts_str = timestamp.isoformat()
        try:
            records = await self.execute_query(
                history_cypher.GET_SNAPSHOT_AT_TIMESTAMP,
                {"node_id": node_id, "timestamp": ts_str},
            )
            if records:
                return _snapshot_to_dict(records[0].get("snap"))
            return None
        except Exception as exc:
            log.error(f"Failed to get snapshot at {ts_str} for node {node_id}: {exc}")
            return None

    async def restore_from_snapshot(
        self,
        node_id: str,
        snapshot_id: str,
    ) -> dict[str, Any]:
        """Restore node properties from a specific snapshot."""
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            # 1. Fetch snapshot properties
            snap_records = await self.execute_query(
                history_cypher.GET_SNAPSHOT_BY_ID,
                {"snapshot_id": snapshot_id},
            )
            if not snap_records:
                raise ValueError(f"Snapshot '{snapshot_id}' not found")

            snap_dict = _snapshot_to_dict(snap_records[0].get("snap"))
            restored_props = snap_dict.get("properties", {})
            restored_props["updated_at"] = now_iso
            restored_props["restored_from_snapshot_id"] = snapshot_id

            # 2. Update actual node
            from app.modules.knowledge.application.dto import UpdateNodeRequest
            updated_node = await self.update_node(
                UpdateNodeRequest(node_id=node_id, properties=restored_props)
            )

            # 3. Record a new snapshot marking the restoration
            await self.create_snapshot(
                node_id=node_id,
                node_label=snap_dict.get("node_label", "GraphEntity"),
                properties=restored_props,
                change_summary=f"Restored from version {snap_dict.get('version_number')}",
                created_by="system_restore",
            )

            log.info(f"Restored node {node_id} from snapshot {snapshot_id}")
            return updated_node
        except Exception as exc:
            log.error(f"Failed to restore node {node_id} from snapshot {snapshot_id}: {exc}")
            raise self._translate_error(exc) from exc

    async def purge_old_snapshots(self, older_than_days: int = 90) -> int:
        """Delete snapshots older than N days."""
        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).isoformat()
        try:
            records = await self.execute_query(
                history_cypher.PURGE_OLD_SNAPSHOTS,
                {"cutoff_timestamp": cutoff},
            )
            deleted = records[0].get("deleted_count", 0) if records else 0
            log.info(f"Purged {deleted} snapshots older than {older_than_days} days")
            return int(deleted)
        except Exception as exc:
            log.error(f"Failed to purge old snapshots: {exc}")
            return 0

    @staticmethod
    def compute_diff(
        properties_old: dict[str, Any],
        properties_new: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Compute property-level diff between two node property dictionaries."""
        diffs: list[dict[str, Any]] = []
        all_keys = set(list(properties_old.keys()) + list(properties_new.keys()))

        ignored_keys = {
            "created_at", "updated_at", "restored_at",
            "restored_from_snapshot_id", "entity_type",
        }

        for key in sorted(all_keys):
            if key in ignored_keys or key.startswith("_"):
                continue
            val_old = properties_old.get(key)
            val_new = properties_new.get(key)
            if val_old != val_new:
                diffs.append({
                    "property_name": key,
                    "old_value": val_old,
                    "new_value": val_new,
                })
        return diffs
