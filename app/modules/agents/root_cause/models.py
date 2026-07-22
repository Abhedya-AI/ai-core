"""models.py — Root Cause Intelligence Agent Domain Models & DTOs."""

from typing import Any

from pydantic import BaseModel, Field

from app.modules.agents.core.agent_result import AgentResult


class TimelineEvent(BaseModel):
    """Chronologically ordered event item."""

    timestamp: str
    event_label: str
    source: str = Field(..., description="e.g. SENSOR, VISION, MAINTENANCE, GRAPH")
    entity_id: str
    details: dict[str, Any] = Field(default_factory=dict)


class CausalEdge(BaseModel):
    """Directed edge in the reconstructed causal graph."""

    cause_id: str
    effect_id: str
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    supporting_evidence: list[str] = Field(default_factory=list)
    source: str = "GRAPH_REASONING"


class Hypothesis(BaseModel):
    """Evaluated root cause hypothesis candidate."""

    hypothesis_id: str
    root_cause_candidate: str
    description: str
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    rank: int = 1
    supporting_evidence: list[str] = Field(default_factory=list)
    causal_path: list[str] = Field(default_factory=list)


class EvidenceBundle(BaseModel):
    """Multi-source evidence collected for root cause investigation."""

    incident_id: str
    graph_facts: list[dict[str, Any]] = Field(default_factory=list)
    sensor_timeline: list[dict[str, Any]] = Field(default_factory=list)
    vision_detections: list[dict[str, Any]] = Field(default_factory=list)
    maintenance_records: list[dict[str, Any]] = Field(default_factory=list)
    permits: list[dict[str, Any]] = Field(default_factory=list)
    historical_incidents: list[dict[str, Any]] = Field(default_factory=list)
    regulatory_rules: list[dict[str, Any]] = Field(default_factory=list)


class RootCauseAgentResult(AgentResult):
    """Domain-extended result returned by Root Cause Intelligence Agent."""

    incident_id: str = ""
    timeline: list[TimelineEvent] = Field(default_factory=list)
    causal_graph: list[CausalEdge] = Field(default_factory=list)
    ranked_hypotheses: list[Hypothesis] = Field(default_factory=list)
    primary_root_cause: str = ""
    corrective_actions: dict[str, list[str]] = Field(default_factory=dict)
