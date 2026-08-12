"""
app/api/v1/sensor_history.py — Sensor Historical Data API.

Tag: History
Prefix: /sensor-history  
"""
from __future__ import annotations
import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Query, Path

from app.api.responses import StandardResponse, PaginatedResponse, make_response, ResponseMetadata, PaginationMeta
from app.api.exceptions import NotFoundError, ValidationError
from app.modules.sensor.application.telemetry_buffer import TelemetryBuffer
from app.modules.sensor.infrastructure.sensor_neo4j_repository import SensorNeo4jRepository
from app.core.logging import get_logger

log = get_logger("api.v1.sensor_history")

router = APIRouter(prefix="/sensor-history", tags=["History"])

_buffer = TelemetryBuffer()
_neo4j_repo = SensorNeo4jRepository()

@router.get("/{sensor_id}", response_model=PaginatedResponse, summary="Get Historical Readings", description="Get reading history for a sensor.")
async def get_history(
    sensor_id: str = Path(..., description="Sensor ID"),
    from_timestamp: Optional[datetime] = Query(None, description="Start timestamp"),
    to_timestamp: Optional[datetime] = Query(None, description="End timestamp"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    page: int = Query(1, ge=1, description="Page number")
):
    try:
        # In a real impl, this might query Neo4j or a time-series DB.
        # Here we will try Neo4j or fallback to buffer
        readings = await _neo4j_repo.get_readings_history(
            sensor_id=sensor_id, 
            start_time=from_timestamp, 
            end_time=to_timestamp, 
            limit=limit, 
            offset=(page-1)*limit
        )
        
        return make_response(
            data=[r.dict() if hasattr(r, 'dict') else r for r in readings] if isinstance(readings, list) else readings,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to get history for {sensor_id}: {str(e)}")
        raise ValidationError(message=f"Failed to retrieve history: {str(e)}")

@router.get("/{sensor_id}/anomaly-events", response_model=StandardResponse, summary="Get Anomaly Events", description="Get anomaly events for a sensor from Neo4j.")
async def get_anomaly_events(
    sensor_id: str = Path(..., description="Sensor ID"),
    limit: int = Query(50, ge=1, le=1000, description="Max results")
):
    try:
        events = await _neo4j_repo.get_sensor_anomalies(sensor_id=sensor_id, limit=limit)
        return make_response(
            data=[e.dict() if hasattr(e, 'dict') else e for e in events] if isinstance(events, list) else events,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to get anomaly events for {sensor_id}: {str(e)}")
        raise ValidationError(message=f"Failed to retrieve anomaly events: {str(e)}")

@router.get("/fleet/reading-count", response_model=StandardResponse, summary="Get Fleet Reading Count", description="Total readings per sensor (from Neo4j).")
async def get_reading_count():
    try:
        counts = await _neo4j_repo.get_fleet_reading_counts()
        return make_response(
            data=counts,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to get fleet reading count: {str(e)}")
        raise ValidationError(message=f"Failed to retrieve reading counts: {str(e)}")
