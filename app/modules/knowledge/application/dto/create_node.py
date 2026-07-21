from typing import Any

from pydantic import BaseModel, Field


class CreateNodeRequest(BaseModel):
    """DTO for requesting node creation in the knowledge graph."""

    label: str = Field(..., description="Graph label / entity type (e.g., Worker, Equipment)")
    node_id: str | None = Field(default=None, description="Optional custom unique node ID")
    properties: dict[str, Any] = Field(default_factory=dict, description="Node property key-value map")
