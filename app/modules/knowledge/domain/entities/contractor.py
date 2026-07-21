from datetime import datetime
from pydantic import Field

from app.modules.knowledge.domain.entities.base import Person


class Contractor(Person):
    """External contractor performing specialized work on site."""

    company: str
    permit_ids: list[str] = Field(default_factory=list)
    contract_end: datetime | None = None
    safety_briefed: bool = False
    entity_type: str = Field(default="Contractor")
