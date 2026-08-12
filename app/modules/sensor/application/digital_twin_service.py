"""
sensor/application/digital_twin_service.py — Sensor Digital Twin Service.

Maintains live in-memory digital twins for all sensors, equipment,
zones, and the plant. Synchronized automatically by the ingestion pipeline.

The twin layer provides:
  - Current state of every sensor without querying Neo4j on every request
  - Aggregated zone and equipment health views
  - Feed for WebSocket real-time dashboard updates
  - Input layer for Feature Engineering and Analytics
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from app.core.logging import get_logger
from app.modules.sensor.domain.digital_twin import (
    SensorTwin, EquipmentTwin, ZoneTwin, PlantTwin, TwinStatus,
)
from app.modules.sensor.domain.models import (
    SensorReading, SensorAnomaly, SensorHealthState, SensorHealth, AnomalySeverity,
)

log = get_logger(__name__)

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class DigitalTwinService:
    """Service to manage digital twins of sensors, equipment, zones, and plants."""
    
    def __init__(self):
        """Initialize the in-memory stores for digital twins."""
        self._sensor_twins: dict[str, SensorTwin] = {}
        self._equipment_twins: dict[str, EquipmentTwin] = {}
        self._zone_twins: dict[str, ZoneTwin] = {}
        self._plant_twin: PlantTwin | None = None
        
    def get_sensor_twin(self, sensor_id: str) -> SensorTwin | None:
        """Retrieve a sensor twin by ID."""
        return self._sensor_twins.get(sensor_id)
        
    def get_equipment_twin(self, equipment_id: str) -> EquipmentTwin | None:
        """Retrieve an equipment twin by ID."""
        return self._equipment_twins.get(equipment_id)
        
    def get_zone_twin(self, zone_id: str) -> ZoneTwin | None:
        """Retrieve a zone twin by ID."""
        return self._zone_twins.get(zone_id)
        
    def get_plant_twin(self) -> PlantTwin | None:
        """Retrieve the plant twin."""
        return self._plant_twin
        
    def get_all_sensor_twins(self) -> list[SensorTwin]:
        """Retrieve all registered sensor twins."""
        return list(self._sensor_twins.values())
        
    def get_zone_sensor_twins(self, zone_id: str) -> list[SensorTwin]:
        """Retrieve all sensor twins within a specific zone."""
        return [t for t in self._sensor_twins.values() if t.zone_id == zone_id]

    def update_from_reading(self, reading: SensorReading) -> SensorTwin:
        """Update sensor twin state from a new reading."""
        twin = self._sensor_twins.get(reading.sensor_id)
        if not twin:
            twin = SensorTwin(sensor_id=reading.sensor_id)
            self._sensor_twins[reading.sensor_id] = twin
            
        twin.last_reading_value = reading.value
        twin.last_reading_timestamp = reading.timestamp
        twin.last_reading_unit = reading.unit
        twin.total_readings += 1
        twin.updated_at = utc_now_iso()
        
        equipment_id = reading.metadata.get("equipment_id") if reading.metadata else None
        zone_id = reading.metadata.get("zone_id") if reading.metadata else None
        
        if equipment_id:
            twin.equipment_id = equipment_id
            eq_twin = self._equipment_twins.get(equipment_id)
            if not eq_twin:
                eq_twin = EquipmentTwin(equipment_id=equipment_id)
                self._equipment_twins[equipment_id] = eq_twin
            if reading.sensor_id not in eq_twin.sensor_twins:
                eq_twin.sensor_twins.append(reading.sensor_id)
                
        if zone_id:
            twin.zone_id = zone_id
            z_twin = self._zone_twins.get(zone_id)
            if not z_twin:
                z_twin = ZoneTwin(zone_id=zone_id)
                self._zone_twins[zone_id] = z_twin
            if reading.sensor_id not in z_twin.sensor_twins:
                z_twin.sensor_twins.append(reading.sensor_id)
                
        return twin
        
    def update_from_health(self, state: SensorHealthState) -> SensorTwin:
        """Update sensor twin based on a health transition."""
        twin = self._sensor_twins.get(state.sensor_id)
        if not twin:
            twin = SensorTwin(sensor_id=state.sensor_id)
            self._sensor_twins[state.sensor_id] = twin
            
        status = getattr(state, 'status', getattr(state, 'current_health', SensorHealth.HEALTHY))
        twin.health_status = status.value if hasattr(status, 'value') else str(status)
        twin.consecutive_anomalies = state.consecutive_anomalies
        twin.uptime_pct = state.uptime_pct
        twin.updated_at = utc_now_iso()
        
        # Map health to TwinStatus
        if status == SensorHealth.OFFLINE:
            twin.status = TwinStatus.OFFLINE
        elif status == SensorHealth.CALIBRATING:
            twin.status = TwinStatus.CALIBRATING
        elif status == SensorHealth.HEALTHY:
            twin.status = TwinStatus.ONLINE
        else:
            twin.status = TwinStatus.DEGRADED
            
        if twin.zone_id:
            self.refresh_zone_twin(twin.zone_id)
        if twin.equipment_id:
            # Simple equipment refresh could be here
            pass
            
        self.refresh_plant_twin()
        
        return twin
        
    def update_from_anomaly(self, anomaly: SensorAnomaly) -> SensorTwin:
        """Update sensor twin when an anomaly is detected."""
        twin = self._sensor_twins.get(anomaly.sensor_id)
        if not twin:
            twin = SensorTwin(sensor_id=anomaly.sensor_id)
            self._sensor_twins[anomaly.sensor_id] = twin
            
        if anomaly.anomaly_id not in twin.active_alerts:
            twin.active_alerts.append(anomaly.anomaly_id)
            
        anomaly_type_val = anomaly.anomaly_type.value
        if anomaly_type_val not in twin.active_anomaly_types:
            twin.active_anomaly_types.append(anomaly_type_val)
            
        twin.updated_at = utc_now_iso()
        return twin
        
    def clear_anomaly(self, sensor_id: str, anomaly_id: str) -> None:
        """Clear an active anomaly from a sensor twin."""
        twin = self._sensor_twins.get(sensor_id)
        if twin and anomaly_id in twin.active_alerts:
            twin.active_alerts.remove(anomaly_id)
            twin.updated_at = utc_now_iso()
            
    def refresh_zone_twin(self, zone_id: str) -> ZoneTwin | None:
        """Recalculate zone aggregate metrics."""
        z_twin = self._zone_twins.get(zone_id)
        if not z_twin:
            return None
            
        sensors = self.get_zone_sensor_twins(zone_id)
        if not sensors:
            return z_twin
            
        z_twin.critical_sensor_count = sum(1 for s in sensors if s.health_status == SensorHealth.CRITICAL.value)
        z_twin.offline_sensor_count = sum(1 for s in sensors if s.status == TwinStatus.OFFLINE)
        
        anomalous_sensors = sum(1 for s in sensors if len(s.active_alerts) > 0)
        z_twin.anomaly_rate_pct = (anomalous_sensors / len(sensors)) * 100.0 if sensors else 0.0
        
        if z_twin.critical_sensor_count > 0:
            z_twin.risk_level = "CRITICAL"
        elif z_twin.offline_sensor_count > 2:
            z_twin.risk_level = "HIGH"
        elif z_twin.anomaly_rate_pct > 20:
            z_twin.risk_level = "MEDIUM"
        else:
            z_twin.risk_level = "LOW"
            
        z_twin.updated_at = utc_now_iso()
        return z_twin
        
    def refresh_plant_twin(self) -> PlantTwin:
        """Aggregate metrics for the entire plant."""
        if not self._plant_twin:
            self._plant_twin = PlantTwin(plant_id="PLANT-MAIN")
            
        sensors = list(self._sensor_twins.values())
        self._plant_twin.total_sensors = len(sensors)
        self._plant_twin.online_sensors = sum(1 for s in sensors if s.status == TwinStatus.ONLINE)
        self._plant_twin.offline_sensors = sum(1 for s in sensors if s.status == TwinStatus.OFFLINE)
        self._plant_twin.critical_sensors = sum(1 for s in sensors if s.health_status == SensorHealth.CRITICAL.value)
        
        if self._plant_twin.total_sensors > 0:
            self._plant_twin.fleet_health_pct = (self._plant_twin.online_sensors / self._plant_twin.total_sensors) * 100.0
        else:
            self._plant_twin.fleet_health_pct = 100.0
            
        zones = list(self._zone_twins.values())
        if any(z.risk_level == "CRITICAL" for z in zones):
            self._plant_twin.overall_risk_level = "CRITICAL"
        elif any(z.risk_level == "HIGH" for z in zones):
            self._plant_twin.overall_risk_level = "HIGH"
        elif any(z.risk_level == "MEDIUM" for z in zones):
            self._plant_twin.overall_risk_level = "MEDIUM"
        else:
            self._plant_twin.overall_risk_level = "LOW"
            
        self._plant_twin.updated_at = utc_now_iso()
        return self._plant_twin
