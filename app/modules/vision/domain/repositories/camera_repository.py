from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.vision.domain.entities import Camera


class CameraRepository(ABC):
    """
    Repository contract for Camera persistence.
    """

    @abstractmethod
    async def save(self, camera: Camera) -> Camera:
        """Persist a camera."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, camera_id: UUID) -> Camera | None:
        """Retrieve a camera by its unique identifier."""
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[Camera]:
        """List all cameras registered in the system."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, camera: Camera) -> Camera:
        """Update an existing camera's details."""
        raise NotImplementedError
