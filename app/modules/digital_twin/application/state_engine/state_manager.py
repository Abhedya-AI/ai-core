from __future__ import annotations
from typing import Any
import time
from datetime import datetime, timezone
import numpy as np

from app.core.logging import get_logger

log = get_logger(__name__)

class TwinStateManager:
    def __init__(self):
        self._states: dict[str, dict] = {}  # entity_id -> current state
        self._history: dict[str, list[dict]] = {}  # entity_id -> list of historical states
        self._max_history = 100  # keep last 100 states per entity
        self._version_counter: dict[str, int] = {}  # entity_id -> current version

    async def get_state(self, entity_id: str) -> dict | None:
        return self._states.get(entity_id)

    async def set_state(self, entity_id: str, state: dict, reason: str) -> dict:
        merged = self._states.get(entity_id, {}).copy()
        merged.update(state)
        merged["transition_reason"] = reason
        merged["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        self._states[entity_id] = merged
        self._increment_version(entity_id)
        self._record_history(entity_id, merged)
        return merged

    async def get_history(self, entity_id: str, limit: int = 50) -> list[dict]:
        hist = self._history.get(entity_id, [])
        # Return newest first
        return hist[-limit:][::-1]

    async def rollback(self, entity_id: str, steps: int = 1) -> dict | None:
        if entity_id not in self._history:
            return None
        hist = self._history[entity_id]
        if len(hist) <= steps:
            if hist:
                self._states[entity_id] = hist[0].copy()
                self._history[entity_id] = [hist[0]]
                self._increment_version(entity_id)
                return self._states[entity_id]
            return None
            
        # Remove the latest 'steps' states
        self._history[entity_id] = hist[:-steps]
        old_state = self._history[entity_id][-1].copy()
        self._states[entity_id] = old_state
        self._increment_version(entity_id)
        return old_state

    async def get_all_states(self) -> dict[str, dict]:
        return self._states.copy()

    async def get_states_by_type(self, entity_type: str) -> dict[str, dict]:
        return {k: v for k, v in self._states.items() if v.get("entity_type") == entity_type}

    async def merge_sync_updates(self, updates: dict[str, dict], source: str) -> dict[str, int]:
        versions = {}
        for entity_id, new_state in updates.items():
            await self.set_state(entity_id, new_state, f"sync_update_from_{source}")
            versions[entity_id] = self._version_counter[entity_id]
        return versions

    async def compute_twin_health_score(self) -> float:
        scores = []
        for state in self._states.values():
            if "health_score" in state:
                try:
                    scores.append(float(state["health_score"]))
                except (ValueError, TypeError):
                    pass
        if not scores:
            return 1.0
        return float(np.mean(scores))

    def _record_history(self, entity_id: str, state: dict) -> None:
        if entity_id not in self._history:
            self._history[entity_id] = []
        self._history[entity_id].append(state.copy())
        if len(self._history[entity_id]) > self._max_history:
            self._history[entity_id] = self._history[entity_id][-self._max_history:]

    def _increment_version(self, entity_id: str) -> int:
        current = self._version_counter.get(entity_id, 0)
        self._version_counter[entity_id] = current + 1
        return self._version_counter[entity_id]
