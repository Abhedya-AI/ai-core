"""agent_result.py — Unified AgentResult model."""

from typing import Any

from pydantic import BaseModel, Field

from app.modules.agents.core.events import AgentDomainEvent
from app.modules.agents.core.telemetry import AgentTelemetry


class AgentResult(BaseModel):
    """Unified result model returned by all agent executions."""

    agent_name: str = Field(...)
    success: bool = Field(default=True)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    execution_time_ms: int = Field(default=0, ge=0)
    evidence: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    events: list[AgentDomainEvent] = Field(default_factory=list)
    output_data: dict[str, Any] = Field(default_factory=dict)
    explanation: str = Field(default="")
    telemetry: AgentTelemetry | None = Field(default=None)
