"""
api/routes.py — FastAPI router for the Vision Intelligence module.
"""

from __future__ import annotations

from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.infrastructure.postgres.session import get_session
from app.modules.vision.application.analyze_frame import AnalyzeFrameUseCase
from app.modules.vision.domain.entities import Detection, VisionEvent
from app.modules.vision.domain.enums import HazardType, RiskLevel
from app.modules.vision.infrastructure.detector import BaseDetector, StubDetector
from app.modules.vision.infrastructure.postgres_repository import (
    PostgresVisionRepository,
)
from app.modules.vision.infrastructure.mapper import parse_camera_id
from app.modules.vision.schemas.request import AnalyzeFrameRequest
from app.modules.vision.schemas.response import (
    AnalyzeFrameResponse,
    GetEventResponse,
    ListEventsResponse,
)
from app.modules.vision.api.serializers import (
    serialize_vision_event,
)

log = get_logger("vision.api")

router = APIRouter(
    prefix="/vision",
    tags=["Vision Intelligence"],
)


# ── Dependency providers ──────────────────────────────────────────────────────

def get_detector() -> BaseDetector:
    """Return the active vision detector."""
    return StubDetector()


def _detection_to_event(det: Detection) -> VisionEvent:
    """Convert a domain Detection back to a VisionEvent for API responses."""
    event_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"event-{det.id}")
    return VisionEvent(
        event_id=event_id,
        detection_id=det.id,
        camera_id=det.camera_id,
        hazard_type=det.hazard_type,
        risk_level=det.risk.level,
        confidence=det.confidence,
        occurred_at=det.detected_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=AnalyzeFrameResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Analyse a frame for safety hazards",
)
async def analyze_frame(
    image: UploadFile = File(..., description="Image file (JPEG, PNG, WebP). Max 20 MB."),
    camera_id:      str   = Form(...,  description="Source camera identifier."),
    frame_id:       str | None = Form(None,   description="Optional frame identifier."),
    location:       str | None = Form(None,   description="Optional location string."),
    min_confidence: float = Form(0.4,  ge=0.0, le=1.0, description="Min confidence threshold."),
    save_image:     bool  = Form(True, description="Persist the frame image."),
    session:  AsyncSession = Depends(get_session),
    detector: BaseDetector = Depends(get_detector),
) -> AnalyzeFrameResponse:
    """Analyse an uploaded frame for safety hazards."""

    image_bytes = await image.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=http_status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image exceeds 20 MB limit.",
        )
    if not image_bytes:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    request = AnalyzeFrameRequest(
        camera_id=camera_id,
        frame_id=frame_id,
        location=location,
        min_confidence=min_confidence,
        save_image=save_image,
    )

    use_case = AnalyzeFrameUseCase(
        detector=detector,
        repository=PostgresVisionRepository(session),
    )

    try:
        events = await use_case.execute(image_bytes, request)
    except Exception as exc:
        log.error(f"AnalyzeFrameUseCase failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Frame analysis failed. See server logs.",
        ) from exc

    return AnalyzeFrameResponse(
        success=True,
        message="Frame analysed successfully.",
        events=[serialize_vision_event(e) for e in events],
    )


@router.get(
    "/events",
    response_model=ListEventsResponse,
    summary="List vision events",
)
async def list_events(
    camera_id:   str | None  = Query(None, description="Filter by camera ID."),
    hazard_type: str | None  = Query(None, description="Filter by hazard type."),
    limit:       int         = Query(50, ge=1, le=200),
    offset:      int         = Query(0,  ge=0),
    session:     AsyncSession = Depends(get_session),
) -> ListEventsResponse:
    """List vision events with optional filters."""

    parsed_hazard = None
    if hazard_type:
        try:
            parsed_hazard = HazardType(hazard_type.upper())
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid hazard type '{hazard_type}'.",
            )

    repo = PostgresVisionRepository(session)
    
    # Query detections based on filters
    if camera_id:
        camera_uuid = parse_camera_id(camera_id)
        detections = await repo.list_by_camera(camera_uuid)
    elif parsed_hazard:
        detections = await repo.list_by_hazard(parsed_hazard)
    else:
        detections = await repo.list_recent(limit=limit)

    events = [_detection_to_event(d) for d in detections]

    return ListEventsResponse(
        total=len(events),
        limit=limit,
        offset=offset,
        events=[serialize_vision_event(e) for e in events],
    )


@router.get(
    "/events/{event_id}",
    response_model=GetEventResponse,
    summary="Get a vision event by ID",
)
async def get_event(
    event_id: str,
    session:  AsyncSession = Depends(get_session),
) -> GetEventResponse:
    """Retrieve a single VisionEvent by its UUID."""
    repo  = PostgresVisionRepository(session)
    
    try:
        event_uuid = uuid.UUID(event_id)
    except ValueError:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid event UUID format: '{event_id}'",
        )

    # In 1-to-1 model, the event ID can be deterministically linked to a detection.
    # To find it, we can fetch all recent or check by ID. For stub, get_by_id returns None.
    det = await repo.get_by_id(event_uuid)
    if det is None:
        return GetEventResponse(event=None)

    event = _detection_to_event(det)
    return GetEventResponse(event=serialize_vision_event(event))


@router.get(
    "/health",
    summary="Vision module health check",
    tags=["Vision Intelligence"],
)
async def vision_health() -> dict:
    """Return the health status of the Vision module."""
    return {
        "module": "vision",
        "status": "ok",
        "milestone": 1.3,
        "detector": "stub",
        "description": "Clean Architecture Domain Entities and Repository contracts implemented.",
    }
