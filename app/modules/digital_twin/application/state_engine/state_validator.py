from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
log = get_logger(__name__)

class TwinStateValidator:
    def validate_sensor_state(self, state: dict) -> tuple[bool, list[str]]:
        missing = self._check_required_fields(state, ["sensor_id", "current_value", "is_online"])
        return len(missing) == 0, missing

    def validate_equipment_state(self, state: dict) -> tuple[bool, list[str]]:
        missing = self._check_required_fields(state, ["equipment_id", "health_score", "status"])
        errors = missing.copy()
        
        if "health_score" not in missing:
            err = self._check_score_range(state["health_score"], "health_score")
            if err:
                errors.append(err)
                
        return len(errors) == 0, errors

    def validate_worker_state(self, state: dict) -> tuple[bool, list[str]]:
        missing = self._check_required_fields(state, ["worker_id", "current_zone_id", "safety_score"])
        errors = missing.copy()
        
        if "safety_score" not in missing:
            err = self._check_score_range(state["safety_score"], "safety_score")
            if err:
                errors.append(err)
                
        return len(errors) == 0, errors

    def validate_zone_state(self, state: dict) -> tuple[bool, list[str]]:
        missing = self._check_required_fields(state, ["zone_id", "health_score", "occupancy"])
        errors = missing.copy()
        
        if "health_score" not in missing:
            err = self._check_score_range(state["health_score"], "health_score")
            if err:
                errors.append(err)
                
        return len(errors) == 0, errors

    def validate_state_transition(self, from_state: dict, to_state: dict) -> tuple[bool, list[str]]:
        errors = []
        if from_state.get("entity_id") != to_state.get("entity_id") and from_state.get("entity_id") is not None:
            errors.append("entity_id mismatch")
            
        from_ts = from_state.get("updated_at", "")
        to_ts = to_state.get("updated_at", "")
        if from_ts and to_ts and to_ts < from_ts:
            errors.append("timestamps are not strictly ordered")
            
        return len(errors) == 0, errors

    def validate_snapshot(self, snapshot: dict) -> tuple[bool, list[str]]:
        missing = self._check_required_fields(snapshot, [
            "snapshot_id", "version_number", "zone_states", "equipment_states", 
            "worker_states", "sensor_states", "camera_states", "hazard_states", 
            "resource_states", "metrics", "total_entities"
        ])
        return len(missing) == 0, missing

    def _check_score_range(self, value: Any, field_name: str) -> str | None:
        try:
            val = float(value)
            if not (0.0 <= val <= 1.0):
                return f"{field_name} must be between 0.0 and 1.0, got {val}"
        except (ValueError, TypeError):
            return f"{field_name} must be a float, got {type(value)}"
        return None

    def _check_required_fields(self, state: dict, required: list[str]) -> list[str]:
        return [f for f in required if f not in state]
