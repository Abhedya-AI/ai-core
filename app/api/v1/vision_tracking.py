"""
app/api/v1/vision_tracking.py

Vision Intelligence - Tracking API.
"""
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from typing import Any

from app.core.logging import get_logger
from app.modules.vision.infrastructure.repositories.in_memory_tracking_repository import InMemoryTrackingRepository

log = get_logger("api.v1.vision_tracking")

router = APIRouter(prefix="/tracking", tags=["Vision — Tracking"])

_tracking_repo_instance = InMemoryTrackingRepository()

def get_tracking_repo() -> InMemoryTrackingRepository:
    return _tracking_repo_instance

@router.get("")
async def list_active_tracks(
    camera_id: str | None = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
    repo: InMemoryTrackingRepository = Depends(get_tracking_repo)
):
    """List active object tracks."""
    tracks = await repo.list_active_tracks(camera_id)
    return tracks[offset:offset+limit]

@router.get("/stats")
async def get_tracking_stats(repo: InMemoryTrackingRepository = Depends(get_tracking_repo)):
    """Get overall tracking statistics."""
    active = await repo.list_active_tracks()
    return {
        "active_track_count": len(active),
        "total_sessions": len(repo._tracks) + len(repo._history),
        "avg_duration_seconds": 0.0,
        "zone_crossings_count": sum(len(t.zone_crossings) for t in active),
        "cameras_with_active_tracks": len({t.camera_id for t in active})
    }

@router.get("/{track_id}/history")
async def get_track_history(track_id: str = Path(...), repo: InMemoryTrackingRepository = Depends(get_tracking_repo)):
    """Get historical path and events for a track."""
    h = await repo.get_history(track_id)
    if not h:
        raise HTTPException(status_code=404, detail="Tracking history not found")
    return h

@router.get("/{track_id}")
async def get_track(track_id: str = Path(...), repo: InMemoryTrackingRepository = Depends(get_tracking_repo)):
    """Get details of a specific track."""
    t = await repo.get_track(track_id)
    if not t:
        raise HTTPException(status_code=404, detail="Track not found")
    return t
