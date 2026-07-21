from pydantic import Field

from app.modules.knowledge.domain.entities.base import ObservationEntity


class Camera(ObservationEntity):
    """CCTV or AI vision camera monitoring plant zones."""

    ip_address: str | None = None
    stream_url: str | None = None
    fps: int = Field(default=30)
    zone_id: str | None = None
    ai_vision_enabled: bool = True
    entity_type: str = Field(default="Camera")
