from pydantic import Field

from app.modules.knowledge.domain.entities.base import EventEntity


class Notification(EventEntity):
    """Alert or push notification sent to workers/supervisors."""

    recipient_worker_id: str
    channel: str = "SMS"   # SMS, EMAIL, APP_PUSH, SIREN
    message: str
    read: bool = False
    priority: str = "HIGH"
    entity_type: str = Field(default="Notification")
