"""
sensor/infrastructure/kafka_publisher.py — Sensor Kafka Event Publisher.

Publishes all sensor domain events to Kafka with:
  - Exponential backoff retry (max 3 attempts)
  - Dead letter queue via Topics.SENSOR_DLQ (logged locally)
  - Per-event metrics (published count, failed count)
  - Structured payloads matching the AgentDomainEvent contract
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.infrastructure.kafka.registry import Topics
from app.modules.sensor.domain.models import SensorReading, SensorAnomaly, SensorHealthState
from app.modules.sensor.domain.rule_models import RuleTriggerRecord
from app.modules.sensor.domain.correlation_models import CorrelationAlert
from app.modules.sensor.domain.analytics_models import SensorAnalyticsReport

log = get_logger("app.modules.sensor.infrastructure.kafka_publisher")

class SensorKafkaPublisher:
    """
    Publishes sensor-related events to Kafka.
    Handles retries and fallback to a dead letter log.
    """

    def __init__(self) -> None:
        """Initialize the Kafka publisher with metrics tracking."""
        self._bus = EventBus.get()
        self._published: int = 0
        self._failed: int = 0

    async def _publish_with_retry(self, topic: str, payload: dict[str, Any], key: str, max_retries: int = 3) -> bool:
        """
        Attempt to publish a message with exponential backoff.
        
        Args:
            topic: Kafka topic to publish to.
            payload: Message payload.
            key: Partition key.
            max_retries: Maximum number of retry attempts.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        for attempt in range(max_retries):
            try:
                await self._bus.publish(topic, payload, key=key)
                self._published += 1
                return True
            except Exception as e:
                backoff = 0.1 * (2 ** attempt)
                log.warning(f"Failed to publish to {topic}, retrying in {backoff}s. Error: {e}")
                await asyncio.sleep(backoff)
        
        log.error(f"[DLQ] Failed to publish message to topic {topic} after {max_retries} retries. Key: {key}, Payload: {payload}")
        self._failed += 1
        return False

    async def publish_reading_received(self, reading: SensorReading) -> bool:
        """Publish a sensor reading received event."""
        payload = {
            "event_type": "SensorReadingReceived",
            "sensor_id": reading.sensor_id,
            "value": reading.value,
            "unit": reading.unit,
            "timestamp": reading.timestamp.isoformat() if isinstance(reading.timestamp, datetime) else reading.timestamp,
            "quality_score": reading.quality_score,
        }
        return await self._publish_with_retry(getattr(Topics, "SENSOR_READING_CREATED", "SENSOR_READING_CREATED"), payload, key=reading.sensor_id)

    async def publish_anomaly_detected(self, anomaly: SensorAnomaly) -> bool:
        """Publish an anomaly detected event."""
        payload = anomaly.model_dump()
        payload["event_type"] = "SensorAnomalyDetected"
        if isinstance(payload.get("timestamp"), datetime):
            payload["timestamp"] = payload["timestamp"].isoformat()
        return await self._publish_with_retry(getattr(Topics, "SENSOR_ANOMALY_DETECTED", "SENSOR_ANOMALY_DETECTED"), payload, key=anomaly.sensor_id)

    async def publish_health_updated(self, state: SensorHealthState) -> bool:
        """Publish a sensor health state update event."""
        payload = state.model_dump()
        payload["event_type"] = "SensorHealthUpdated"
        if isinstance(payload.get("last_updated"), datetime):
            payload["last_updated"] = payload["last_updated"].isoformat()
        if isinstance(payload.get("last_maintenance"), datetime):
            payload["last_maintenance"] = payload["last_maintenance"].isoformat()
        return await self._publish_with_retry(getattr(Topics, "SENSOR_HEALTH_CHANGED", "SENSOR_HEALTH_CHANGED"), payload, key=state.sensor_id)

    async def publish_sensor_offline(self, sensor_id: str) -> bool:
        """Publish a sensor offline event."""
        payload = {
            "event_type": "SensorOffline",
            "sensor_id": sensor_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return await self._publish_with_retry(getattr(Topics, "SENSOR_HEALTH_CHANGED", "SENSOR_HEALTH_CHANGED"), payload, key=sensor_id)

    async def publish_sensor_recovered(self, sensor_id: str) -> bool:
        """Publish a sensor recovered event."""
        payload = {
            "event_type": "SensorRecovered",
            "sensor_id": sensor_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return await self._publish_with_retry(getattr(Topics, "SENSOR_HEALTH_CHANGED", "SENSOR_HEALTH_CHANGED"), payload, key=sensor_id)

    async def publish_maintenance_required(self, sensor_id: str, reason: str, failure_probability: float) -> bool:
        """Publish a sensor maintenance required event."""
        payload = {
            "event_type": "SensorMaintenanceRequired",
            "sensor_id": sensor_id,
            "reason": reason,
            "failure_probability": failure_probability,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        topic = getattr(Topics, "SENSOR_CALIBRATION_REQUIRED", "SENSOR_CALIBRATION_REQUIRED")
        return await self._publish_with_retry(topic, payload, key=sensor_id)

    async def publish_rule_triggered(self, record: RuleTriggerRecord) -> bool:
        """Publish a sensor rule triggered event."""
        payload = record.model_dump()
        payload["event_type"] = "SensorRuleTriggered"
        if isinstance(payload.get("triggered_at"), datetime):
            payload["triggered_at"] = payload["triggered_at"].isoformat()
        topic = getattr(Topics, "SENSOR_THRESHOLD_VIOLATED", getattr(Topics, "RISK_THRESHOLD_BREACHED", "SENSOR_THRESHOLD_VIOLATED"))
        return await self._publish_with_retry(topic, payload, key=record.sensor_id)

    async def publish_correlation_detected(self, alert: CorrelationAlert) -> bool:
        """Publish a correlation detected event."""
        payload = alert.model_dump()
        payload["event_type"] = "SensorCorrelationDetected"
        if isinstance(payload.get("created_at"), datetime):
            payload["created_at"] = payload["created_at"].isoformat()
        return await self._publish_with_retry(getattr(Topics, "SENSOR_ANOMALY_DETECTED", "SENSOR_ANOMALY_DETECTED"), payload, key=alert.primary_sensor_id)

    async def publish_analytics_generated(self, report: SensorAnalyticsReport) -> bool:
        """Publish a sensor analytics generated report event."""
        payload = {
            "event_type": "SensorAnalyticsGenerated",
            "sensor_id": report.sensor_id,
            "summary": report.summary,
            "failure_probability": report.failure_probability,
            "trend_direction": report.trend_direction,
            "uptime_pct": report.uptime_pct,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        topic = getattr(Topics, "SENSOR_FLEET_REPORT", "SENSOR_FLEET_REPORT")
        return await self._publish_with_retry(topic, payload, key=report.sensor_id)

    def metrics(self) -> dict[str, Any]:
        """
        Get the metrics for published messages.
        
        Returns:
            Dictionary with published count, failed count, and success rate.
        """
        total = self._published + self._failed
        success_rate = (self._published / total * 100) if total > 0 else 100.0
        return {
            "published": self._published,
            "failed": self._failed,
            "success_rate": round(success_rate, 2)
        }
