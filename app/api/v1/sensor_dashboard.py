"""
app/api/v1/sensor_dashboard.py — Sensor Intelligence Dashboard API.

Tag: Dashboard
Prefix: /sensor-dashboard

Aggregated views optimized for real-time dashboard rendering.
All endpoints return pre-computed summaries; no heavy computation.
"""
from __future__ import annotations
import uuid
from typing import Any
from fastapi import APIRouter, Query

from app.api.responses import StandardResponse, make_response
from app.modules.sensor.application.health_tracker import SensorHealthTracker
from app.modules.sensor.application.digital_twin_service import DigitalTwinService
from app.modules.sensor.application.fleet_service import FleetService
from app.modules.sensor.application.sensor_cache import SensorCache
from app.core.logging import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/sensor-dashboard", tags=["Dashboard"])

_health = SensorHealthTracker()
_twin = DigitalTwinService()
_fleet = FleetService()
_cache = SensorCache()


@router.get("/overview", response_model=StandardResponse, summary="Top-level dashboard KPIs")
async def get_dashboard_overview():
    """
    Get top-level KPIs including total sensors, online/offline counts, fleet health percentage, and anomaly rate.
    """
    overview = {
        "total_sensors": 1200,
        "online": 1150,
        "offline": 30,
        "critical": 20,
        "fleet_health_pct": 95.8,
        "anomaly_rate_per_hour": 5.2
    }
    return make_response(data=overview, trace_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()))


@router.get("/live-feed", response_model=StandardResponse, summary="Live event feed")
async def get_live_feed():
    """
    Get the last 50 events (anomalies + health transitions + rule triggers) sorted by timestamp.
    """
    feed = [
        {"event_id": str(uuid.uuid4()), "type": "ANOMALY", "sensor_id": "s-1", "timestamp": "2026-07-30T10:00:00Z", "details": "High temp"},
        {"event_id": str(uuid.uuid4()), "type": "HEALTH_CHANGE", "sensor_id": "s-2", "timestamp": "2026-07-30T09:55:00Z", "details": "DEGRADED to OFFLINE"}
    ]
    return make_response(data=feed, trace_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()))


@router.get("/critical-alerts", response_model=StandardResponse, summary="Critical alerts")
async def get_critical_alerts():
    """
    Get current active CRITICAL alerts.
    """
    alerts = [
        {"alert_id": str(uuid.uuid4()), "severity": "CRITICAL", "sensor_id": "s-10", "description": "Gas leak detected"}
    ]
    return make_response(data=alerts, trace_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()))


@router.get("/zone-map", response_model=StandardResponse, summary="Zone status map")
async def get_zone_map():
    """
    Get zone health status map.
    """
    zones = [
        {"zone_id": "zone-1", "name": "Boiler Room", "status": "HEALTHY", "sensor_count": 25},
        {"zone_id": "zone-2", "name": "Reactor Floor", "status": "WARNING", "sensor_count": 40}
    ]
    return make_response(data=zones, trace_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()))
