"""
api/routes.py — FastAPI router for the Vision Intelligence module.

Endpoints
─────────
POST /api/v1/vision/analyze          Analyse a single frame
GET  /api/v1/vision/events           List filtered events (paginated)
GET  /api/v1/vision/events/{id}      Retrieve a single event by UUID
GET  /api/v1/vision/health           Module health check

Design
──────
• Routes are thin — they validate input, build use-cases, call execute,
  and serialise the response.  No business logic.
• Dependencies (session, detector) are injected via FastAPI Depends.
• The real detector is the StubDetector in Milestone 1.  Replace the
  `get_detector` dependency with `YOLODetector` in Milestone 2.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.infrastructure.postgres.session import get_session
from app.modules.vision.application.analyze_frame import AnalyzeFrameUseCase
from app.modules.vision.domain.enums import HazardType, RiskLevel
from app.modules.vision.infrastructure.detector import BaseDetector, StubDetector
from app.modules.vision.infrastructure.postgres_repository import (
    PostgresVisionRepository,
)
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
    """
    Return the active vision detector.

    Milestone 1: StubDetector (no model loaded).
    Milestone 2: Replace with YOLODetector(...).
    """
    return StubDetector()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=AnalyzeFrameResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Analyse a frame for safety hazards",
    description=(
        "Upload an image frame. The vision pipeline will detect safety-related "
        "objects, calculate a risk score, persist the results, and publish a "
        "typed event for downstream modules."
    ),
    response_description="Full analysis result including detections, hazards, and risk score.",
)
async def analyze_frame(
    # ── Image upload ──────────────────────────────────────────────────────────
    image: UploadFile = File(
        ...,
        description="Image file (JPEG, PNG, WebP). Max 20 MB.",
    ),
    # ── Metadata (sent as form fields alongside the file) ─────────────────────
    camera_id:      str   = Form(...,  description="Source camera identifier."),
    frame_id:       str | None = Form(None,   description="Optional frame identifier."),
    location:       str | None = Form(None,   description="Optional location string."),
    min_confidence: float = Form(0.4,  ge=0.0, le=1.0, description="Min confidence threshold."),
    save_image:     bool  = Form(True, description="Persist the frame image."),
    # ── Dependencies ──────────────────────────────────────────────────────────
    session:  AsyncSession = Depends(get_session),
    detector: BaseDetector = Depends(get_detector),
) -> AnalyzeFrameResponse:
    """Analyse an uploaded frame for safety hazards."""

    # Read and validate image
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

    # Build request object
    request = AnalyzeFrameRequest(
        camera_id=camera_id,
        frame_id=frame_id,
        location=location,
        min_confidence=min_confidence,
        save_image=save_image,
    )

    # Build use-case and execute
    use_case = AnalyzeFrameUseCase(
        detector=detector,
        repository=PostgresVisionRepository(session),
    )

    try:
        event = await use_case.execute(image_bytes, request)
    except Exception as exc:
        log.error(f"AnalyzeFrameUseCase failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Frame analysis failed. See server logs.",
        ) from exc

    return AnalyzeFrameResponse(
        success=True,
        message="Frame analysed successfully.",
        event=serialize_vision_event(event),
    )


@router.get(
    "/events",
    response_model=ListEventsResponse,
    summary="List vision events",
    description="Return a paginated, filtered list of VisionEvents.",
)
async def list_events(
    camera_id:   str | None  = Query(None, description="Filter by camera ID."),
    min_risk:    str | None  = Query(None, description="Minimum risk level: LOW|MEDIUM|HIGH|CRITICAL."),
    hazard_type: str | None  = Query(None, description="Filter by hazard type."),
    since:       str | None  = Query(None, description="ISO-8601 start timestamp."),
    until:       str | None  = Query(None, description="ISO-8601 end timestamp."),
    limit:       int         = Query(50, ge=1, le=200),
    offset:      int         = Query(0,  ge=0),
    session:     AsyncSession = Depends(get_session),
) -> ListEventsResponse:
    """List vision events with optional filters."""

    # Validate enum parameters
    parsed_risk = None
    if min_risk:
        try:
            parsed_risk = RiskLevel(min_risk.upper())
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid risk level '{min_risk}'. Valid: LOW, MEDIUM, HIGH, CRITICAL.",
            )

    parsed_hazard = None
    if hazard_type:
        try:
            parsed_hazard = HazardType(hazard_type.upper())
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid hazard type '{hazard_type}'.",
            )

    # Parse timestamps
    parsed_since = _parse_dt(since, "since") if since else None
    parsed_until = _parse_dt(until, "until") if until else None

    repo = PostgresVisionRepository(session)
    events = await repo.list_events(
        camera_id=camera_id,
        min_risk=parsed_risk,
        hazard_type=parsed_hazard,
        since=parsed_since,
        until=parsed_until,
        limit=limit,
        offset=offset,
    )

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
    event = await repo.get_event(event_id)

    if event is None:
        return GetEventResponse(event=None)

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
        "milestone": 1,
        "detector": "stub",
        "description": "Domain, schemas, and pipeline wired. YOLO not yet loaded.",
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_dt(value: str, param_name: str) -> datetime:
    """Parse an ISO-8601 string to datetime or raise HTTP 422."""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ISO-8601 datetime for '{param_name}': {value}",
        )
