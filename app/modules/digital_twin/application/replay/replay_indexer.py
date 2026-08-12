from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
log = get_logger(__name__)

class ReplayIndexer:
    def __init__(self):
        pass

    async def index_by_incident(self, twin_id: str, incident_id: str, snapshot_store: dict[str, Any]) -> dict[str, Any]:
        relevant = []
        for sid, snap in snapshot_store.items():
            if incident_id in snap.get("events", []):
                relevant.append(sid)
                
        return {
            "start_timestamp": "",
            "end_timestamp": "",
            "relevant_snapshot_ids": relevant,
            "related_entities": []
        }

    async def index_by_asset(self, twin_id: str, asset_id: str, asset_type: str, snapshot_store: dict[str, Any]) -> dict[str, Any]:
        relevant = []
        for sid, snap in snapshot_store.items():
            if asset_id in snap.get("state", {}):
                relevant.append(sid)
        return {"relevant_snapshot_ids": relevant}

    async def index_by_zone(self, twin_id: str, zone_id: str, snapshot_store: dict[str, Any]) -> dict[str, Any]:
        relevant = []
        last_health = None
        for sid, snap in snapshot_store.items():
            z_state = snap.get("state", {}).get(zone_id, {})
            h = z_state.get("health_score")
            if h is not None:
                if last_health is not None and abs(h - last_health) > 0.1:
                    relevant.append(sid)
                last_health = h
        return {"relevant_snapshot_ids": relevant}

    async def index_by_worker(self, twin_id: str, worker_id: str, snapshot_store: dict[str, Any]) -> dict[str, Any]:
        relevant = []
        last_zone = None
        for sid, snap in snapshot_store.items():
            w_state = snap.get("state", {}).get(worker_id, {})
            z = w_state.get("zone_id")
            if z and z != last_zone:
                relevant.append(sid)
                last_zone = z
        return {"relevant_snapshot_ids": relevant}

    async def index_by_timestamp(self, twin_id: str, start: str, end: str, snapshot_store: dict[str, Any]) -> dict[str, Any]:
        relevant = []
        for sid, snap in snapshot_store.items():
            ts = snap.get("timestamp", "")
            if start <= ts <= end:
                relevant.append(sid)
        return {"relevant_snapshot_ids": relevant}

    async def build_full_index(self, twin_id: str, snapshot_store: dict[str, Any]) -> dict[str, Any]:
        return {
            "by_incident": {},
            "by_zone": {},
            "by_equipment": {},
            "timeline": []
        }
