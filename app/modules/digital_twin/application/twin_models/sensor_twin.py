from __future__ import annotations
from typing import Any
import numpy as np

from app.core.logging import get_logger
from app.modules.digital_twin.domain.models import SensorTwin, _now_iso

log = get_logger(__name__)

class SensorTwinBuilder:
    async def build(self, entity_id: str, context: dict[str, Any]) -> dict[str, Any]:
        sensor_data = context.get("sensor_data", {})
        
        current_value = sensor_data.get("current_value")
        history = sensor_data.get("reading_history", [])
        
        is_anomalous = self._compute_anomaly([r.get("value", 0) for r in history], current_value) if current_value is not None else False
        is_online = sensor_data.get("is_online", True)
        
        health_score = 1.0
        if not is_online:
            health_score = 0.0
        elif is_anomalous:
            health_score = 0.5
            
        twin = SensorTwin(
            sensor_id=entity_id,
            sensor_name=sensor_data.get("sensor_name", f"Sensor-{entity_id}"),
            sensor_type=sensor_data.get("sensor_type", "UNKNOWN"),
            zone_id=sensor_data.get("zone_id", "UNKNOWN"),
            equipment_id=sensor_data.get("equipment_id"),
            current_value=current_value,
            unit=sensor_data.get("unit", ""),
            min_value=sensor_data.get("min_value", 0.0),
            max_value=sensor_data.get("max_value", 100.0),
            threshold_low=sensor_data.get("threshold_low", 0.0),
            threshold_high=sensor_data.get("threshold_high", 100.0),
            is_online=is_online,
            is_anomalous=is_anomalous,
            last_reading_at=sensor_data.get("last_reading_at", _now_iso()),
            reading_history=history,
            health_score=health_score,
            risk_contribution=sensor_data.get("risk_contribution", 0.0)
        )
        return twin.model_dump()

    async def update(self, current_state: dict[str, Any], new_data: dict[str, Any]) -> dict[str, Any]:
        updated = dict(current_state)
        sensor_data = new_data.get("sensor_data", {})
        
        if "current_value" in sensor_data:
            updated["current_value"] = sensor_data["current_value"]
        if "is_online" in sensor_data:
            updated["is_online"] = sensor_data["is_online"]
            
        history = updated.get("reading_history", [])
        if "current_value" in sensor_data:
            history.append({
                "value": sensor_data["current_value"], 
                "timestamp": sensor_data.get("timestamp", _now_iso())
            })
            if len(history) > 100:
                history = history[-100:]
            updated["reading_history"] = history
            
        current_value = updated.get("current_value")
        is_anomalous = self._compute_anomaly([r.get("value", 0) for r in history], current_value) if current_value is not None else False
        updated["is_anomalous"] = is_anomalous
        
        health_score = 1.0
        if not updated.get("is_online", True):
            health_score = 0.0
        elif is_anomalous:
            health_score = 0.5
        updated["health_score"] = health_score
        
        updated["updated_at"] = _now_iso()
        return updated

    def validate(self, state: dict[str, Any]) -> bool:
        required = ["sensor_id", "sensor_name", "zone_id", "is_online", "health_score"]
        return all(k in state for k in required)

    def _compute_anomaly(self, readings: list[float], current: float, threshold: float = 3.0) -> bool:
        if not readings or len(readings) < 5:
            return False
        mean = np.mean(readings)
        std = np.std(readings)
        if std == 0:
            return False
        z_score = abs(current - mean) / std
        return z_score > threshold
