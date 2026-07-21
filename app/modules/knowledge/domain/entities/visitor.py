from datetime import datetime
from pydantic import Field

from app.modules.knowledge.domain.entities.base import Person


class Visitor(Person):
    """Temporary guest or visitor on facility premises."""

    pass_number: str
    host_worker_id: str
    check_in: datetime | None = None
    check_out: datetime | None = None
    entity_type: str = Field(default="Visitor")
