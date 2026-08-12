"""
app/api/v1/sensor_analytics.py — Sensor Analytics API.

Tag: Analytics
Prefix: /analytics
"""
from __future__ import annotations
import uuid
from typing import Optional
from fastapi import APIRouter, Query, Path

from app.api.responses import StandardResponse, make_response
from app.api.exceptions import NotFoundError, ValidationError
from app.modules.sensor.application.analytics_service import SensorAnalyticsService
from app.modules.sensor.application.telemetry_buffer import TelemetryBuffer
from app.modules.sensor.application.health_tracker import SensorHealthTracker
from app.core.logging import get_logger

log = get_logger("api.v1.sensor_analytics")

router = APIRouter(prefix="/analytics", tags=["Analytics"])

_buffer = TelemetryBuffer()
_health_tracker = SensorHealthTracker()
_analytics = SensorAnalyticsService(buffer=_buffer, health_tracker=_health_tracker)

@router.get("/{sensor_id}/moving-averages", response_model=StandardResponse, summary="Get Moving Averages", description="Retrieve moving average for a sensor.")
async def get_moving_averages(
    sensor_id: str = Path(..., description="Sensor ID"),
    window: int = Query(20, ge=2, description="Window size for moving average")
):
    try:
        values = _buffer.get_values(sensor_id)
        result = _analytics.calculate_moving_averages(sensor_id, values, window=window)
        return make_response(
            data=result.model_dump() if hasattr(result, 'model_dump') else result,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to calculate moving averages for {sensor_id}: {str(e)}")
        raise ValidationError(message=f"Calculation failed: {str(e)}")

@router.get("/{sensor_id}/trend", response_model=StandardResponse, summary="Get Trend Analysis", description="Retrieve trend analysis for a sensor.")
async def get_trend(sensor_id: str = Path(..., description="Sensor ID")):
    try:
        values = _buffer.get_values(sensor_id)
        result = _analytics.analyze_trend(sensor_id, values)
        return make_response(
            data=result.model_dump() if hasattr(result, 'model_dump') else result,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to analyze trend for {sensor_id}: {str(e)}")
        raise ValidationError(message=f"Analysis failed: {str(e)}")

@router.get("/{sensor_id}/peaks", response_model=StandardResponse, summary="Get Peaks", description="Retrieve peak records for a sensor.")
async def get_peaks(sensor_id: str = Path(..., description="Sensor ID")):
    try:
        values = _buffer.get_values(sensor_id)
        result = _analytics.detect_peaks(sensor_id, values)
        return make_response(
            data=result.model_dump() if hasattr(result, 'model_dump') else result,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to find peaks for {sensor_id}: {str(e)}")
        raise ValidationError(message=f"Failed to find peaks: {str(e)}")

@router.get("/{sensor_id}/uptime", response_model=StandardResponse, summary="Get Uptime Stats", description="Retrieve uptime statistics for a sensor.")
async def get_uptime(sensor_id: str = Path(..., description="Sensor ID")):
    try:
        readings = _buffer.get_recent(sensor_id)
        result = _analytics.calculate_uptime(sensor_id, readings)
        return make_response(
            data=result.model_dump() if hasattr(result, 'model_dump') else result,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to calculate uptime for {sensor_id}: {str(e)}")
        raise ValidationError(message=f"Calculation failed: {str(e)}")

@router.get("/{sensor_id}/failure-probability", response_model=StandardResponse, summary="Get Failure Probability", description="Calculate failure probability for a sensor.")
async def get_failure_probability(sensor_id: str = Path(..., description="Sensor ID")):
    try:
        health = _health_tracker.get_health(sensor_id)
        values = _buffer.get_values(sensor_id)
        trend = _analytics.analyze_trend(sensor_id, values)
        result = _analytics.estimate_failure_probability(sensor_id, health_state=health, trend=trend)
        return make_response(
            data=result.model_dump() if hasattr(result, 'model_dump') else result,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to predict failure for {sensor_id}: {str(e)}")
        raise ValidationError(message=f"Prediction failed: {str(e)}")

@router.get("/{sensor_id}/report", response_model=StandardResponse, summary="Get Full Analytics Report", description="Retrieve a full analytics report for a sensor.")
async def get_report(
    sensor_id: str = Path(..., description="Sensor ID"),
    period_hours: int = Query(24, ge=1, description="Period in hours")
):
    try:
        readings = _buffer.get_recent(sensor_id)
        health = _health_tracker.get_health(sensor_id)
        result = _analytics.generate_report(sensor_id, readings=readings, health_state=health)
        return make_response(
            data=result.model_dump() if hasattr(result, 'model_dump') else result,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to generate report for {sensor_id}: {str(e)}")
        raise ValidationError(message=f"Report generation failed: {str(e)}")

@router.get("/fleet/summary", response_model=StandardResponse, summary="Get Fleet Summary", description="Retrieve a summary across all sensors in buffer.")
async def get_fleet_summary():
    try:
        sensor_ids = _buffer.get_all_sensor_ids()
        summary = {
            "total_sensors_in_buffer": len(sensor_ids),
            "sensor_ids": sensor_ids
        }
        return make_response(
            data=summary,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to generate fleet summary: {str(e)}")
        raise ValidationError(message=f"Summary generation failed: {str(e)}")
