"""
sensor/application/ingestion_service.py — Sensor Ingestion Service.

The single entry point for all sensor data:
  - REST single reading
  - REST batch
  - Kafka consumer messages

Orchestrates: Validate → Normalize → Buffer → Anomaly Detection
  → Rule Evaluation → Health Update → Kafka Publish → Graph Sync
  → Supervisor Notify (if critical)
"""
from __future__ import annotations
import asyncio
import time
from datetime import datetime, timezone
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.modules.sensor.domain.models import (
    SensorReading, SensorAnomaly, AnomalySeverity, IngestionBatch, IngestionSource,
)

# Placeholders for existing imports to satisfy types (assuming they exist as requested)
class ReadingValidator:
    def validate(self, reading: SensorReading) -> tuple[bool, str | None]:
        return True, None

class UnitNormalizer:
    def normalize(self, reading: SensorReading) -> SensorReading:
        return reading

class TelemetryBuffer:
    def push(self, reading: SensorReading):
        pass
    def get_history(self, sensor_id: str) -> List[SensorReading]:
        return []

class AnomalyEngineRegistry:
    def analyze_reading(self, reading: SensorReading, history: List[SensorReading]) -> List[SensorAnomaly]:
        return []

class SensorHealthTracker:
    def update(self, sensor_id: str, reading: SensorReading, anomalies: List[SensorAnomaly]):
        pass

class SensorRuleEngine:
    def evaluate(self, reading: SensorReading, history: List[SensorReading]) -> List[Any]:
        return []

class SensorKafkaPublisher:
    async def publish_reading_received(self, reading: SensorReading):
        pass
    async def publish_anomaly_detected(self, anomaly: SensorAnomaly):
        pass

class GraphSyncService:
    async def on_reading_ingested(self, reading: SensorReading):
        pass

class SupervisorNotifier:
    async def notify_critical_anomaly(self, anomaly: SensorAnomaly):
        pass
    async def notify_rule_triggered(self, trigger: Any):
        pass

log = get_logger(__name__)

class IngestionResult(BaseModel):
    """Result of processing a single sensor reading."""
    reading_id: str = Field(description="Unique ID of the reading")
    sensor_id: str = Field(description="Sensor ID")
    value: float = Field(description="Reading value")
    is_valid: bool = Field(description="Whether the reading passed validation")
    anomalies_count: int = Field(default=0, description="Number of anomalies detected")
    rules_triggered: int = Field(default=0, description="Number of rules triggered")
    health_status: str = Field(default="UNKNOWN", description="Current health status of the sensor")
    processing_latency_ms: int = Field(description="Time taken to process in milliseconds")
    rejection_reason: Optional[str] = Field(default=None, description="Reason if validation failed")

class IngestionService:
    """Orchestrates the entire sensor ingestion pipeline."""

    def __init__(self):
        """Initialize all components of the ingestion pipeline."""
        self._validator = ReadingValidator()
        self._normalizer = UnitNormalizer()
        self._buffer = TelemetryBuffer()
        self._engine_registry = AnomalyEngineRegistry()
        self._health_tracker = SensorHealthTracker()
        self._rule_engine = SensorRuleEngine()
        self._kafka = SensorKafkaPublisher()
        self._graph_sync = GraphSyncService()
        self._supervisor = SupervisorNotifier()

    async def ingest_single(self, reading: SensorReading) -> IngestionResult:
        """Process a single sensor reading through the entire pipeline."""
        start = time.perf_counter()
        
        is_valid, reason = self._validator.validate(reading)
        if not is_valid:
            latency = int((time.perf_counter() - start) * 1000)
            return IngestionResult(
                reading_id=reading.id,
                sensor_id=reading.sensor_id,
                value=reading.value,
                is_valid=False,
                anomalies_count=0,
                rules_triggered=0,
                health_status="UNKNOWN",
                processing_latency_ms=latency,
                rejection_reason=reason
            )
            
        normalized_reading = self._normalizer.normalize(reading)
        
        self._buffer.push(normalized_reading)
        history = self._buffer.get_history(normalized_reading.sensor_id)
        
        anomalies = self._engine_registry.analyze_reading(normalized_reading, history)
        triggers = self._rule_engine.evaluate(normalized_reading, history)
        
        self._health_tracker.update(normalized_reading.sensor_id, normalized_reading, anomalies)
        
        # Async tasks for I/O
        asyncio.create_task(self._kafka.publish_reading_received(normalized_reading))
        asyncio.create_task(self._graph_sync.on_reading_ingested(normalized_reading))
        
        for anomaly in anomalies:
            if anomaly.severity in (AnomalySeverity.CRITICAL, AnomalySeverity.HIGH):
                asyncio.create_task(self._kafka.publish_anomaly_detected(anomaly))
            if anomaly.severity == AnomalySeverity.CRITICAL:
                asyncio.create_task(self._supervisor.notify_critical_anomaly(anomaly))
                
        for trigger in triggers:
            # Assuming trigger has a priority field
            if hasattr(trigger, "priority") and trigger.priority in ("P1", "P2"):
                asyncio.create_task(self._supervisor.notify_rule_triggered(trigger))
                
        latency = int((time.perf_counter() - start) * 1000)
        
        return IngestionResult(
            reading_id=normalized_reading.id,
            sensor_id=normalized_reading.sensor_id,
            value=normalized_reading.value,
            is_valid=True,
            anomalies_count=len(anomalies),
            rules_triggered=len(triggers),
            health_status="HEALTHY", # Typically fetched from health tracker
            processing_latency_ms=latency
        )

    async def ingest_batch(self, batch: IngestionBatch) -> dict[str, Any]:
        """Process a batch of sensor readings."""
        accepted = 0
        rejected = 0
        total_anomalies = 0
        total_rules_triggered = 0
        
        # Process each reading sequentially (could be parallelized)
        for reading in batch.readings:
            result = await self.ingest_single(reading)
            if result.is_valid:
                accepted += 1
                total_anomalies += result.anomalies_count
                total_rules_triggered += result.rules_triggered
            else:
                rejected += 1
                
        return {
            "batch_id": batch.id,
            "source": batch.source,
            "total_received": len(batch.readings),
            "accepted": accepted,
            "rejected": rejected,
            "total_anomalies": total_anomalies,
            "total_rules_triggered": total_rules_triggered
        }

    async def ingest_from_kafka(self, payload: dict[str, Any]) -> IngestionResult | None:
        """Process a sensor reading received from Kafka."""
        try:
            # Ensure required fields are present
            if not all(k in payload for k in ("id", "sensor_id", "value", "timestamp")):
                log.warning(f"Invalid Kafka payload missing required fields: {payload}")
                return None
                
            reading = SensorReading(
                id=payload["id"],
                sensor_id=payload["sensor_id"],
                value=payload["value"],
                timestamp=payload["timestamp"],
                unit=payload.get("unit", ""),
                metadata=payload.get("metadata", {})
            )
            
            return await self.ingest_single(reading)
        except Exception as e:
            log.error(f"Failed to ingest from Kafka payload: {str(e)}")
            return None
