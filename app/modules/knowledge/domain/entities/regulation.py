from pydantic import Field

from app.modules.knowledge.domain.entities.base import GraphEntity


class Regulation(GraphEntity):
    """OSHA, ISO, or factory safety regulation rule."""

    code: str   # e.g., "OSHA-1910.147"
    title: str
    authority: str = "OSHA"
    mandatory: bool = True
    summary: str
    entity_type: str = Field(default="Regulation")
