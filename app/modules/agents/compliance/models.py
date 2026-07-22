"""models.py — Compliance Intelligence Agent Domain Models & DTOs."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.modules.agents.core.agent_result import AgentResult


class ViolationSeverity(str, Enum):
    """Compliance violation severity levels."""

    MINOR = "MINOR"
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"


class ComplianceViolation(BaseModel):
    """Structured compliance violation item."""

    violation_id: str
    violation_type: str = Field(..., description="e.g. EXPIRED_PERMIT, SOP_SEQUENCE_SKIPPED, MISSING_PPE")
    severity: ViolationSeverity = ViolationSeverity.MAJOR
    affected_entity: str
    evidence_summary: str
    regulation_reference: str = "OSHA-1910.147"
    timestamp: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ComplianceScore(BaseModel):
    """Multi-dimensional compliance score."""

    overall_score: float = Field(default=100.0, ge=0.0, le=100.0)
    critical_violations_count: int = 0
    major_violations_count: int = 0
    minor_violations_count: int = 0
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)


class ComplianceEvidence(BaseModel):
    """Gathered evidence bundle for compliance evaluation."""

    permits: list[dict[str, Any]] = Field(default_factory=list)
    sops: list[dict[str, Any]] = Field(default_factory=list)
    regulations: list[dict[str, Any]] = Field(default_factory=list)
    worker_certifications: list[dict[str, Any]] = Field(default_factory=list)
    maintenance_records: list[dict[str, Any]] = Field(default_factory=list)
    vision_observations: list[dict[str, Any]] = Field(default_factory=list)
    graph_context: list[dict[str, Any]] = Field(default_factory=list)


class ComplianceAgentResult(AgentResult):
    """Domain-extended result returned by Compliance Intelligence Agent."""

    compliance_score: ComplianceScore = Field(default_factory=ComplianceScore)
    is_compliant: bool = True
    violations: list[ComplianceViolation] = Field(default_factory=list)
    permit_validation: dict[str, Any] = Field(default_factory=dict)
    sop_validation: dict[str, Any] = Field(default_factory=dict)
    categorized_recommendations: dict[str, list[str]] = Field(default_factory=dict)
    referenced_regulations: list[str] = Field(default_factory=list)
