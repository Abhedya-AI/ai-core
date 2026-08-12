"""
sensor/domain/digital_twin.py — Sensor Digital Twin domain models.

A Digital Twin is the live, graph-synchronized virtual representation
of every physical sensor, equipment unit, zone, and plant.

Updated automatically by the Knowledge Graph sync layer on every:
  - Sensor reading ingestion
  - Health state transition
  - Anomaly detection
  - Rule trigger
  - Maintenance event
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class TwinStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"
    CALIBRATING = "CALIBRATING"
    MAINTENANCE = "MAINTENANCE"
    UNKNOWN = "UNKNOWN"

class SensorTwin(BaseModel):
    """Live virtual representation of one physical sensor."""
    twin_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sensor_id: str
    name: str = ""
    sensor_type: str = ""
    unit: str = ""
    zone_id: str | None = None
    equipment_id: str | None = None
    plant_id: str | None = None
    status: TwinStatus = TwinStatus.ONLINE
    last_reading_value: float | None = None
    last_reading_timestamp: str | None = None
    last_reading_unit: str | None = None
    health_status: str = "HEALTHY"
    consecutive_anomalies: int = 0
    total_readings: int = 0
    uptime_pct: float = 100.0
    active_alerts: list[str] = Field(default_factory=list)
    active_anomaly_types: list[str] = Field(default_factory=list)
    connected_sensors: list[str] = Field(default_factory=list)
    last_maintenance: str | None = None
    failure_probability: float = 0.0
    estimated_rul_hours: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    updated_at: str = Field(default_factory=utc_now_iso)
    created_at: str = Field(default_factory=utc_now_iso)

class EquipmentTwin(BaseModel):
    """Virtual representation of equipment."""
    twin_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    equipment_id: str
    name: str = ""
    equipment_type: str = ""
    zone_id: str | None = None
    plant_id: str | None = None
    status: TwinStatus = TwinStatus.ONLINE
    sensor_twins: list[str] = Field(default_factory=list)
    overall_health_pct: float = 100.0
    critical_sensor_count: int = 0
    offline_sensor_count: int = 0
    active_alerts: list[str] = Field(default_factory=list)
    last_maintenance: str | None = None
    operating_hours: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    updated_at: str = Field(default_factory=utc_now_iso)

class ZoneTwin(BaseModel):
    """Virtual representation of a plant zone."""
    twin_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    zone_id: str
    name: str = ""
    plant_id: str | None = None
    status: TwinStatus = TwinStatus.ONLINE
    sensor_twins: list[str] = Field(default_factory=list)
    equipment_twins: list[str] = Field(default_factory=list)
    worker_count: int = 0
    risk_level: str = "LOW"
    active_alerts: list[str] = Field(default_factory=list)
    sensor_coverage_pct: float = 100.0
    critical_sensor_count: int = 0
    offline_sensor_count: int = 0
    anomaly_rate_pct: float = 0.0
    updated_at: str = Field(default_factory=utc_now_iso)

class PlantTwin(BaseModel):
    """Plant-level digital twin (top of hierarchy)."""
    twin_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plant_id: str
    name: str = ""
    zone_twins: list[str] = Field(default_factory=list)
    total_sensors: int = 0
    online_sensors: int = 0
    offline_sensors: int = 0
    critical_sensors: int = 0
    total_equipment: int = 0
    fleet_health_pct: float = 100.0
    overall_risk_level: str = "LOW"
    active_incidents: int = 0
    updated_at: str = Field(default_factory=utc_now_iso)
