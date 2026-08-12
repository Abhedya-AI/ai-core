from __future__ import annotations

import uuid
from typing import Any

from app.core.logging import get_logger
log = get_logger(__name__)

class BranchingTimeline:
    def __init__(self, base_snapshot: dict[str, Any]):
        self._base_snapshot = base_snapshot
        self._branches: dict[str, dict[str, Any]] = {}
        
    async def create_branch(self, branch_name: str, conditions: dict[str, Any], from_timestamp: str | None = None) -> str:
        branch_id = str(uuid.uuid4())
        self._branches[branch_id] = {
            "id": branch_id,
            "name": branch_name,
            "base": self._base_snapshot,
            "events": [],
            "current_state": dict(self._base_snapshot),
            "conditions": conditions,
            "from_timestamp": from_timestamp
        }
        return branch_id
        
    async def apply_events_to_branch(self, branch_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
        if branch_id not in self._branches:
            raise ValueError(f"Branch {branch_id} not found")
            
        branch = self._branches[branch_id]
        branch["events"].extend(events)
        
        # update current_state based on events (assuming events have entity_id and state updates)
        for event in events:
            eid = event.get("entity_id")
            if eid:
                if eid not in branch["current_state"]:
                    branch["current_state"][eid] = {}
                branch["current_state"][eid].update(event.get("updates", {}))
                
        return branch["current_state"]
        
    async def merge_branches(self, branch_ids: list[str]) -> dict[str, Any]:
        merged = {}
        for bid in branch_ids:
            if bid in self._branches:
                b_state = self._branches[bid]["current_state"]
                for eid, state in b_state.items():
                    if eid not in merged:
                        merged[eid] = dict(state)
                    else:
                        # pick state with highest confidence, simplistic merge
                        conf_existing = merged[eid].get("confidence", 0.0)
                        conf_new = state.get("confidence", 0.0)
                        if conf_new > conf_existing:
                            merged[eid].update(state)
        return merged
        
    async def get_branch_state(self, branch_id: str, at_timestamp: str | None = None) -> dict[str, Any]:
        if branch_id not in self._branches:
            return {}
        return self._branches[branch_id]["current_state"]
        
    async def compare_branches(self, branch_id_a: str, branch_id_b: str) -> dict[str, Any]:
        state_a = await self.get_branch_state(branch_id_a)
        state_b = await self.get_branch_state(branch_id_b)
        
        diff = {}
        all_keys = set(state_a.keys()).union(set(state_b.keys()))
        for k in all_keys:
            if k not in state_a:
                diff[k] = {"only_in": "B"}
            elif k not in state_b:
                diff[k] = {"only_in": "A"}
            else:
                if state_a[k] != state_b[k]:
                    diff[k] = {"diff": True}
        return diff
        
    def list_branches(self) -> list[dict[str, Any]]:
        return [{"id": v["id"], "name": v["name"], "events_count": len(v["events"])} for v in self._branches.values()]
