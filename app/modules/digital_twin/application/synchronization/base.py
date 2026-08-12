from __future__ import annotations
from typing import Protocol, runtime_checkable, Any
from dataclasses import dataclass
from datetime import datetime
import dateutil.parser

from app.core.logging import get_logger
log = get_logger(__name__)

@dataclass
class SyncResult:
    source: str
    status: str  # "COMPLETED", "FAILED", "PARTIAL"
    entity_updates: dict[str, Any]  # entity_id -> updated state dict
    update_count: int
    error_message: str | None
    latency_ms: float
    synced_at: str

@runtime_checkable
class AbstractSyncEngine(Protocol):
    async def sync(self, twin_id: str, context: dict[str, Any]) -> SyncResult: ...
    async def incremental_sync(self, twin_id: str, since: str, context: dict[str, Any]) -> SyncResult: ...
    def get_source(self) -> str: ...
    def is_available(self) -> bool: ...

class SyncConflictResolver:
    def resolve(self, existing: dict, incoming: dict, source: str) -> dict:
        if not existing:
            return incoming.copy()
        if not incoming:
            return existing.copy()
        
        merged = existing.copy()
        
        existing_ts = self._get_timestamp(existing)
        incoming_ts = self._get_timestamp(incoming)
        
        existing_override = existing.get("manual_override", False)
        incoming_override = incoming.get("manual_override", False)
        
        # Conflict resolution strategy
        if existing_override and not incoming_override:
            return merged
        
        if incoming_override and not existing_override:
            return self._merge_dicts(merged, incoming, source)
        
        if incoming_ts >= existing_ts:
            return self._merge_dicts(merged, incoming, source)
            
        return merged

    def _merge_dicts(self, existing: dict, incoming: dict, source: str) -> dict:
        result = existing.copy()
        for k, v in incoming.items():
            if isinstance(v, dict) and k in result and isinstance(result[k], dict):
                result[k] = self._merge_dicts(result[k], v, source)
            else:
                result[k] = v
        
        result["last_updated_by"] = source
        return result

    def _get_timestamp(self, state: dict) -> float:
        ts_str = state.get("timestamp") or state.get("updated_at")
        if not ts_str:
            return 0.0
        try:
            dt = dateutil.parser.isoparse(str(ts_str))
            return dt.timestamp()
        except Exception:
            return 0.0
