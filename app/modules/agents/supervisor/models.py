"""models.py — Supervisor Agent Domain Models & DTOs."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.types import Capability


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class WorkflowState(str, Enum):
    """Lifecycle states for Supervisor workflow execution."""

    QUEUED = "QUEUED"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"  # HITL checkpoint
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REPLANNING = "REPLANNING"


class WorkflowIntent(str, Enum):
    """High-level domain intents extracted by TaskAnalyzer."""

    EMERGENCY_INVESTIGATION = "EMERGENCY_INVESTIGATION"
    PREDICTION = "PREDICTION"
    ROOT_CAUSE_ANALYSIS = "ROOT_CAUSE_ANALYSIS"
    COMPLIANCE_AUDIT = "COMPLIANCE_AUDIT"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    DOCUMENT_RESEARCH = "DOCUMENT_RESEARCH"
    VISION_SURVEILLANCE = "VISION_SURVEILLANCE"
    GENERAL_SAFETY = "GENERAL_SAFETY"


class ConflictResolutionStrategy(str, Enum):
    """Strategies for resolving conflicting agent outputs."""

    HIGHEST_CONFIDENCE = "HIGHEST_CONFIDENCE"
    SOURCE_AUTHORITY = "SOURCE_AUTHORITY"
    CONSERVATIVE_SAFETY = "CONSERVATIVE_SAFETY"
    HUMAN_REVIEW = "HUMAN_REVIEW"


# ---------------------------------------------------------------------------
# Core Workflow DTOs
# ---------------------------------------------------------------------------

class WorkflowStep(BaseModel):
    """Single step in an execution workflow."""

    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stage_name: str = Field(...)
    agent_name: str = Field(...)
    capability_required: Capability = Field(...)
    depends_on: list[str] = Field(default_factory=list)
    allow_parallel: bool = Field(default=False)
    status: str = Field(default="PENDING")
    timeout_seconds: float = Field(default=30.0)


class HITLCheckpoint(BaseModel):
    """Human-in-the-Loop checkpoint requiring operator approval before proceeding."""

    checkpoint_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = Field(...)
    stage_name: str = Field(...)
    reason: str = Field(default="High-impact emergency response action requires safety officer approval.")
    required_role: str = Field(default="SAFETY_OFFICER")
    approved: bool | None = Field(default=None)
    approved_by: str | None = Field(default=None)
    approved_at: str | None = Field(default=None)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ConflictRecord(BaseModel):
    """Records a conflict between two agent outputs and how it was resolved."""

    conflict_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_a: str = Field(...)
    output_a: Any = Field(...)
    confidence_a: float = Field(...)
    agent_b: str = Field(...)
    output_b: Any = Field(...)
    confidence_b: float = Field(...)
    resolution_strategy: ConflictResolutionStrategy = Field(...)
    winning_agent: str = Field(...)
    resolved_output: Any = Field(...)
    rationale: str = Field(default="")


class AggregatedResult(BaseModel):
    """Unified incident report / response synthesized by Supervisor."""

    workflow_id: str = Field(...)
    intent: WorkflowIntent = Field(default=WorkflowIntent.GENERAL_SAFETY)
    overall_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    primary_findings: list[str] = Field(default_factory=list)
    risk_summary: dict[str, Any] = Field(default_factory=dict)
    vision_summary: dict[str, Any] = Field(default_factory=dict)
    prediction_summary: dict[str, Any] = Field(default_factory=dict)
    root_cause_summary: dict[str, Any] = Field(default_factory=dict)
    compliance_summary: dict[str, Any] = Field(default_factory=dict)
    emergency_plan_summary: dict[str, Any] = Field(default_factory=dict)
    notifications_dispatched: list[dict[str, Any]] = Field(default_factory=list)
    document_evidence: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    conflicts_resolved: list[ConflictRecord] = Field(default_factory=list)
    hitl_checkpoints: list[HITLCheckpoint] = Field(default_factory=list)


class SupervisorTelemetry(BaseModel):
    """Performance telemetry captured across the workflow execution."""

    workflow_id: str = Field(...)
    planning_time_ms: int = Field(default=0)
    execution_time_ms: int = Field(default=0)
    parallel_efficiency: float = Field(default=0.0, ge=0.0, le=1.0)
    agent_invocations: int = Field(default=0)
    parallel_groups_count: int = Field(default=0)
    retries_count: int = Field(default=0)
    failures_count: int = Field(default=0)
    graph_queries_count: int = Field(default=0)
    cache_hits: int = Field(default=0)
    agent_latencies_ms: dict[str, int] = Field(default_factory=dict)


class SupervisorAgentResult(AgentResult):
    """Domain-extended result returned by Supervisor Agent."""

    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    intent: WorkflowIntent = Field(default=WorkflowIntent.GENERAL_SAFETY)
    workflow_state: WorkflowState = Field(default=WorkflowState.COMPLETED)
    aggregated_report: AggregatedResult | None = Field(default=None)
    execution_summary: str = Field(default="")
    orchestration_telemetry: SupervisorTelemetry | None = Field(default=None)
