"""
infrastructure/postgres_repository.py — PostgreSQL repository implementations.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

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
from app.modules.vision.domain.entities import Camera, Detection
from app.modules.vision.domain.enums import DetectionStatus, HazardType, RiskLevel
from app.modules.vision.domain.repositories import (
    CameraRepository,
    RepositoryError,
    VisionRepository,
)
from app.modules.vision.domain.value_objects import BoundingBox, RiskScore

log = get_logger("vision.postgres_repository")


# ── ORM Models ─────────────────────────────────────────────────────────────────

class CameraModel(Base):
    """
    SQLAlchemy ORM model for registered cameras.
    """

    __tablename__ = "vision_cameras"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str] = mapped_column(String(256), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    detections: Mapped[List["DetectionModel"]] = relationship(
        "DetectionModel",
        back_populates="camera",
        cascade="all, delete-orphan",
    )


VisionEventModel = CameraModel


class DetectionModel(Base):
    """
    SQLAlchemy ORM model for individual detections.
    """

    __tablename__ = "vision_detections"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    camera_id: Mapped[UUID] = mapped_column(ForeignKey("vision_cameras.id"), nullable=False, index=True)
    hazard_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_x_min: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_y_min: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_x_max: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_y_max: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    risk_reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    camera: Mapped["CameraModel"] = relationship("CameraModel", back_populates="detections")


# ── Domain ↔ ORM converters ────────────────────────────────────────────────────

def _camera_to_orm(camera: Camera) -> CameraModel:
    return CameraModel(
        id=camera.id,
        name=camera.name,
        location=camera.location,
        is_active=camera.is_active,
        created_at=camera.created_at,
    )


def _orm_to_camera(row: CameraModel) -> Camera:
    return Camera(
        id=row.id,
        name=row.name,
        location=row.location,
        is_active=row.is_active,
        created_at=row.created_at,
    )


def _detection_to_orm(det: Detection) -> DetectionModel:
    return DetectionModel(
        id=det.id,
        camera_id=det.camera_id,
        hazard_type=det.hazard_type.value,
        confidence=det.confidence,
        bbox_x_min=det.bounding_box.x_min,
        bbox_y_min=det.bounding_box.y_min,
        bbox_x_max=det.bounding_box.x_max,
        bbox_y_max=det.bounding_box.y_max,
        risk_score=det.risk.score,
        risk_level=det.risk.level.value,
        risk_reason=det.risk.reason,
        status=det.status.value,
        detected_at=det.detected_at,
    )


def _orm_to_detection(row: DetectionModel) -> Detection:
    return Detection(
        id=row.id,
        camera_id=row.camera_id,
        hazard_type=HazardType(row.hazard_type),
        confidence=row.confidence,
        bounding_box=BoundingBox(
            x_min=row.bbox_x_min,
            y_min=row.bbox_y_min,
            x_max=row.bbox_x_max,
            y_max=row.bbox_y_max,
        ),
        risk=RiskScore(
            score=row.risk_score,
            level=RiskLevel(row.risk_level),
            reason=row.risk_reason,
        ),
        status=DetectionStatus(row.status),
        detected_at=row.detected_at,
    )


# ── Repository implementations ─────────────────────────────────────────────────

class PostgresVisionRepository(VisionRepository):
    """
    PostgreSQL-backed VisionRepository.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, detection: Detection) -> Detection:
        log.info(f"[M1 STUB] save detection_id={detection.id}")
        # Milestone 2: uncomment
        # try:
        #     orm = _detection_to_orm(detection)
        #     self._session.add(orm)
        #     await self._session.flush()
        # except Exception as exc:
        #     raise RepositoryError(f"save failed: {exc}") from exc
        return detection

    async def get_by_id(self, detection_id: UUID) -> Detection | None:
        log.info(f"[M1 STUB] get_by_id detection_id={detection_id}")
        # Milestone 2: uncomment
        # try:
        #     stmt = select(DetectionModel).where(DetectionModel.id == detection_id)
        #     res = await self._session.execute(stmt)
        #     row = res.scalar_one_or_none()
        #     return _orm_to_detection(row) if row else None
        # except Exception as exc:
        #     raise RepositoryError(f"get_by_id failed: {exc}") from exc
        return None

    async def list_recent(self, limit: int = 100) -> list[Detection]:
        log.info(f"[M1 STUB] list_recent limit={limit}")
        return []

    async def delete(self, detection_id: UUID) -> None:
        log.info(f"[M1 STUB] delete detection_id={detection_id}")
        # Milestone 2: uncomment
        # try:
        #     stmt = select(DetectionModel).where(DetectionModel.id == detection_id)
        #     res = await self._session.execute(stmt)
        #     row = res.scalar_one_or_none()
        #     if row:
        #         await self._session.delete(row)
        # except Exception as exc:
        #     raise RepositoryError(f"delete failed: {exc}") from exc

    async def list_by_camera(self, camera_id: UUID) -> list[Detection]:
        log.info(f"[M1 STUB] list_by_camera camera_id={camera_id}")
        return []

    async def list_by_hazard(self, hazard_type: HazardType) -> list[Detection]:
        log.info(f"[M1 STUB] list_by_hazard hazard_type={hazard_type}")
        return []

    async def list_critical(self, limit: int = 50) -> list[Detection]:
        log.info(f"[M1 STUB] list_critical limit={limit}")
        return []

    async def list_between(self, start: datetime, end: datetime) -> list[Detection]:
        log.info(f"[M1 STUB] list_between start={start} end={end}")
        return []


class PostgresCameraRepository(CameraRepository):
    """
    PostgreSQL-backed CameraRepository.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, camera: Camera) -> Camera:
        log.info(f"[M1 STUB] save camera_id={camera.id}")
        # Milestone 2: uncomment
        # try:
        #     orm = _camera_to_orm(camera)
        #     self._session.add(orm)
        #     await self._session.flush()
        # except Exception as exc:
        #     raise RepositoryError(f"save failed: {exc}") from exc
        return camera

    async def get_by_id(self, camera_id: UUID) -> Camera | None:
        log.info(f"[M1 STUB] get_by_id camera_id={camera_id}")
        # Milestone 2: uncomment
        # try:
        #     stmt = select(CameraModel).where(CameraModel.id == camera_id)
        #     res = await self._session.execute(stmt)
        #     row = res.scalar_one_or_none()
        #     return _orm_to_camera(row) if row else None
        # except Exception as exc:
        #     raise RepositoryError(f"get_by_id failed: {exc}") from exc
        return None

    async def list_all(self) -> list[Camera]:
        log.info("[M1 STUB] list_all")
        return []

    async def update(self, camera: Camera) -> Camera:
        log.info(f"[M1 STUB] update camera_id={camera.id}")
        # Milestone 2: uncomment
        # try:
        #     stmt = select(CameraModel).where(CameraModel.id == camera.id)
        #     res = await self._session.execute(stmt)
        #     row = res.scalar_one_or_none()
        #     if row:
        #         row.name = camera.name
        #         row.location = camera.location
        #         row.is_active = camera.is_active
        #         await self._session.flush()
        # except Exception as exc:
        #     raise RepositoryError(f"update failed: {exc}") from exc
        return camera
