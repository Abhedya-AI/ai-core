"""
app/api/v1/sensor_health.py — Sensor Health Management API.

Tag: Health
Prefix: /sensor-health
"""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Path, Query

from app.api.responses import StandardResponse, make_response
from app.api.exceptions import NotFoundError, ValidationError
from app.modules.sensor.application.health_tracker import SensorHealthTracker
from app.modules.sensor.domain.models import SensorHealth, SensorHealthState
from app.core.logging import get_logger

log = get_logger("api.v1.sensor_health")

router = APIRouter(prefix="/sensor-health", tags=["Health"])

_health_tracker = SensorHealthTracker()

@router.get("", response_model=StandardResponse, summary="List Sensor Health", description="List health states of all tracked sensors.")
async def list_sensor_health(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=1000, description="Max results")
):
    try:
        states = _health_tracker.get_all_states()
        start = (page - 1) * limit
        paginated = states[start:start+limit]
        
        return make_response(
            data=[s.model_dump() if hasattr(s, 'model_dump') else s for s in paginated],
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to list sensor health: {str(e)}")
        raise ValidationError(message=f"Failed to list health states: {str(e)}")

@router.get("/fleet/summary", response_model=StandardResponse, summary="Fleet Health Summary", description="Get fleet-wide counts of sensors by health status.")
async def get_fleet_summary():
    try:
        summary = _health_tracker.get_fleet_summary()
        return make_response(
            data=summary,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to get fleet health summary: {str(e)}")
        raise ValidationError(message=f"Failed to get fleet summary: {str(e)}")

@router.get("/at-risk", response_model=StandardResponse, summary="At-Risk Sensors", description="List sensors with WARNING or CRITICAL status.")
async def get_at_risk_sensors():
    try:
        at_risk = _health_tracker.get_at_risk_sensors()
        return make_response(
            data=[s.model_dump() if hasattr(s, 'model_dump') else s for s in at_risk],
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to get at-risk sensors: {str(e)}")
        raise ValidationError(message=f"Failed to get at-risk sensors: {str(e)}")

@router.get("/{sensor_id}", response_model=StandardResponse, summary="Get Sensor Health", description="Get health state for a specific sensor.")
async def get_sensor_health(sensor_id: str = Path(..., description="Sensor ID")):
    try:
        state = _health_tracker.get_health(sensor_id)
        if not state:
            state = SensorHealthState(sensor_id=sensor_id)
            
        return make_response(
            data=state.model_dump() if hasattr(state, 'model_dump') else state,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to get health for sensor {sensor_id}: {str(e)}")
        raise ValidationError(message=f"Failed to get health state: {str(e)}")

@router.post("/{sensor_id}/mark-offline", response_model=StandardResponse, summary="Mark Sensor Offline", description="Force a sensor into OFFLINE state.")
async def mark_offline(sensor_id: str = Path(..., description="Sensor ID")):
    try:
        state = _health_tracker.mark_offline(sensor_id)
        return make_response(
            data=state.model_dump() if hasattr(state, 'model_dump') else state,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to mark sensor {sensor_id} offline: {str(e)}")
        raise ValidationError(message=f"Failed to update state: {str(e)}")

@router.post("/{sensor_id}/mark-calibrating", response_model=StandardResponse, summary="Mark Sensor Calibrating", description="Mark a sensor as CALIBRATING.")
async def mark_calibrating(sensor_id: str = Path(..., description="Sensor ID")):
    try:
        state = _health_tracker.mark_calibrating(sensor_id)
        return make_response(
            data=state.model_dump() if hasattr(state, 'model_dump') else state,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to mark sensor {sensor_id} calibrating: {str(e)}")
        raise ValidationError(message=f"Failed to update state: {str(e)}")
