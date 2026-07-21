"""telemetry.py — Agent Execution Telemetry Model."""

from pydantic import BaseModel, Field


class AgentTelemetry(BaseModel):
    """Telemetry metrics recorded per agent execution."""

    agent_name: str
    execution_time_ms: int = 0
    tokens_used: int = 0
    graph_queries_executed: int = 0
    documents_retrieved: int = 0
    confidence: float = 1.0
    errors_count: int = 0
    retries_count: int = 0
    events_published: int = 0
