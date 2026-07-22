"""
infrastructure/postgres_repository.py — PostgreSQL implementation of VisionRepository.

Milestone 1: ORM model definitions + repository skeleton with all
             method signatures implemented.
             The actual SQL operations are stubs that log and return the
             input unchanged (no DB required to run the pipeline).

Milestone 2: Uncomment the SQLAlchemy operations and run the migration.

ORM Models (defined here, registered with the shared Base)
──────────────────────────────────────────────────────────
DetectionModel   → Postgres table: vision_detections
VisionEventModel → Postgres table: vision_events

Table design follows the spec:
    vision_events
        id, event_id, timestamp, camera_id, frame_id,
        risk_level, risk_value, detection_count, hazard_count,
        image_path, location, metadata

    vision_detections
        id, detection_id, event_id (FK), timestamp,
        camera_id, frame_id, hazard_type, confidence,
        risk_level, bbox_x1..y2, image_path
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.logging import get_logger
from app.infrastructure.postgres.base import Base
from app.modules.vision.domain.entities import Detection, Hazard, VisionEvent
from app.modules.vision.domain.enums import HazardType, RiskLevel
from app.modules.vision.domain.repository import RepositoryError, VisionRepository
from app.modules.vision.domain.value_objects import BoundingBox, RiskScore

log = get_logger("vision.postgres_repository")


# ── ORM Models ─────────────────────────────────────────────────────────────────

class VisionEventModel(Base):
    """
    SQLAlchemy ORM model for vision_events table.

    Stores the frame-level aggregate: risk score, camera, frame,
    location, and counts.  Detections are stored separately.
    """

    __tablename__ = "vision_events"

    id:              Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id:        Mapped[str]            = mapped_column(String(36), unique=True, nullable=False, index=True)
    timestamp:       Mapped[datetime]       = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    camera_id:       Mapped[str]            = mapped_column(String(128), nullable=False, index=True)
    frame_id:        Mapped[str]            = mapped_column(String(128), nullable=False)
    risk_level:      Mapped[str]            = mapped_column(String(16), nullable=False)
    risk_value:      Mapped[float]          = mapped_column(Float, nullable=False)
    detection_count: Mapped[int]            = mapped_column(Integer, nullable=False, default=0)
    hazard_count:    Mapped[int]            = mapped_column(Integer, nullable=False, default=0)
    image_path:      Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    location:        Mapped[Optional[str]]  = mapped_column(String(256), nullable=True)
    metadata_json:   Mapped[Optional[Any]]  = mapped_column("metadata", JSON, nullable=True)

    # Relationship
    detections: Mapped[List["DetectionModel"]] = relationship(
        "DetectionModel",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DetectionModel(Base):
    """
    SQLAlchemy ORM model for vision_detections table.

    Stores each individual detection with its bounding box,
    hazard type, confidence, and risk level.
    """

    __tablename__ = "vision_detections"

    id:           Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    detection_id: Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, index=True)
    event_id_fk:  Mapped[str]           = mapped_column("event_id", String(36), ForeignKey("vision_events.event_id"), nullable=False, index=True)
    timestamp:    Mapped[datetime]      = mapped_column(DateTime(timezone=True), nullable=False)
    camera_id:    Mapped[str]           = mapped_column(String(128), nullable=False)
    frame_id:     Mapped[str]           = mapped_column(String(128), nullable=False)
    hazard_type:  Mapped[str]           = mapped_column(String(32), nullable=False, index=True)
    confidence:   Mapped[float]         = mapped_column(Float, nullable=False)
    risk_level:   Mapped[str]           = mapped_column(String(16), nullable=False)
    bbox_x1:      Mapped[float]         = mapped_column(Float, nullable=False)
    bbox_y1:      Mapped[float]         = mapped_column(Float, nullable=False)
    bbox_x2:      Mapped[float]         = mapped_column(Float, nullable=False)
    bbox_y2:      Mapped[float]         = mapped_column(Float, nullable=False)
    image_path:   Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    event: Mapped["VisionEventModel"] = relationship("VisionEventModel", back_populates="detections")


# ── Domain ↔ ORM converters ────────────────────────────────────────────────────

def _detection_to_orm(det: Detection, event_id: str) -> DetectionModel:
    """Convert a domain Detection to its ORM representation."""
    from app.modules.vision.application.calculate_risk import _score_to_level, _HAZARD_WEIGHTS
    weight = _HAZARD_WEIGHTS.get(det.hazard_type, 0.0) * det.confidence
    risk_level = _score_to_level(weight)

    return DetectionModel(
        detection_id=det.id,
        event_id_fk=event_id,
        timestamp=det.timestamp,
        camera_id=det.camera_id,
        frame_id=det.frame_id,
        hazard_type=det.hazard_type.value,
        confidence=det.confidence,
        risk_level=risk_level.value,
        bbox_x1=det.bounding_box.x_min,
        bbox_y1=det.bounding_box.y_min,
        bbox_x2=det.bounding_box.x_max,
        bbox_y2=det.bounding_box.y_max,
        image_path=det.image_path,
    )


def _orm_to_detection(row: DetectionModel) -> Detection:
    """Convert an ORM DetectionModel row back to a domain Detection."""
    return Detection(
        id=row.detection_id,
        hazard_type=HazardType(row.hazard_type),
        confidence=row.confidence,
        bounding_box=BoundingBox(
            x_min=row.bbox_x1,
            y_min=row.bbox_y1,
            x_max=row.bbox_x2,
            y_max=row.bbox_y2,
        ),
        frame_id=row.frame_id,
        camera_id=row.camera_id,
        timestamp=row.timestamp,
        image_path=row.image_path,
    )


def _event_to_orm(event: VisionEvent) -> VisionEventModel:
    """Convert a domain VisionEvent to its ORM representation."""
    return VisionEventModel(
        event_id=event.event_id,
        timestamp=event.timestamp,
        camera_id=event.camera_id,
        frame_id=event.frame_id,
        risk_level=event.risk_score.level.value,
        risk_value=event.risk_score.score,
        detection_count=event.detection_count,
        hazard_count=event.hazard_count,
        image_path=event.image_path,
        location=event.location,
        metadata_json=event.metadata,
    )


# ── Repository implementation ─────────────────────────────────────────────────

class PostgresVisionRepository(VisionRepository):
    """
    PostgreSQL-backed VisionRepository.

    Constructor
    ───────────
    session     AsyncSession from the ABHEDYA session factory.

    Milestone 1
    ───────────
    All methods are present but use stub SQL paths (logged, not
    executed) so the pipeline runs without a DB connection.

    To activate real persistence in Milestone 2:
      1. Remove the "# M1 STUB" blocks.
      2. Uncomment the SQLAlchemy operations.
      3. Run: uv run alembic revision --autogenerate -m "vision_module"
              uv run alembic upgrade head
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── save_event ─────────────────────────────────────────────────────────────

    async def save_event(self, event: VisionEvent) -> VisionEvent:
        log.info(f"[M1 STUB] save_event event_id={event.event_id}")

        # ── Milestone 2: uncomment ────────────────────────────────────────────
        # try:
        #     event_orm = _event_to_orm(event)
        #     self._session.add(event_orm)
        #
        #     for det in event.detections:
        #         det_orm = _detection_to_orm(det, event.event_id)
        #         self._session.add(det_orm)
        #
        #     await self._session.flush()
        #     log.info(f"VisionEvent {event.event_id} flushed to DB.")
        # except Exception as exc:
        #     raise RepositoryError(f"save_event failed: {exc}") from exc
        # ─────────────────────────────────────────────────────────────────────

        return event

    # ── get_event ──────────────────────────────────────────────────────────────

    async def get_event(self, event_id: str) -> VisionEvent | None:
        log.info(f"[M1 STUB] get_event event_id={event_id}")

        # ── Milestone 2: uncomment ────────────────────────────────────────────
        # try:
        #     stmt = select(VisionEventModel).where(
        #         VisionEventModel.event_id == event_id
        #     )
        #     result = await self._session.execute(stmt)
        #     row = result.scalar_one_or_none()
        #     if row is None:
        #         return None
        #     return _orm_to_event(row)
        # except Exception as exc:
        #     raise RepositoryError(f"get_event failed: {exc}") from exc
        # ─────────────────────────────────────────────────────────────────────

        return None

    # ── list_events ────────────────────────────────────────────────────────────

    async def list_events(
        self,
        *,
        camera_id=None,
        min_risk=None,
        hazard_type=None,
        since=None,
        until=None,
        limit=50,
        offset=0,
    ) -> list[VisionEvent]:
        log.info("[M1 STUB] list_events — returning []")
        return []

    # ── save_detection ─────────────────────────────────────────────────────────

    async def save_detection(self, detection: Detection) -> Detection:
        log.info(f"[M1 STUB] save_detection detection_id={detection.id}")
        return detection

    # ── list_detections_for_event ──────────────────────────────────────────────

    async def list_detections_for_event(self, event_id: str) -> list[Detection]:
        log.info(f"[M1 STUB] list_detections_for_event event_id={event_id}")
        return []
