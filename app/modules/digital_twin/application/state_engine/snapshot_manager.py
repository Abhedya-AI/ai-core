from __future__ import annotations
from typing import Any
import time
import uuid
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.digital_twin.application.state_engine.state_manager import TwinStateManager

log = get_logger(__name__)

class TwinSnapshotManager:
    def __init__(self):
        self._snapshots: dict[str, dict] = {}
        self._version_counter: dict[str, int] = {}
        
        try:
            from app.infrastructure.database.session import async_session
            self._session_maker = async_session
        except ImportError:
            self._session_maker = None
            log.warning("PostgreSQL not available. Using in-memory snapshot storage.")

    async def create_snapshot(self, twin_id: str, state_manager: TwinStateManager, description: str, created_by: str) -> dict:
        t0 = time.perf_counter()
        
        all_states = await state_manager.get_all_states()
        
        snapshot = {
            "snapshot_id": str(uuid.uuid4()),
            "twin_id": twin_id,
            "version_number": self._version_counter.get(twin_id, 0) + 1,
            "description": description,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "zone_states": {},
            "equipment_states": {},
            "worker_states": {},
            "sensor_states": {},
            "camera_states": {},
            "hazard_states": {},
            "resource_states": {}
        }
        
        self._version_counter[twin_id] = snapshot["version_number"]
        
        # Partition states
        for eid, state in all_states.items():
            etype = state.get("entity_type", "").lower()
            if etype == "zone":
                snapshot["zone_states"][eid] = state
            elif etype == "equipment":
                snapshot["equipment_states"][eid] = state
            elif etype == "worker":
                snapshot["worker_states"][eid] = state
            elif etype == "sensor":
                snapshot["sensor_states"][eid] = state
            elif etype == "camera":
                snapshot["camera_states"][eid] = state
            elif etype == "hazard":
                snapshot["hazard_states"][eid] = state
            elif etype == "resource":
                snapshot["resource_states"][eid] = state
            else:
                # default partition if unknown
                snapshot["resource_states"][eid] = state
                
        snapshot["total_entities"] = len(all_states)
        snapshot["metrics"] = {
            "health_score": await state_manager.compute_twin_health_score()
        }
        
        self._snapshots[snapshot["snapshot_id"]] = snapshot
        
        latency_ms = (time.perf_counter() - t0) * 1000
        snapshot["latency_ms"] = latency_ms
        log.info(f"Created snapshot {snapshot['snapshot_id']} in {latency_ms:.2f}ms")
        
        return snapshot

    async def get_snapshot(self, snapshot_id: str) -> dict | None:
        return self._snapshots.get(snapshot_id)

    async def list_snapshots(self, twin_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
        snaps = [s for s in self._snapshots.values() if s.get("twin_id") == twin_id]
        snaps.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return snaps[offset:offset+limit]

    async def delete_snapshot(self, snapshot_id: str) -> bool:
        if snapshot_id in self._snapshots:
            del self._snapshots[snapshot_id]
            return True
        return False

    async def restore_from_snapshot(self, snapshot_id: str, state_manager: TwinStateManager) -> int:
        snapshot = await self.get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")
            
        count = 0
        categories = [
            "zone_states", "equipment_states", "worker_states", "sensor_states", 
            "camera_states", "hazard_states", "resource_states"
        ]
        for cat in categories:
            for eid, state in snapshot.get(cat, {}).items():
                await state_manager.set_state(eid, state, reason=f"restored_from_snapshot_{snapshot_id}")
                count += 1
                
        return count

    async def compare_snapshots(self, snapshot_id_a: str, snapshot_id_b: str) -> dict:
        snap_a = await self.get_snapshot(snapshot_id_a)
        snap_b = await self.get_snapshot(snapshot_id_b)
        
        if not snap_a or not snap_b:
            raise ValueError("One or both snapshots not found")
            
        def extract_entities(snap):
            entities = {}
            for cat in ["zone_states", "equipment_states", "worker_states", "sensor_states", "camera_states", "hazard_states", "resource_states"]:
                entities.update(snap.get(cat, {}))
            return entities
            
        entities_a = extract_entities(snap_a)
        entities_b = extract_entities(snap_b)
        
        set_a = set(entities_a.keys())
        set_b = set(entities_b.keys())
        
        added = list(set_b - set_a)
        removed = list(set_a - set_b)
        changed = []
        
        for k in set_a.intersection(set_b):
            if entities_a[k] != entities_b[k]:
                changed.append(k)
                
        return {
            "added": added,
            "removed": removed,
            "changed": changed
        }
