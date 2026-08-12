"""
extended_entities.py — Domain entity models for Plant, Reading, Alert, Emergency,
Inspection, Risk, Recommendation, Policy, Standard, PPE, and Device.
"""

from typing import Any
from pydantic import Field

from app.modules.knowledge.domain.entities.base import (
    AssetEntity,
    EventEntity,
    GraphEntity,
    LocationEntity,
    ObservationEntity,
)


class Plant(LocationEntity):
    """Industrial plant facility entity."""

    address: str | None = Field(default=None, description="Physical address of the plant")
    capacity: str | None = Field(default=None, description="Operating capacity specification")
    entity_type: str = Field(default="Plant")


class Reading(ObservationEntity):
    """Sensor or device metric reading entity."""

    sensor_id: str = Field(default="", description="Source sensor ID")
    metric: str = Field(default="telemetry", description="Metric type (temperature, pressure, etc.)")
    value: float = Field(default=0.0, description="Numeric reading value")
    unit: str | None = Field(default=None, description="Unit of measurement")
    entity_type: str = Field(default="Reading")


class Alert(EventEntity):
    """Safety or operational alert entity."""

    severity: str = Field(default="WARNING", description="Alert severity: INFO, WARNING, CRITICAL")
    source_id: str | None = Field(default=None, description="ID of entity generating the alert")
    message: str = Field(default="", description="Detailed alert message")
    entity_type: str = Field(default="Alert")


class Emergency(EventEntity):
    """Emergency condition or escalation event."""

    emergency_type: str = Field(default="GENERAL", description="Type of emergency: FIRE, GAS_LEAK, STRUCTURAL, etc.")
    zone_id: str | None = Field(default=None, description="Associated zone ID")
    active: bool = Field(default=True, description="Whether emergency is currently active")
    entity_type: str = Field(default="Emergency")


class Inspection(EventEntity):
    """Safety or compliance inspection record entity."""

    inspector_id: str | None = Field(default=None, description="Worker ID of inspector")
    target_id: str | None = Field(default=None, description="ID of inspected equipment/zone")
    passed: bool = Field(default=True, description="Inspection result pass/fail status")
    findings: str = Field(default="", description="Summary of inspection findings")
    entity_type: str = Field(default="Inspection")


class Risk(GraphEntity):
    """Risk assessment entity in the knowledge graph."""

    category: str = Field(default="OPERATIONAL", description="Risk category: FIRE, CHEMICAL, ELECTRICAL, etc.")
    risk_score: float = Field(default=0.0, description="Normalized risk score [0.0 - 1.0]")
    description: str = Field(default="", description="Detailed risk assessment summary")
    status: str = Field(default="ACTIVE", description="Risk status: ACTIVE, MITIGATED, MONITORING")
    entity_type: str = Field(default="Risk")


class Recommendation(GraphEntity):
    """Actionable safety recommendation entity."""

    title: str = Field(default="", description="Short recommendation title")
    action_item: str = Field(default="", description="Prescriptive action required")
    priority: str = Field(default="MEDIUM", description="Recommendation priority: LOW, MEDIUM, HIGH, URGENT")
    category: str = Field(default="PREVENTIVE", description="Category: PREVENTIVE, CORRECTIVE, MITIGATIVE")
    entity_type: str = Field(default="Recommendation")


class Policy(GraphEntity):
    """Industrial safety policy document entity."""

    name: str = Field(default="", description="Policy title")
    code: str = Field(default="", description="Policy identifier code")
    category: str = Field(default="SAFETY", description="Policy domain category")
    content: str = Field(default="", description="Policy text or reference link")
    entity_type: str = Field(default="Policy")


class Standard(GraphEntity):
    """Regulatory or industry compliance standard entity."""

    code: str = Field(default="", description="Standard code e.g. OSHA-1910, ISO-45001")
    issuer: str = Field(default="ISO", description="Standard governing body: OSHA, ISO, NFPA, etc.")
    title: str = Field(default="", description="Title of standard document")
    requirements: dict[str, Any] = Field(default_factory=dict, description="Structured requirement rules")
    entity_type: str = Field(default="Standard")


class PPE(AssetEntity):
    """Personal Protective Equipment asset entity."""

    ppe_type: str = Field(default="HELMET", description="Type of PPE: HELMET, RESPIRATOR, GLOVES, VEST, HARNESS")
    condition: str = Field(default="GOOD", description="PPE condition: NEW, GOOD, INSPECTION_REQUIRED, REPLACED")
    last_inspected: str | None = Field(default=None, description="ISO timestamp of last inspection")
    entity_type: str = Field(default="PPE")


class Device(AssetEntity):
    """Industrial IoT gateway, edge node, or monitoring device entity."""

    device_type: str = Field(default="GATEWAY", description="Device class: GATEWAY, CONTROLLER, TRANSMITTER")
    ip_address: str | None = Field(default=None, description="Network IP address of device")
    status: str = Field(default="ONLINE", description="Device status: ONLINE, OFFLINE, DEGRADED")
    entity_type: str = Field(default="Device")
