from typing import Any

from pydantic import BaseModel, Field


class UpdateNodeRequest(BaseModel):
    """DTO for updating node properties."""

    node_id: str = Field(..., description="Unique node ID to update")
    label: str | None = Field(default=None, description="Optional entity label for indexing")
    properties: dict[str, Any] = Field(..., description="Properties to set or update")
