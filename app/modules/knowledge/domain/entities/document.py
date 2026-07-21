from pydantic import Field

from app.modules.knowledge.domain.entities.base import GraphEntity


class Document(GraphEntity):
    """SOP, safety manual, regulatory text, or incident report."""

    title: str
    doc_type: str = "SOP"   # SOP, REGULATION, MANUAL, REPORT
    source_url: str | None = None
    version: str = "1.0"
    total_chunks: int = 0
    entity_type: str = Field(default="Document")
