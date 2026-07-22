from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.modules.vision.domain.entities import Detection
from app.modules.vision.domain.enums import HazardType


class RepositoryError(Exception):
    """Base exception for vision repository failures."""
    pass


class VisionRepository(ABC):
    """
    Repository contract for Detection persistence.
    """

    @abstractmethod
    async def save(self, detection: Detection) -> Detection:
        """Persist a detection."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, detection_id: UUID) -> Detection | None:
        """Retrieve a detection by ID."""
        raise NotImplementedError

    @abstractmethod
    async def list_recent(
        self,
        limit: int = 100,
    ) -> list[Detection]:
        """Return recent detections."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, detection_id: UUID) -> None:
        """Delete a detection."""
        raise NotImplementedError

    # Business queries for advanced growth
    @abstractmethod
    async def list_by_camera(self, camera_id: UUID) -> list[Detection]:
        """List detections for a specific camera."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_hazard(self, hazard_type: HazardType) -> list[Detection]:
        """List detections for a specific hazard type."""
        raise NotImplementedError

    @abstractmethod
    async def list_critical(self, limit: int = 50) -> list[Detection]:
        """List recent critical detections."""
        raise NotImplementedError

    @abstractmethod
    async def list_between(self, start: datetime, end: datetime) -> list[Detection]:
        """List detections within a time range."""
        raise NotImplementedError
