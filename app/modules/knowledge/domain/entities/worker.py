from pydantic import Field

from app.modules.knowledge.domain.entities.base import Person
from app.modules.knowledge.domain.enums import WorkerRole


class Worker(Person):
    """Factory worker or site operator entity."""

    badge_number: str
    role: WorkerRole = WorkerRole.OPERATOR
    department: str = Field(default="Operations")
    shift: str = Field(default="DAY")
    certifications: list[str] = Field(default_factory=list)
    entity_type: str = Field(default="Worker")
