"""
sensor/domain/supervisor_contracts.py — Typed Supervisor Payload Contracts.

All escalations from Sensor Intelligence to the Supervisor use
these typed Pydantic models. Never use raw dicts for inter-agent messages.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class EscalationPriority(str, Enum):
    P1_CRITICAL = "P1_CRITICAL"
    P2_HIGH = "P2_HIGH"
    P3_MEDIUM = "P3_MEDIUM"
    P4_LOW = "P4_LOW"

class EscalationIntent(str, Enum):
    EMERGENCY_INVESTIGATION = "EMERGENCY_INVESTIGATION"
    RISK_ANALYSIS = "RISK_ANALYSIS"
    GENERAL_SAFETY = "GENERAL_SAFETY"
    MAINTENANCE_REQUEST = "MAINTENANCE_REQUEST"
    FLEET_HEALTH_REPORT = "FLEET_HEALTH_REPORT"

class AnomalyReport(BaseModel, frozen=True):
    """Report for an anomaly detected on a sensor."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = "SENSOR_ANOMALY_ESCALATION"
    intent: EscalationIntent
    priority: EscalationPriority
    sensor_id: str
    anomaly_type: str
    severity: str
    value: float
    expected_value: float | None = None
    description: str
    zone_id: str | None = None
    equipment_id: str | None = None
    requires_hitl: bool = False
    confidence: float = 1.0
    timestamp: str = Field(default_factory=utc_now_iso)

class RuleTriggerReport(BaseModel, frozen=True):
    """Report for a threshold/business rule that was triggered."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = "SENSOR_RULE_TRIGGERED"
    intent: EscalationIntent = EscalationIntent.RISK_ANALYSIS
    priority: EscalationPriority
    rule_id: str
    rule_name: str
    sensor_id: str
    matched_conditions: list[str]
    value_at_trigger: float
    zone_id: str | None = None
    equipment_id: str | None = None
    timestamp: str = Field(default_factory=utc_now_iso)

class SensorOfflineReport(BaseModel, frozen=True):
    """Report indicating a sensor has gone offline."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = "SENSOR_OFFLINE_ALERT"
    intent: EscalationIntent = EscalationIntent.GENERAL_SAFETY
    priority: EscalationPriority = EscalationPriority.P2_HIGH
    sensor_id: str
    zone_id: str | None = None
    equipment_id: str | None = None
    offline_since: str | None = None
    timestamp: str = Field(default_factory=utc_now_iso)

class FleetHealthReport(BaseModel, frozen=True):
    """Aggregated report detailing overall sensor fleet health."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = "FLEET_HEALTH_DEGRADED"
    intent: EscalationIntent = EscalationIntent.FLEET_HEALTH_REPORT
    priority: EscalationPriority = EscalationPriority.P2_HIGH
    fleet_health_pct: float
    total_sensors: int
    critical_count: int
    offline_count: int
    degraded_count: int
    top_anomaly_types: list[str]
    at_risk_zones: list[str]
    timestamp: str = Field(default_factory=utc_now_iso)

class MaintenanceRequest(BaseModel, frozen=True):
    """Request for maintaining or repairing a sensor."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = "SENSOR_MAINTENANCE_REQUIRED"
    intent: EscalationIntent = EscalationIntent.MAINTENANCE_REQUEST
    priority: EscalationPriority = EscalationPriority.P3_MEDIUM
    sensor_id: str
    reason: str
    failure_probability: float
    estimated_rul_hours: float | None = None
    zone_id: str | None = None
    equipment_id: str | None = None
    timestamp: str = Field(default_factory=utc_now_iso)
