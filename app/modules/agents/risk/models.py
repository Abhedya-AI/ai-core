"""models.py — Risk Agent Domain Models & Result DTOs."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.modules.agents.core.agent_result import AgentResult


class SeverityEnum(str, Enum):
    """Hazard and risk severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PriorityEnum(str, Enum):
    """Action priority levels."""

    P4 = "P4"
    P3 = "P3"
    P2 = "P2"
    P1 = "P1"


class RiskScore(BaseModel):
    """Deterministic risk score representation."""

    probability: float = Field(default=0.0, ge=0.0, le=1.0)
    severity: SeverityEnum = SeverityEnum.LOW
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    impact: float = Field(default=0.0, ge=0.0, le=100.0)
    priority: PriorityEnum = PriorityEnum.P4
    score_value: float = Field(default=0.0, ge=0.0, le=100.0)


class RiskEvidence(BaseModel):
    """Structured evidence gathered for risk assessment."""

    graph_facts: list[dict[str, Any]] = Field(default_factory=list)
    sensor_readings: list[dict[str, Any]] = Field(default_factory=list)
    maintenance_logs: list[dict[str, Any]] = Field(default_factory=list)
    permits: list[dict[str, Any]] = Field(default_factory=list)
    incidents: list[dict[str, Any]] = Field(default_factory=list)
    vision_events: list[dict[str, Any]] = Field(default_factory=list)


class RiskAgentResult(AgentResult):
    """Domain-extended result returned by Risk Intelligence Agent."""

    risk_score: RiskScore = Field(default_factory=RiskScore)
    severity: SeverityEnum = SeverityEnum.LOW
    affected_entities: list[str] = Field(default_factory=list)
    propagation_paths: list[dict[str, Any]] = Field(default_factory=list)
    categorized_recommendations: dict[str, list[str]] = Field(default_factory=dict)
