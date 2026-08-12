from __future__ import annotations
from typing import Any
import uuid
from datetime import datetime, timezone

from app.core.logging import get_logger

log = get_logger(__name__)

class TwinVersionManager:
    def __init__(self):
        self._twin_versions: dict[str, list[dict]] = {}  # twin_id -> list of version dicts
        self._version_counters: dict[str, int] = {}  # twin_id -> current version number

    async def create_version(self, twin_id: str, snapshot_id: str | None, description: str, created_by: str, change_summary: dict) -> dict:
        if twin_id not in self._twin_versions:
            self._twin_versions[twin_id] = []
            
        current = self._version_counters.get(twin_id, 0)
        new_version = current + 1
        self._version_counters[twin_id] = new_version
        
        version_dict = {
            "version_id": str(uuid.uuid4()),
            "twin_id": twin_id,
            "version_number": new_version,
            "snapshot_id": snapshot_id,
            "description": description,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "change_summary": change_summary
        }
        
        self._twin_versions[twin_id].append(version_dict)
        return version_dict

    async def get_version(self, version_id: str) -> dict | None:
        for versions in self._twin_versions.values():
            for v in versions:
                if v.get("version_id") == version_id:
                    return v
        return None

    async def list_versions(self, twin_id: str, limit: int = 20) -> list[dict]:
        versions = self._twin_versions.get(twin_id, [])
        # Newest first
        sorted_versions = sorted(versions, key=lambda x: x.get("version_number", 0), reverse=True)
        return sorted_versions[:limit]

    async def get_latest_version(self, twin_id: str) -> dict | None:
        versions = await self.list_versions(twin_id, limit=1)
        return versions[0] if versions else None

    async def get_version_by_number(self, twin_id: str, version_number: int) -> dict | None:
        versions = self._twin_versions.get(twin_id, [])
        for v in versions:
            if v.get("version_number") == version_number:
                return v
        return None

    async def diff_versions(self, version_id_a: str, version_id_b: str) -> dict:
        va = await self.get_version(version_id_a)
        vb = await self.get_version(version_id_b)
        
        if not va or not vb:
            raise ValueError("One or both versions not found")
            
        return {
            "version_a": va.get("version_number"),
            "version_b": vb.get("version_number"),
            "change_summary_a": va.get("change_summary"),
            "change_summary_b": vb.get("change_summary")
        }
