"""
api/routes.py — FastAPI router for the Vision Intelligence module.

Route responsibilities
──────────────────────
• Parse and validate the HTTP request.
• Call the application layer (VisionOrchestrator / repository).
• Map the result to a response schema.
• Map application exceptions to HTTP status codes.

Routes do NOT:
• Contain business logic.
• Construct domain objects.
• Call infrastructure (DB, Kafka) directly.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.infrastructure.postgres.session import get_session
from app.modules.vision.application.dto.analyze_response import FrameAnalysisResult
from app.modules.vision.application.exceptions import (
    DetectorUnavailableError,
    EventPublishingError,
    FrameReadError,
    PersistenceError,
    RiskCalculationError,
)
from app.modules.vision.application.services.vision_orchestrator import (
    VisionOrchestrator,
)
from app.modules.vision.domain.enums import HazardType
from app.modules.vision.infrastructure.detector import StubDetector
from app.modules.vision.infrastructure.postgres_repository import (
    PostgresVisionRepository,
)
from app.modules.vision.schemas.request import AnalyzeFrameRequest
from app.modules.vision.schemas.response import (
    AnalyzeFrameResponse,
    GetEventResponse,
    ListEventsResponse,
)
from app.modules.vision.api.serializers import serialize_vision_event

log = get_logger("vision.api")

router = APIRouter(
    prefix="/vision",
    tags=["Vision Intelligence"],
)


# ── Dependency providers ──────────────────────────────────────────────────────

def get_orchestrator(
    session: AsyncSession = Depends(get_session),
) -> VisionOrchestrator:
    """
    Provide a VisionOrchestrator backed by the StubDetector.

    In production, swap StubDetector for YOLODetector by changing this
    function (or by wiring through settings.detector_mode).
    """
    return VisionOrchestrator.with_stub(
        repository=PostgresVisionRepository(session),
    )


# ── Exception → HTTP status mapping ──────────────────────────────────────────

_EXCEPTION_MAP: dict[type, tuple[int, str]] = {
    FrameReadError:             (http_status.HTTP_422_UNPROCESSABLE_ENTITY,  "Invalid image."),
    DetectorUnavailableError:   (http_status.HTTP_503_SERVICE_UNAVAILABLE,   "Detector unavailable."),
    RiskCalculationError:       (http_status.HTTP_500_INTERNAL_SERVER_ERROR, "Risk calculation failed."),
    PersistenceError:           (http_status.HTTP_500_INTERNAL_SERVER_ERROR, "Persistence failed."),
}


def _handle_vision_error(exc: Exception) -> None:
    """Re-raise VisionErrors as appropriate HTTPExceptions."""
    for exc_type, (status_code, user_message) in _EXCEPTION_MAP.items():
        if isinstance(exc, exc_type):
            log.error(f"{type(exc).__name__}: {exc}")
            raise HTTPException(status_code=status_code, detail=user_message) from exc
    # Unknown exception — 500
    log.error(f"Unhandled vision error: {exc}", exc_info=True)
    raise HTTPException(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Frame analysis failed. See server logs.",
    ) from exc


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=AnalyzeFrameResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Analyse a frame for safety hazards",
    description=(
        "Upload a camera frame and receive a complete safety analysis "
        "including detected hazards, risk scores, and actionable alerts."
    ),
)
async def analyze_frame(
    image:          UploadFile = File(..., description="Image file (JPEG / PNG / WebP). Max 20 MB."),
    camera_id:      str        = Form(...,  description="Source camera identifier."),
    frame_id:       str | None = Form(None, description="Optional frame identifier."),
    location:       str | None = Form(None, description="Optional location string."),
    min_confidence: float      = Form(0.4,  ge=0.0, le=1.0, description="Min confidence threshold."),
    save_image:     bool       = Form(True, description="Persist the frame image."),
    orchestrator: VisionOrchestrator = Depends(get_orchestrator),
) -> AnalyzeFrameResponse:
    """Analyse an uploaded frame for safety hazards."""

    image_bytes = await image.read()

    if not image_bytes:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=http_status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image exceeds 20 MB limit.",
        )

    request = AnalyzeFrameRequest(
        camera_id=camera_id,
        frame_id=frame_id,
        location=location,
        min_confidence=min_confidence,
        save_image=save_image,
    )

    try:
        result: FrameAnalysisResult = await orchestrator.analyze(image_bytes, request)
    except EventPublishingError:
        # Kafka failure is non-fatal — the event is persisted; just log it.
        log.warning("Kafka publish failed after successful analysis (non-fatal).")
        result = None   # handled below if needed
    except Exception as exc:
        _handle_vision_error(exc)

    # Serialize the VisionEvent into the API response schema
    event_schema = serialize_vision_event(result.event) if result.event else None

    return AnalyzeFrameResponse(
        success=True,
        message=(
            f"Frame analysed successfully. "
            f"Detected {result.detection_count} object(s), "
            f"risk level: {result.highest_risk.value if result.highest_risk else 'N/A'}."
        ),
        events=[event_schema] if event_schema else [],
    )


@router.get(
    "/events",
    response_model=ListEventsResponse,
    summary="List vision events",
)
async def list_events(
    camera_id:   str | None = Query(None, description="Filter by camera ID."),
    hazard_type: str | None = Query(None, description="Filter by hazard type."),
    limit:       int        = Query(50, ge=1, le=200),
    offset:      int        = Query(0,  ge=0),
    session:     AsyncSession = Depends(get_session),
) -> ListEventsResponse:
    """List stored vision events with optional filters."""

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

    try:
        events = await repo.list_events(
            camera_id=camera_id,
            hazard_type=parsed_hazard,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        log.error(f"list_events query failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve events.",
        ) from exc

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
    """Retrieve a single VisionEvent by its string event_id."""

    repo = PostgresVisionRepository(session)

    try:
        event = await repo.get_event(event_id)
    except Exception as exc:
        log.error(f"get_event({event_id}) failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event.",
        ) from exc

    if event is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Event '{event_id}' not found.",
        )

    return GetEventResponse(event=serialize_vision_event(event))


@router.get(
    "/health",
    summary="Vision module health check",
)
async def vision_health() -> dict:
    """Return the health status of the Vision module."""
    return {
        "module":      "vision",
        "status":      "ok",
        "milestone":   2,
        "detector":    "stub",
        "description": (
            "Application Layer implemented: use cases, DTOs, "
            "VisionOrchestrator, and custom exception hierarchy."
        ),
    }
