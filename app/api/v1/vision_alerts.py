"""
app/api/v1/vision_alerts.py — Camera Health and Vision Alerts endpoints.
"""
from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, Path, HTTPException, Body
from fastapi import status as http_status
from pydantic import BaseModel
from app.core.logging import get_logger
from app.modules.vision.infrastructure.repositories.in_memory_alert_repository import InMemoryAlertRepository
from app.modules.vision.infrastructure.repositories.in_memory_camera_repository import InMemoryCameraRepository
from app.modules.vision.domain.entities.camera_health import CameraHealth
from app.modules.vision.domain.enums.camera_status import CameraStatus

log = get_logger("vision.api.alerts")

router = APIRouter(tags=["Vision — Alerts & Health"])

_alert_repo = InMemoryAlertRepository()
_camera_repo_for_alerts = InMemoryCameraRepository()


class AcknowledgeBody(BaseModel):
    acknowledged_by: str


class ResolveBody(BaseModel):
    resolved_by: str


@router.get("/camera-health", summary="List camera health", operation_id="list_camera_health")
async def list_camera_health(
    status: str | None = Query(None),
    zone_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    cameras = await _camera_repo_for_alerts.list_cameras(zone_id=zone_id, status=status, limit=limit, offset=offset)
    health_list = []
    for cam in cameras:
        h = await _camera_repo_for_alerts.get_health(cam.id)
        if h:
            health_list.append(h.model_dump())
        else:
            health_list.append(CameraHealth(camera_id=cam.id, status=cam.health_status).model_dump())
    return {"total": len(health_list), "health": health_list}


@router.get("/camera-health/{camera_id}", summary="Get camera health", operation_id="get_camera_health_detail")
async def get_camera_health(
    camera_id: str = Path(...),
) -> dict:
    h = await _camera_repo_for_alerts.get_health(camera_id)
    if not h:
        cam = await _camera_repo_for_alerts.get_camera(camera_id)
        if not cam:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=f"Camera '{camera_id}' not found.")
        return CameraHealth(camera_id=camera_id, status=cam.health_status).model_dump()
    return h.model_dump()


@router.get("/vision-alerts/stats", summary="Alert statistics", operation_id="get_vision_alert_stats")
async def get_alert_stats() -> dict:
    all_alerts = await _alert_repo.list_alerts(limit=10000)
    active = [a for a in all_alerts if a.is_active]
    critical = [a for a in active if a.is_critical]
    high = [a for a in active if a.severity.value == "HIGH"]
    return {
        "total_active": len(active),
        "critical_count": len(critical),
        "high_count": len(high),
        "zones_affected": len({a.zone_id for a in active if a.zone_id}),
        "cameras_affected": len({a.camera_id for a in active}),
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
    }


@router.get("/vision-alerts", summary="List vision alerts", operation_id="list_vision_alerts")
async def list_alerts(
    zone_id: str | None = Query(None),
    severity: str | None = Query(None),
    status: str | None = Query(None),
    camera_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    alerts = await _alert_repo.list_alerts(zone_id=zone_id, severity=severity, status=status, camera_id=camera_id, limit=limit, offset=offset)
    return {"total": len(alerts), "limit": limit, "offset": offset, "alerts": [a.model_dump() for a in alerts]}


@router.get("/vision-alerts/{alert_id}", summary="Get vision alert", operation_id="get_vision_alert")
async def get_alert(alert_id: str = Path(...)) -> dict:
    alert = await _alert_repo.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=f"Alert '{alert_id}' not found.")
    return alert.model_dump()


@router.post("/vision-alerts/{alert_id}/acknowledge", summary="Acknowledge alert", operation_id="acknowledge_alert")
async def acknowledge_alert(alert_id: str = Path(...), body: AcknowledgeBody = ...) -> dict:
    alert = await _alert_repo.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=f"Alert '{alert_id}' not found.")
    updated = alert.acknowledge(body.acknowledged_by)
    await _alert_repo.update_alert(updated)
    return updated.model_dump()


@router.post("/vision-alerts/{alert_id}/resolve", summary="Resolve alert", operation_id="resolve_alert")
async def resolve_alert(alert_id: str = Path(...), body: ResolveBody = ...) -> dict:
    alert = await _alert_repo.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=f"Alert '{alert_id}' not found.")
    updated = alert.resolve(body.resolved_by)
    await _alert_repo.update_alert(updated)
    return updated.model_dump()
