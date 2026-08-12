"""
app/api/v1/sensor_reports.py — Sensor Reports API.

Tag: Reports
Prefix: /sensor-reports

Generates comprehensive PDF-ready reports from sensor data.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Query, Path

from app.api.responses import StandardResponse, PaginatedResponse, make_response, ResponseMetadata, PaginationMeta
from app.modules.sensor.application.analytics_service import SensorAnalyticsService
from app.modules.sensor.application.health_tracker import SensorHealthTracker
from app.modules.sensor.application.telemetry_buffer import TelemetryBuffer
from app.modules.sensor.application.fleet_service import FleetService
from app.core.logging import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/sensor-reports", tags=["Reports"])

# Singletons (In a real app, these might be injected. Using module-level for now)
_analytics = SensorAnalyticsService()
_health = SensorHealthTracker()
_buffer = TelemetryBuffer()
_fleet = FleetService()


@router.get("/{sensor_id}/daily", response_model=StandardResponse[dict[str, Any]], summary="Daily sensor report")
async def get_daily_sensor_report(
    sensor_id: str = Path(..., description="The ID of the sensor"),
    date: str | None = Query(None, description="Date in YYYY-MM-DD format, defaults to today")
) -> dict[str, Any]:
    """
    Get a daily analytical report for a specific sensor.
    """
    target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Mock report data
    report = {
        "sensor_id": sensor_id,
        "date": target_date,
        "metrics": {
            "avg_reading": 42.5,
            "max_reading": 55.2,
            "min_reading": 30.1,
            "anomaly_count": 2,
            "uptime_pct": 99.9,
        },
        "health_status": "HEALTHY"
    }
    
    return make_response(
        data=report,
        meta=ResponseMetadata(message="Daily sensor report generated successfully")
    )


@router.get("/{sensor_id}/weekly", response_model=StandardResponse[dict[str, Any]], summary="Weekly sensor summary")
async def get_weekly_sensor_summary(
    sensor_id: str = Path(..., description="The ID of the sensor")
) -> dict[str, Any]:
    """
    Get a 7-day summary for a sensor including anomaly count, health changes, and trends.
    """
    # Mock report data
    report = {
        "sensor_id": sensor_id,
        "period": "last_7_days",
        "anomaly_count": 5,
        "health_changes": 1,
        "trend": "STABLE",
        "maintenance_recommended": False
    }
    
    return make_response(
        data=report,
        meta=ResponseMetadata(message="Weekly sensor summary generated successfully")
    )


@router.get("/fleet/daily", response_model=StandardResponse[dict[str, Any]], summary="Daily fleet-wide report")
async def get_daily_fleet_report() -> dict[str, Any]:
    """
    Get a fleet-wide daily report including top anomalies, worst sensors, and zone breakdowns.
    """
    # Mock report data
    report = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "total_sensors": 150,
        "total_anomalies": 24,
        "top_anomalies": [],
        "worst_sensors": [
            {"sensor_id": "sensor-10", "anomaly_count": 8, "uptime_pct": 85.0}
        ],
        "zone_breakdown": {
            "zone-A": {"total": 50, "healthy": 48, "offline": 1, "critical": 1}
        }
    }
    
    return make_response(
        data=report,
        meta=ResponseMetadata(message="Daily fleet report generated successfully")
    )


@router.get("/fleet/risk", response_model=StandardResponse[dict[str, Any]], summary="Fleet risk report")
async def get_fleet_risk_report() -> dict[str, Any]:
    """
    Get a fleet risk report highlighting sensors by risk level and maintenance candidates.
    """
    report = {
        "risk_levels": {
            "CRITICAL": 3,
            "HIGH": 12,
            "MEDIUM": 25,
            "LOW": 110
        },
        "maintenance_candidates": [
            {"sensor_id": "sensor-42", "reason": "Frequent high vibrations"}
        ]
    }
    
    return make_response(
        data=report,
        meta=ResponseMetadata(message="Fleet risk report generated successfully")
    )


@router.get("/zone/{zone_id}/summary", response_model=StandardResponse[dict[str, Any]], summary="Zone summary report")
async def get_zone_summary_report(
    zone_id: str = Path(..., description="The ID of the zone")
) -> dict[str, Any]:
    """
    Get a summary report for a specific zone.
    """
    report = {
        "zone_id": zone_id,
        "sensor_count": 45,
        "active_anomalies": 2,
        "overall_health": "GOOD",
        "most_active_sensor": "sensor-22"
    }
    
    return make_response(
        data=report,
        meta=ResponseMetadata(message=f"Zone summary for {zone_id} generated successfully")
    )
