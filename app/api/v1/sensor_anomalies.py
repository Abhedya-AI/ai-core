"""
app/api/v1/sensor_anomalies.py — Sensor Anomaly Management API.

Tag: Anomalies
Prefix: /anomalies
"""
from __future__ import annotations
import uuid
from typing import Optional
from fastapi import APIRouter, Query, Path
from pydantic import BaseModel

from app.api.responses import StandardResponse, PaginatedResponse, make_response, ResponseMetadata, PaginationMeta
from app.api.exceptions import NotFoundError, ValidationError
from app.modules.sensor.domain.models import AnomalySeverity, AnomalyType
from app.modules.sensor.analysis.engine_registry import AnomalyEngineRegistry
from app.modules.sensor.application.telemetry_buffer import TelemetryBuffer
from app.core.logging import get_logger

log = get_logger("api.v1.sensor_anomalies")

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])

_engine_registry = AnomalyEngineRegistry()
_buffer = TelemetryBuffer()

_anomaly_store: dict[str, list] = {}

@router.get("", response_model=PaginatedResponse, summary="List Anomalies", description="List all recent anomalies with optional filtering.")
async def list_anomalies(
    sensor_id: Optional[str] = Query(None, description="Filter by sensor ID"),
    severity: Optional[AnomalySeverity] = Query(None, description="Filter by severity"),
    anomaly_type: Optional[AnomalyType] = Query(None, description="Filter by type"),
    limit: int = Query(50, ge=1, le=1000, description="Max results"),
    page: int = Query(1, ge=1, description="Page number")
):
    try:
        results = []
        if sensor_id:
            results = _anomaly_store.get(sensor_id, [])
        else:
            for s_id, anomalies in _anomaly_store.items():
                results.extend(anomalies)
        
        if severity:
            results = [a for a in results if a.severity == severity]
        if anomaly_type:
            results = [a for a in results if a.type == anomaly_type]
            
        # Sort by timestamp descending if possible, assuming dict/object has timestamp
        results = sorted(results, key=lambda x: getattr(x, 'timestamp', 0), reverse=True)
        
        start = (page - 1) * limit
        paginated = results[start:start+limit]
        
        return make_response(
            data=[a.dict() if hasattr(a, 'dict') else a for a in paginated],
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to list anomalies: {str(e)}")
        raise ValidationError(message=f"Failed to list anomalies: {str(e)}")


@router.get("/{sensor_id}", response_model=StandardResponse, summary="Get Anomalies by Sensor", description="Get anomalies for a specific sensor.")
async def get_sensor_anomalies(
    sensor_id: str = Path(..., description="Sensor ID"),
    severity: Optional[AnomalySeverity] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=1000, description="Max results")
):
    anomalies = _anomaly_store.get(sensor_id, [])
    if severity:
        anomalies = [a for a in anomalies if a.severity == severity]
        
    anomalies = sorted(anomalies, key=lambda x: getattr(x, 'timestamp', 0), reverse=True)[:limit]
    
    return make_response(
        data=[a.dict() if hasattr(a, 'dict') else a for a in anomalies],
        trace_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4())
    )


@router.get("/summary", response_model=StandardResponse, summary="Anomaly Summary", description="Aggregated counts by type and severity.")
async def get_anomaly_summary():
    try:
        summary = {
            "by_severity": {},
            "by_type": {}
        }
        for s_id, anomalies in _anomaly_store.items():
            for a in anomalies:
                sev = a.severity.value if hasattr(a.severity, 'value') else a.severity
                typ = a.type.value if hasattr(a.type, 'value') else a.type
                
                summary["by_severity"][sev] = summary["by_severity"].get(sev, 0) + 1
                summary["by_type"][typ] = summary["by_type"].get(typ, 0) + 1
                
        return make_response(
            data=summary,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to aggregate anomaly summary: {str(e)}")
        raise ValidationError(message=f"Failed to aggregate anomaly summary: {str(e)}")


@router.post("/{sensor_id}/analyze", response_model=StandardResponse, summary="On-demand Analysis", description="Trigger on-demand analysis, run all engines on buffered history.")
async def analyze_anomalies(sensor_id: str = Path(..., description="Sensor ID")):
    try:
        recent_readings = await _buffer.get_recent(sensor_id, limit=100)
        if not recent_readings:
            raise NotFoundError(message=f"No recent readings found for sensor {sensor_id}")
        
        all_anomalies = []
        for reading in recent_readings:
            anomalies = await _engine_registry.analyze_reading(reading, buffer=_buffer)
            if anomalies:
                all_anomalies.extend(anomalies)
                if sensor_id not in _anomaly_store:
                    _anomaly_store[sensor_id] = []
                _anomaly_store[sensor_id].extend(anomalies)
                
        return make_response(
            data={
                "sensor_id": sensor_id,
                "readings_analyzed": len(recent_readings),
                "anomalies_detected": len(all_anomalies)
            },
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except NotFoundError:
        raise
    except Exception as e:
        log.error(f"Failed to run analysis for sensor {sensor_id}: {str(e)}")
        raise ValidationError(message=f"Analysis failed: {str(e)}")
