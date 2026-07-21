from typing import Any, Literal

from pydantic import BaseModel, Field

from app.modules.knowledge.domain.relationships.relationship_types import RelationshipType


class CreateRelationshipRequest(BaseModel):
    """DTO for creating a directed edge between two graph nodes."""

    source_id: str
    target_id: str
    rel_type: RelationshipType
    properties: dict[str, Any] = Field(default_factory=dict)


class NodeMatchCriteria(BaseModel):
    """Criteria for filtering graph nodes."""

    label: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphSearchRequest(BaseModel):
    """DTO for structured graph querying."""

    start_criteria: NodeMatchCriteria
    relationship_type: RelationshipType | None = None
    target_criteria: NodeMatchCriteria | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    direction: Literal["OUTGOING", "INCOMING", "BOTH"] = "OUTGOING"
