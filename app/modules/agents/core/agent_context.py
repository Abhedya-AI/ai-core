"""agent_context.py — Standardized Agent Execution Context DTO."""

import uuid
from typing import Any

from pydantic import BaseModel, Field


class AgentContext(BaseModel):
    """
    Standardized execution context passed to all agents.

    Encapsulates user request, trace telemetry, graph snapshots,
    sensor feeds, document chunks, and execution state.
    """

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str = Field(..., description="User request or triggering task statement")
    target_entity_id: str | None = Field(default=None, description="Optional primary entity ID (e.g. Tank T-12)")
    zone_id: str | None = Field(default=None, description="Optional target zone ID")
    graph_snapshot: dict[str, Any] = Field(default_factory=dict)
    documents: list[dict[str, Any]] = Field(default_factory=list)
    sensor_data: list[dict[str, Any]] = Field(default_factory=list)
    predictions: list[dict[str, Any]] = Field(default_factory=list)
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
