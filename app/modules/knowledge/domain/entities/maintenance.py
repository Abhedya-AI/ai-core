from datetime import datetime
from pydantic import Field

from app.modules.knowledge.domain.entities.base import EventEntity


class Maintenance(EventEntity):
    """Maintenance task executed on plant equipment."""

    equipment_id: str
    assigned_worker_id: str
    permit_id: str | None = None
    task_description: str
    scheduled_date: datetime
    completed_date: datetime | None = None
    is_preventative: bool = True
    entity_type: str = Field(default="Maintenance")
