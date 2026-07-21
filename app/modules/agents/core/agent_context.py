"""agent_context.py — Immutable AgentContext model."""

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentContext(BaseModel):
    """
    Immutable execution context passed to all agents.
    """

    model_config = ConfigDict(frozen=True)

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str = Field(..., description="User request statement")
    intent: str = Field(default="GENERAL_SAFETY")
    target_entity_id: str | None = Field(default=None)
    zone_id: str | None = Field(default=None)
    graph_snapshot: dict[str, Any] = Field(default_factory=dict)
    documents: list[dict[str, Any]] = Field(default_factory=list)
    sensor_data: list[dict[str, Any]] = Field(default_factory=list)
    predictions: list[dict[str, Any]] = Field(default_factory=list)
    vision_events: list[dict[str, Any]] = Field(default_factory=list)
    user_context: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
