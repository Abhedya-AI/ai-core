"""
sensor/domain/rule_models.py — Rule Engine domain models.

Configurable rule engine supporting threshold rules, combined conditions,
time-based rules, cross-sensor rules, zone-level rules, and escalation.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class RulePriority(str, Enum):
    """Priority levels for rules."""
    P1 = "CRITICAL"
    P2 = "HIGH"
    P3 = "MEDIUM"
    P4 = "LOW"
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"



class RuleConditionOperator(str, Enum):
    """Operators for rule conditions."""
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"
    EQ = "EQ"
    NEQ = "NEQ"
    BETWEEN = "BETWEEN"
    OUTSIDE = "OUTSIDE"
    CONTAINS = "CONTAINS"


class RuleActionType(str, Enum):
    """Types of actions that can be triggered by a rule."""
    PUBLISH_EVENT = "PUBLISH_EVENT"
    NOTIFY_SUPERVISOR = "NOTIFY_SUPERVISOR"
    TRIGGER_ALERT = "TRIGGER_ALERT"
    LOG_WARNING = "LOG_WARNING"
    ESCALATE = "ESCALATE"
    DISPATCH_MAINTENANCE = "DISPATCH_MAINTENANCE"


class RuleScope(str, Enum):
    """Scope at which a rule applies."""
    SENSOR = "SENSOR"
    EQUIPMENT = "EQUIPMENT"
    ZONE = "ZONE"
    PLANT = "PLANT"
    CROSS_SENSOR = "CROSS_SENSOR"


class RuleCondition(BaseModel):
    """A condition that must be met for a rule to trigger."""
    model_config = ConfigDict(frozen=True)

    field: str = Field(description="The field to evaluate, e.g. 'value', 'rate_of_change'")
    operator: RuleConditionOperator = Field(description="Operator for the condition")
    threshold: float | None = Field(default=None, description="Primary threshold value")
    threshold_min: float | None = Field(default=None, description="Minimum threshold for BETWEEN/OUTSIDE")
    threshold_max: float | None = Field(default=None, description="Maximum threshold for BETWEEN/OUTSIDE")
    sensor_type_filter: str | None = Field(default=None, description="Only apply this condition to a specific SensorType")
    time_window_sec: int | None = Field(default=None, description="Time window in seconds for time-based conditions")
    peer_sensor_id: str | None = Field(default=None, description="Peer sensor ID for cross-sensor rules")


class RuleAction(BaseModel):
    """An action executed when a rule triggers."""
    model_config = ConfigDict(frozen=True)

    action_type: RuleActionType = Field(description="Type of action to execute")
    severity: str = Field(default="HIGH", description="Severity level of the action")
    message_template: str = Field(default="", description="Message template for notifications or logs")
    escalation_target: str | None = Field(default=None, description="Target for escalation, e.g., supervisor")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional action context metadata")


class SensorRule(BaseModel):
    """A configurable rule applied to sensor data."""
    model_config = ConfigDict(frozen=True)

    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the rule")
    name: str = Field(description="Name of the rule")
    description: str = Field(default="", description="Description of what the rule does")
    scope: RuleScope = Field(default=RuleScope.SENSOR, description="Scope of the rule")
    sensor_id: str | None = Field(default=None, description="Specific sensor ID this rule applies to. If None, applies to all matching sensors")
    sensor_type_filter: str | None = Field(default=None, description="Filter for a specific SensorType (e.g. TEMPERATURE)")
    zone_id: str | None = Field(default=None, description="Apply rule to sensors in a specific zone")
    equipment_id: str | None = Field(default=None, description="Apply rule to sensors on specific equipment")
    conditions: list[RuleCondition] = Field(default_factory=list, description="Conditions that must ALL be satisfied (AND logic)")
    actions: list[RuleAction] = Field(default_factory=list, description="Actions to execute when conditions are met")
    priority: RulePriority = Field(default=RulePriority.P3, description="Priority of this rule")
    cooldown_sec: float = Field(default=300.0, description="Minimum seconds between consecutive triggers")
    enabled: bool = Field(default=True, description="Whether the rule is actively evaluating")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Creation UTC timestamp")


class RuleTriggerRecord(BaseModel):
    """A record of a rule being triggered by sensor data."""
    model_config = ConfigDict()

    trigger_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for the trigger instance")
    rule_id: str = Field(description="ID of the rule that triggered")
    sensor_id: str = Field(description="ID of the sensor that caused the trigger")
    triggered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Trigger UTC timestamp")
    matched_conditions: list[str] = Field(default_factory=list, description="List of condition descriptions that matched")
    actions_executed: list[str] = Field(default_factory=list, description="List of action types executed")
    value_at_trigger: float = Field(description="The primary sensor value when the rule triggered")
