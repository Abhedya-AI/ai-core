"""
sensor/application/supervisor_notifier.py — Typed Supervisor Notification Bridge.

Sensor Intelligence NEVER invokes downstream agents directly.
All escalations use typed SupervisorContract payloads published via EventBus.
The Supervisor decides whether to invoke Risk, Forecast, Emergency, etc.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.infrastructure.kafka.registry import Topics
from app.modules.sensor.domain.models import SensorAnomaly, AnomalySeverity
# Importing Rule models as required
try:
    from app.modules.sensor.domain.rule_models import RuleTriggerRecord, RulePriority
except ImportError:
    pass

from app.modules.sensor.domain.supervisor_contracts import (
    AnomalyReport, RuleTriggerReport, SensorOfflineReport,
    FleetHealthReport, MaintenanceRequest,
    EscalationPriority, EscalationIntent,
)

log = get_logger(__name__)

class SupervisorNotifier:
    """Bridge for sending typed escalation payloads to the Supervisor agent via EventBus."""
    
    def __init__(self):
        self._bus = EventBus.get()
        
    async def _publish(self, payload_model: BaseModel) -> bool:
        """Serialize payload to dict and publish to AGENT_TASK_REQUESTED."""
        try:
            topic = getattr(Topics, "AGENT_TASK_REQUESTED", "agent.task.requested")
            payload = payload_model.model_dump(mode="json")
            await self._bus.publish(topic, payload)
            log.info(f"Published task request {payload_model.__class__.__name__} to Supervisor.")
            return True
        except Exception as e:
            log.error(f"Failed to publish {payload_model.__class__.__name__} to Supervisor: {e}", exc_info=True)
            return False

    async def notify_critical_anomaly(self, anomaly: SensorAnomaly, zone_id: str | None, equipment_id: str | None) -> bool:
        """Escalate a critical sensor anomaly to the Supervisor."""
        priority = EscalationPriority.P1_CRITICAL if anomaly.severity == AnomalySeverity.CRITICAL else EscalationPriority.P2_HIGH
        intent = EscalationIntent.EMERGENCY_INVESTIGATION if priority == EscalationPriority.P1_CRITICAL else EscalationIntent.RISK_ANALYSIS
        
        report = AnomalyReport(
            intent=intent,
            priority=priority,
            sensor_id=anomaly.sensor_id,
            anomaly_type=anomaly.anomaly_type.value,
            severity=anomaly.severity.value,
            value=anomaly.value,
            expected_value=anomaly.expected_value,
            description=anomaly.description,
            zone_id=zone_id,
            equipment_id=equipment_id,
            requires_hitl=(priority == EscalationPriority.P1_CRITICAL),
            confidence=anomaly.confidence
        )
        return await self._publish(report)

    async def notify_rule_triggered(self, record: Any, rule_name: str, rule_priority: str, zone_id: str | None, equipment_id: str | None) -> bool:
        """Escalate a triggered rule. Only escalate P1/P2 priorities."""
        priority_map = {
            "CRITICAL": EscalationPriority.P1_CRITICAL,
            "HIGH": EscalationPriority.P2_HIGH,
            "MEDIUM": EscalationPriority.P3_MEDIUM,
            "LOW": EscalationPriority.P4_LOW,
        }
        priority = priority_map.get(str(rule_priority).upper(), EscalationPriority.P3_MEDIUM)
        
        if priority not in (EscalationPriority.P1_CRITICAL, EscalationPriority.P2_HIGH):
            log.debug(f"Skipping rule trigger escalation for {rule_name}: priority {priority} too low.")
            return False
            
        report = RuleTriggerReport(
            priority=priority,
            rule_id=getattr(record, "rule_id", "unknown_rule_id"),
            rule_name=rule_name,
            sensor_id=getattr(record, "sensor_id", "unknown_sensor"),
            matched_conditions=getattr(record, "matched_conditions", []),
            value_at_trigger=getattr(record, "value", 0.0),
            zone_id=zone_id,
            equipment_id=equipment_id
        )
        return await self._publish(report)
        
    async def notify_sensor_offline(self, sensor_id: str, zone_id: str | None, equipment_id: str | None) -> bool:
        """Escalate a sensor offline event."""
        report = SensorOfflineReport(
            sensor_id=sensor_id,
            zone_id=zone_id,
            equipment_id=equipment_id,
            offline_since=datetime.now(timezone.utc).isoformat()
        )
        return await self._publish(report)
        
    async def notify_fleet_degraded(self, fleet_health_pct: float, summary: dict) -> bool:
        """Escalate a degraded fleet health state."""
        if fleet_health_pct >= 70.0:
            log.debug(f"Fleet health is {fleet_health_pct}%, skipping escalation.")
            return False
            
        report = FleetHealthReport(
            fleet_health_pct=fleet_health_pct,
            total_sensors=summary.get("total_sensors", 0),
            critical_count=summary.get("critical_count", 0),
            offline_count=summary.get("offline_count", 0),
            degraded_count=summary.get("degraded_count", 0),
            top_anomaly_types=summary.get("top_anomaly_types", []),
            at_risk_zones=summary.get("at_risk_zones", [])
        )
        return await self._publish(report)
        
    async def request_maintenance(self, sensor_id: str, reason: str, failure_prob: float, rul_hours: float | None, zone_id: str | None, equipment_id: str | None) -> bool:
        """Escalate a maintenance request for a sensor."""
        report = MaintenanceRequest(
            sensor_id=sensor_id,
            reason=reason,
            failure_probability=failure_prob,
            estimated_rul_hours=rul_hours,
            zone_id=zone_id,
            equipment_id=equipment_id
        )
        return await self._publish(report)
