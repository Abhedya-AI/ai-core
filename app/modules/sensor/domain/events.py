"""
sensor/domain/events.py — Domain event factories for Sensor Intelligence.

All sensor domain events are emitted as AgentDomainEvent instances
to maintain compatibility with the existing EventBus → EventBridge
→ WebSocket/SSE pipeline.

Each factory function constructs a fully-formed event with the
correct event_type, payload, and trace context.
"""

from __future__ import annotations

from typing import Any

from app.modules.agents.core.events import AgentDomainEvent
from app.modules.sensor.domain.models import (
    AnomalySeverity,
    SensorAnomaly,
    SensorHealth,
)


AGENT_NAME = "SensorAgent"


def anomaly_detected_event(
    anomaly: SensorAnomaly,
    trace_id: str,
) -> AgentDomainEvent:
    """Emit when any anomaly engine detects an anomaly on a sensor reading.

    Downstream consumers:
      - Risk Agent (adjusts risk score)
      - Dashboard (real-time alert)
      - EventBridge → WebSocket/SSE
    """
    return AgentDomainEvent(
        event_type="SensorAnomalyDetected",
        agent_name=AGENT_NAME,
        trace_id=trace_id,
        payload={
            "anomaly_id": anomaly.anomaly_id,
            "sensor_id": anomaly.sensor_id,
            "anomaly_type": anomaly.anomaly_type.value,
            "severity": anomaly.severity.value,
            "value": anomaly.value,
            "expected_value": anomaly.expected_value,
            "threshold": anomaly.threshold,
            "deviation_sigma": anomaly.deviation_sigma,
            "description": anomaly.description,
            "engine_name": anomaly.engine_name,
            "timestamp": anomaly.timestamp,
        },
    )


def threshold_breached_event(
    sensor_id: str,
    value: float,
    threshold: float,
    direction: str,
    trace_id: str,
) -> AgentDomainEvent:
    """Emit when a reading breaches a configured threshold policy.

    Args:
        direction: "ABOVE" or "BELOW" indicating breach direction.
    """
    severity = "CRITICAL" if abs(value - threshold) / max(abs(threshold), 1.0) > 0.5 else "HIGH"
    return AgentDomainEvent(
        event_type="SensorThresholdBreached",
        agent_name=AGENT_NAME,
        trace_id=trace_id,
        payload={
            "sensor_id": sensor_id,
            "value": value,
            "threshold": threshold,
            "direction": direction,
            "severity": severity,
            "deviation_pct": round(abs(value - threshold) / max(abs(threshold), 1.0) * 100, 2),
        },
    )


def health_changed_event(
    sensor_id: str,
    previous_status: SensorHealth,
    new_status: SensorHealth,
    reason: str,
    trace_id: str,
) -> AgentDomainEvent:
    """Emit when a sensor's health state machine transitions."""
    return AgentDomainEvent(
        event_type="SensorHealthChanged",
        agent_name=AGENT_NAME,
        trace_id=trace_id,
        payload={
            "sensor_id": sensor_id,
            "previous_status": previous_status.value,
            "new_status": new_status.value,
            "reason": reason,
        },
    )


def calibration_required_event(
    sensor_id: str,
    reason: str,
    drift_magnitude: float,
    trace_id: str,
) -> AgentDomainEvent:
    """Emit when drift detection suggests the sensor needs recalibration."""
    return AgentDomainEvent(
        event_type="SensorCalibrationRequired",
        agent_name=AGENT_NAME,
        trace_id=trace_id,
        payload={
            "sensor_id": sensor_id,
            "reason": reason,
            "drift_magnitude": drift_magnitude,
        },
    )


def sensor_offline_event(
    sensor_id: str,
    last_reading_timestamp: str | None,
    trace_id: str,
) -> AgentDomainEvent:
    """Emit when a sensor stops reporting (health → OFFLINE)."""
    return AgentDomainEvent(
        event_type="SensorOffline",
        agent_name=AGENT_NAME,
        trace_id=trace_id,
        payload={
            "sensor_id": sensor_id,
            "last_reading_timestamp": last_reading_timestamp,
        },
    )


def fleet_health_report_event(
    total_sensors: int,
    healthy_count: int,
    degraded_count: int,
    critical_count: int,
    offline_count: int,
    trace_id: str,
) -> AgentDomainEvent:
    """Emit periodic fleet-wide health summary."""
    return AgentDomainEvent(
        event_type="SensorFleetHealthReport",
        agent_name=AGENT_NAME,
        trace_id=trace_id,
        payload={
            "total_sensors": total_sensors,
            "healthy": healthy_count,
            "degraded": degraded_count,
            "critical": critical_count,
            "offline": offline_count,
            "health_pct": round(healthy_count / max(total_sensors, 1) * 100, 1),
        },
    )
