"""
domain/repositories/vision_repository.py — VisionRepository contract.

This is a pure interface (ABC). Infrastructure implementations live in
infrastructure/postgres_repository.py and similar.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.modules.vision.domain.enums import HazardType


class VisionRepository(ABC):
    """
    Repository contract for VisionEvent and Detection persistence.

    The implementation is injected at startup (dependency injection).
    Tests use InMemoryVisionRepository; production uses PostgresRepository.
    """

    # ── VisionEvent CRUD ───────────────────────────────────────────────────────

    @abstractmethod
    async def save_event(self, event) -> object:
        """Persist a VisionEvent and return the saved instance."""
        raise NotImplementedError

    @abstractmethod
    async def get_event(self, event_id: str) -> Optional[object]:
        """Retrieve a VisionEvent by its string event_id."""
        raise NotImplementedError

    @abstractmethod
    async def list_events(self, **kwargs) -> list:
        """List VisionEvents with optional filters (camera_id, limit, etc.)."""
        raise NotImplementedError

    # ── Detection CRUD ─────────────────────────────────────────────────────────

    @abstractmethod
    async def save_detection(self, detection) -> object:
        """Persist a Detection and return the saved instance."""
        raise NotImplementedError

    @abstractmethod
    async def list_detections_for_event(self, event_id: str) -> list:
        """List all Detections that belong to a given VisionEvent."""
        raise NotImplementedError

    # ── Legacy / advanced queries (optional, default no-op) ───────────────────

    async def list_by_camera(self, camera_id: str) -> list:
        """List detections for a specific camera."""
        return []

    async def list_by_hazard(self, hazard_type: HazardType) -> list:
        """List detections for a specific hazard type."""
        return []

    async def list_critical(self, limit: int = 50) -> list:
        """List recent critical detections."""
        return []

    async def list_between(self, start: datetime, end: datetime) -> list:
        """List detections within a time range."""
        return []
