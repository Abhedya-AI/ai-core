"""
domain/repository.py — Abstract repository interface for the Vision module.

This file defines WHAT the application layer can ask of a persistence
layer, not HOW it is implemented.  The concrete implementation lives in
infrastructure/postgres_repository.py.

Benefits
────────
• The application use-cases depend on this interface, not on SQLAlchemy.
• Tests can inject a simple in-memory implementation.
• Swapping PostgreSQL for another store (e.g. TimescaleDB) requires
  no changes in the application or domain layers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.modules.vision.domain.entities import Detection, VisionEvent
from app.modules.vision.domain.enums import HazardType, RiskLevel


class VisionRepository(ABC):
    """
    Port (interface) for Vision module persistence.

    All methods are async to match the rest of the ABHEDYA infrastructure
    (asyncpg / SQLAlchemy async engine).
    """

    # ── VisionEvent operations ────────────────────────────────────────────────

    @abstractmethod
    async def save_event(self, event: VisionEvent) -> VisionEvent:
        """
        Persist a VisionEvent and its associated detections.

        Implementations must:
          1. Save the VisionEvent row.
          2. Save all Detection rows linked to the event.
          3. Return the saved VisionEvent (with any DB-assigned fields
             such as auto-increment surrogate keys, if applicable).

        Raises
        ──────
        RepositoryError  On any persistence failure.
        """

    @abstractmethod
    async def get_event(self, event_id: str) -> VisionEvent | None:
        """
        Retrieve a VisionEvent by its UUID.

        Returns None if no event with the given ID exists.
        """

    @abstractmethod
    async def list_events(
        self,
        *,
        camera_id:   str | None = None,
        min_risk:    RiskLevel | None = None,
        hazard_type: HazardType | None = None,
        since:       datetime | None = None,
        until:       datetime | None = None,
        limit:       int = 50,
        offset:      int = 0,
    ) -> list[VisionEvent]:
        """
        Return a filtered, paginated list of VisionEvents.

        All filter parameters are optional and may be combined.

        Parameters
        ──────────
        camera_id   Filter to events from a specific camera.
        min_risk    Return only events at or above this risk level.
        hazard_type Return only events containing this hazard type.
        since       Return events with timestamp >= since (UTC).
        until       Return events with timestamp <= until (UTC).
        limit       Maximum number of results (default 50, max 200).
        offset      Pagination offset.
        """

    # ── Detection operations ──────────────────────────────────────────────────

    @abstractmethod
    async def save_detection(self, detection: Detection) -> Detection:
        """Persist a single Detection row."""

    @abstractmethod
    async def list_detections_for_event(self, event_id: str) -> list[Detection]:
        """Return all Detection rows belonging to the given VisionEvent."""


# ── Repository Error ──────────────────────────────────────────────────────────

class RepositoryError(Exception):
    """
    Raised when a repository operation fails.

    Callers should catch this type rather than infrastructure-specific
    exceptions (e.g. SQLAlchemy IntegrityError) to preserve layer
    boundaries.
    """
