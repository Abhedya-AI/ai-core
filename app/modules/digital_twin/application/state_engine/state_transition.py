from __future__ import annotations
from typing import Any
from datetime import datetime, timezone

from app.core.logging import get_logger
import dateutil.parser

log = get_logger(__name__)

class TwinStateTransitionEngine:
    VALID_TRANSITIONS: dict[str, list[str]] = {
        "ACTIVE": ["DEGRADED", "OFFLINE", "MAINTENANCE", "CRITICAL"],
        "OFFLINE": ["INITIALIZING", "ACTIVE"],
        "DEGRADED": ["ACTIVE", "CRITICAL", "OFFLINE", "MAINTENANCE"],
        "INITIALIZING": ["ACTIVE", "OFFLINE", "FAILED"],
        "CRITICAL": ["MAINTENANCE", "OFFLINE", "DEGRADED"],
        "MAINTENANCE": ["ACTIVE", "INITIALIZING", "OFFLINE"],
        "FAILED": ["INITIALIZING", "OFFLINE", "MAINTENANCE"]
    }

    def is_valid_transition(self, entity_type: str, from_status: str, to_status: str) -> bool:
        if from_status == to_status:
            return True
        allowed = self.VALID_TRANSITIONS.get(from_status, [])
        return to_status in allowed

    async def apply_transition(self, entity_id: str, entity_type: str, current_state: dict, new_status: str, reason: str, metadata: dict = {}) -> dict:
        new_state = current_state.copy()
        new_state["status"] = new_status
        new_state["transition_reason"] = reason
        new_state["updated_at"] = datetime.now(timezone.utc).isoformat()
        for k, v in metadata.items():
            new_state[k] = v
        return new_state

    def get_available_transitions(self, entity_type: str, current_status: str) -> list[str]:
        return self.VALID_TRANSITIONS.get(current_status, [])

    async def detect_anomalous_transitions(self, state_history: list[dict]) -> list[dict]:
        # Detects rapid state changes (>3 transitions in 5 minutes = anomaly)
        anomalies = []
        if len(state_history) < 4:
            return anomalies
            
        for i in range(len(state_history) - 3):
            window = state_history[i:i+4]
            # Ensure window is sorted by timestamp (newest first in history usually)
            try:
                t_old = dateutil.parser.isoparse(window[-1].get("updated_at", "")).timestamp()
                t_new = dateutil.parser.isoparse(window[0].get("updated_at", "")).timestamp()
                diff = abs(t_new - t_old)
                if diff <= 300:  # 5 minutes
                    anomalies.append({
                        "type": "RAPID_TRANSITION",
                        "description": "More than 3 transitions within 5 minutes detected.",
                        "states": window
                    })
            except Exception:
                pass
                
        return anomalies
