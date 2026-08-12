"""
app/api/v1/sensor_alerts.py — Sensor Alert Management API.

Tag: Alerts  
Prefix: /alerts
"""
from __future__ import annotations
import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Query, Path
from pydantic import BaseModel, Field

from app.api.responses import StandardResponse, PaginatedResponse, make_response, ResponseMetadata, PaginationMeta
from app.api.exceptions import NotFoundError, ValidationError
from app.modules.sensor.domain.models import AnomalySeverity
from app.core.logging import get_logger

log = get_logger("api.v1.sensor_alerts")

router = APIRouter(prefix="/alerts", tags=["Alerts"])

_alerts: list[dict] = []

@router.get("", response_model=PaginatedResponse, summary="List Alerts", description="List alerts with optional filtering.")
async def list_alerts(
    severity: Optional[AnomalySeverity] = Query(None, description="Filter by severity"),
    sensor_id: Optional[str] = Query(None, description="Filter by sensor ID"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgement status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=1000, description="Max results")
):
    try:
        filtered = _alerts
        if severity:
            filtered = [a for a in filtered if a.get("severity") == severity]
        if sensor_id:
            filtered = [a for a in filtered if a.get("sensor_id") == sensor_id]
        if acknowledged is not None:
            filtered = [a for a in filtered if a.get("acknowledged", False) == acknowledged]
            
        filtered = sorted(filtered, key=lambda x: x.get("timestamp", 0), reverse=True)
        
        start = (page - 1) * limit
        paginated = filtered[start:start+limit]
        
        return make_response(
            data=paginated,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to list alerts: {str(e)}")
        raise ValidationError(message=f"Failed to list alerts: {str(e)}")

@router.get("/active", response_model=StandardResponse, summary="Get Active Alerts", description="Get all unacknowledged alerts.")
async def get_active_alerts():
    try:
        active = [a for a in _alerts if not a.get("acknowledged", False)]
        active = sorted(active, key=lambda x: x.get("timestamp", 0), reverse=True)
        return make_response(
            data=active,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to get active alerts: {str(e)}")
        raise ValidationError(message=f"Failed to get active alerts: {str(e)}")

@router.get("/critical", response_model=StandardResponse, summary="Get Critical Alerts", description="Get only CRITICAL alerts.")
async def get_critical_alerts():
    try:
        critical = [a for a in _alerts if a.get("severity") == AnomalySeverity.CRITICAL]
        critical = sorted(critical, key=lambda x: x.get("timestamp", 0), reverse=True)
        return make_response(
            data=critical,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to get critical alerts: {str(e)}")
        raise ValidationError(message=f"Failed to get critical alerts: {str(e)}")

@router.get("/{alert_id}", response_model=StandardResponse, summary="Get Alert Details", description="Get details of a specific alert by ID.")
async def get_alert(alert_id: str = Path(..., description="Alert ID")):
    alert = next((a for a in _alerts if a.get("id") == alert_id), None)
    if not alert:
        raise NotFoundError(message=f"Alert {alert_id} not found")
        
    return make_response(
        data=alert,
        trace_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4())
    )

@router.post("/{alert_id}/acknowledge", response_model=StandardResponse, summary="Acknowledge Alert", description="Acknowledge an alert.")
async def acknowledge_alert(alert_id: str = Path(..., description="Alert ID")):
    alert = next((a for a in _alerts if a.get("id") == alert_id), None)
    if not alert:
        raise NotFoundError(message=f"Alert {alert_id} not found")
        
    try:
        alert["acknowledged"] = True
        alert["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
        
        return make_response(
            data=alert,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to acknowledge alert {alert_id}: {str(e)}")
        raise ValidationError(message=f"Failed to acknowledge alert: {str(e)}")
