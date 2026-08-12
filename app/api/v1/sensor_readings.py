"""
app/api/v1/sensor_readings.py — Sensor Readings Ingest & History API.

Tag: Sensor Readings
Prefix: /sensor-readings
"""
from __future__ import annotations
import uuid
import asyncio
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Query, Path, Body
from pydantic import BaseModel, Field

from app.api.responses import StandardResponse, PaginatedResponse, make_response
from app.api.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.modules.sensor.domain.models import SensorReading, IngestionBatch, IngestionSource, AnomalySeverity
from app.modules.sensor.application.validators import ReadingValidator
from app.modules.sensor.application.normalizer import UnitNormalizer
from app.modules.sensor.application.telemetry_buffer import TelemetryBuffer
from app.modules.sensor.analysis.engine_registry import AnomalyEngineRegistry
from app.modules.sensor.application.health_tracker import SensorHealthTracker
from app.modules.sensor.application.rule_engine import SensorRuleEngine
from app.modules.sensor.infrastructure.kafka_publisher import SensorKafkaPublisher
from app.modules.sensor.application.graph_sync_service import GraphSyncService
from app.modules.sensor.application.supervisor_notifier import SupervisorNotifier

log = get_logger("api.v1.sensor_readings")

router = APIRouter(prefix="/sensor-readings", tags=["Sensor Readings"])

_buffer = TelemetryBuffer()
_validator = ReadingValidator()
_normalizer = UnitNormalizer()
_engine_registry = AnomalyEngineRegistry()
_health_tracker = SensorHealthTracker()
_rule_engine = SensorRuleEngine()
_kafka = SensorKafkaPublisher()
_graph_sync = GraphSyncService()
_supervisor = SupervisorNotifier()


class ReadingIngestRequest(BaseModel):
    sensor_id: str = Field(..., description="ID of the sensor")
    value: float = Field(..., description="Sensor reading value")
    unit: Optional[str] = Field(None, description="Unit of the reading")
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Timestamp of reading")
    quality_score: float = Field(1.0, description="Quality score of reading from 0.0 to 1.0")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional reading metadata")

class BatchIngestRequest(BaseModel):
    readings: list[ReadingIngestRequest] = Field(..., description="List of readings to ingest")
    source: IngestionSource = Field(IngestionSource.REST, description="Source of ingestion")


@router.post("", response_model=StandardResponse, summary="Ingest Reading", description="Ingest a single sensor reading and process through the pipeline.")
async def ingest_reading(request: ReadingIngestRequest):
    start_time = datetime.now(timezone.utc)
    
    try:
        raw_reading = SensorReading(
            sensor_id=request.sensor_id,
            value=request.value,
            unit=request.unit or "",
            timestamp=request.timestamp or datetime.now(timezone.utc).isoformat(),
            quality_score=request.quality_score,
            metadata=request.metadata or {}
        )

        is_valid, errors = _validator.validate(raw_reading)
        if not is_valid:
            raise ValidationError(message=f"Invalid reading data: {', '.join(errors)}")
        
        reading = _normalizer.normalize(raw_reading)
        _buffer.push(reading)
        
        history = _buffer.get_values(reading.sensor_id)
        anomalies = _engine_registry.analyze_reading(reading, history)
        rule_triggers = _rule_engine.evaluate(reading, history)
        health_state, _ = _health_tracker.update(reading.sensor_id, reading, anomalies)
        
        await _kafka.publish_reading_received(reading)
        for a in anomalies:
            await _kafka.publish_anomaly_detected(a)
            
        asyncio.create_task(_graph_sync.on_reading_ingested(reading))
        
        has_critical = any(a.severity == AnomalySeverity.CRITICAL for a in anomalies)
        if has_critical:
            for a in anomalies:
                if a.severity == AnomalySeverity.CRITICAL:
                    await _supervisor.notify_critical_anomaly(a)
        
        latency = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        result = {
            "reading_id": reading.reading_id,
            "sensor_id": reading.sensor_id,
            "value": reading.value,
            "anomalies_count": len(anomalies),
            "rules_triggered": len(rule_triggers),
            "health_status": health_state.status.value,
            "processing_latency_ms": round(latency, 2)
        }
        
        return make_response(data=result, trace_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()))
        
    except ValidationError:
        raise
    except Exception as e:
        log.error(f"Failed to ingest reading for sensor {request.sensor_id}: {str(e)}")
        raise ValidationError(message=f"Ingestion pipeline failed: {str(e)}")


@router.post("/batch", response_model=StandardResponse, summary="Batch Ingest Readings", description="Ingest a batch of sensor readings.")
async def ingest_batch(request: BatchIngestRequest):
    start_time = datetime.now(timezone.utc)
    accepted = 0
    rejected = 0
    total_anomalies = 0
    
    for item in request.readings:
        try:
            raw_reading = SensorReading(
                sensor_id=item.sensor_id,
                value=item.value,
                unit=item.unit or "",
                timestamp=item.timestamp or datetime.now(timezone.utc).isoformat(),
                quality_score=item.quality_score,
                metadata=item.metadata or {}
            )
            is_valid, _ = _validator.validate(raw_reading)
            if not is_valid:
                rejected += 1
                continue
            
            reading = _normalizer.normalize(raw_reading)
            _buffer.push(reading)
            history = _buffer.get_values(reading.sensor_id)
            anomalies = _engine_registry.analyze_reading(reading, history)
            _health_tracker.update(reading.sensor_id, reading, anomalies)
            
            total_anomalies += len(anomalies)
            accepted += 1
        except Exception:
            rejected += 1

    latency = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
    
    return make_response(
        data={
            "accepted": accepted,
            "rejected": rejected,
            "total_anomalies": total_anomalies,
            "processing_latency_ms": round(latency, 2)
        },
        trace_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4())
    )


@router.get("/{sensor_id}/recent", response_model=StandardResponse, summary="Recent Readings", description="Get N most recent readings for a sensor.")
async def get_recent_readings(
    sensor_id: str = Path(..., description="Sensor ID"),
    limit: int = Query(50, ge=1, le=1000, description="Max readings to return")
):
    readings = _buffer.get_recent(sensor_id, count=limit)
    return make_response(
        data=[r.model_dump() if hasattr(r, 'model_dump') else r for r in readings],
        trace_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4())
    )


@router.get("/{sensor_id}/stats", response_model=StandardResponse, summary="Sensor Statistics", description="Basic statistics for buffered readings of a sensor.")
async def get_sensor_stats(sensor_id: str = Path(..., description="Sensor ID")):
    values = _buffer.get_values(sensor_id)
    if not values:
        stats = {"sensor_id": sensor_id, "count": 0, "mean": 0.0, "min": 0.0, "max": 0.0}
    else:
        stats = {
            "sensor_id": sensor_id,
            "count": len(values),
            "mean": round(sum(values) / len(values), 4),
            "min": min(values),
            "max": max(values)
        }
    return make_response(data=stats, trace_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()))
