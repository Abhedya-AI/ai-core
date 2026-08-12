"""
app/api/v1/vision_frame_history.py — Frame History endpoints.
"""
from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from fastapi import status as http_status
from app.core.logging import get_logger
from app.modules.vision.infrastructure.repositories.in_memory_frame_repository import InMemoryFrameRepository

log = get_logger("vision.api.frame_history")

router = APIRouter(prefix="/frame-history", tags=["Vision — Frame History"])

_frame_repo = InMemoryFrameRepository()


def get_frame_repo() -> InMemoryFrameRepository:
    return _frame_repo


@router.get(
    "/stats",
    summary="Frame storage statistics",
    operation_id="get_frame_stats",
)
async def get_frame_stats(
    repo: InMemoryFrameRepository = Depends(get_frame_repo),
) -> dict:
    """Aggregate statistics about stored frames."""
    frames = list(repo._frames.values())
    return {
        "total_frames": len(frames),
        "cameras_count": len({f.camera_id for f in frames}),
        "key_frame_count": sum(1 for f in frames if f.is_key_frame),
        "avg_size_bytes": int(sum(f.size_bytes for f in frames) / max(len(frames), 1)),
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
    }


@router.get(
    "",
    summary="List frames",
    operation_id="list_frames",
)
async def list_frames(
    camera_id: str | None = Query(None),
    is_key_frame: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    repo: InMemoryFrameRepository = Depends(get_frame_repo),
) -> dict:
    """List stored video frames."""
    frames = list(repo._frames.values())
    if camera_id:
        frames = [f for f in frames if f.camera_id == camera_id]
    if is_key_frame is not None:
        frames = [f for f in frames if f.is_key_frame == is_key_frame]
    frames.sort(key=lambda f: f.captured_at, reverse=True)
    paged = frames[offset: offset + limit]
    return {"total": len(frames), "limit": limit, "offset": offset, "frames": [f.model_dump() for f in paged]}


@router.get(
    "/{frame_id}/metadata",
    summary="Get frame metadata",
    operation_id="get_frame_metadata",
)
async def get_frame_metadata(
    frame_id: str = Path(...),
    repo: InMemoryFrameRepository = Depends(get_frame_repo),
) -> dict:
    """Get rich metadata for a specific frame."""
    meta = await repo.get_metadata(frame_id)
    if not meta:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=f"Frame metadata '{frame_id}' not found.")
    return meta.model_dump()


@router.get(
    "/{frame_id}",
    summary="Get frame",
    operation_id="get_frame",
)
async def get_frame(
    frame_id: str = Path(...),
    repo: InMemoryFrameRepository = Depends(get_frame_repo),
) -> dict:
    """Get a stored frame by ID."""
    frame = await repo.get_frame(frame_id)
    if not frame:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=f"Frame '{frame_id}' not found.")
    return frame.model_dump()
