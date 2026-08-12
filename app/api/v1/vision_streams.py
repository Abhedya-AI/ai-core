"""
app/api/v1/vision_streams.py

Vision Intelligence - Video Streams API.
"""
from fastapi import APIRouter, Path
from datetime import datetime, timezone
import uuid

from app.core.logging import get_logger

log = get_logger("api.v1.vision_streams")

router = APIRouter(prefix="/video-streams", tags=["Vision — Video Streams"])

_active_streams: dict[str, dict] = {}

@router.post("/{camera_id}/start")
async def start_stream(camera_id: str = Path(...)):
    """Start processing a video stream."""
    stream_id = str(uuid.uuid4())
    st = {
        "camera_id": camera_id,
        "stream_id": stream_id,
        "status": "STREAMING",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "recording": False
    }
    _active_streams[camera_id] = st
    return {"camera_id": camera_id, "stream_id": stream_id, "status": "STREAMING", "message": "Stream started", "started_at": st["started_at"]}

@router.delete("/{camera_id}/stop")
async def stop_stream(camera_id: str = Path(...)):
    """Stop processing a video stream."""
    if camera_id in _active_streams:
        del _active_streams[camera_id]
    return {"camera_id": camera_id, "status": "STOPPED", "message": "Stream stopped", "stopped_at": datetime.now(timezone.utc).isoformat()}

@router.get("")
async def list_streams():
    """List all active video streams."""
    return list(_active_streams.values())

@router.get("/{camera_id}/status")
async def stream_status(camera_id: str = Path(...)):
    """Get the status of a video stream."""
    if camera_id not in _active_streams:
        return {"camera_id": camera_id, "status": "STOPPED"}
    return _active_streams[camera_id]

@router.post("/{camera_id}/record/start")
async def start_recording(camera_id: str = Path(...)):
    """Start recording a stream."""
    if camera_id in _active_streams:
        _active_streams[camera_id]["recording"] = True
    return {"camera_id": camera_id, "recording": True, "segment_duration_s": 300, "message": "Recording started"}

@router.post("/{camera_id}/record/stop")
async def stop_recording(camera_id: str = Path(...)):
    """Stop recording a stream."""
    if camera_id in _active_streams:
        _active_streams[camera_id]["recording"] = False
    return {"camera_id": camera_id, "recording": False, "message": "Recording stopped"}
