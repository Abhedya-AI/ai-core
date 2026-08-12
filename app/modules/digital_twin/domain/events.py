from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.modules.digital_twin.domain.enums import (
    SimulationType, SimulationStatus, ScenarioType, OptimizationTarget,
    PlanType, StateTransitionReason, EntityType
)

def _now_iso() -> str: 
    return datetime.now(timezone.utc).isoformat()

def _uuid() -> str: 
    return str(uuid.uuid4())

class TwinDomainEvent(BaseModel):
    model_config = ConfigDict(frozen=True)
    event_id: str = Field(default_factory=_uuid)
    event_type: str
    timestamp: str = Field(default_factory=_now_iso)
    source: str = Field(default="digital_twin")
    correlation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TwinCreated(TwinDomainEvent):
    event_type: str = Field(default="TwinCreated")
    twin_id: str
    plant_id: str
    plant_name: str
    sync_mode: str


class TwinUpdated(TwinDomainEvent):
    event_type: str = Field(default="TwinUpdated")
    twin_id: str
    updated_fields: list[str]
    version_number: int


class TwinSnapshotCreated(TwinDomainEvent):
    event_type: str = Field(default="TwinSnapshotCreated")
    twin_id: str
    snapshot_id: str
    version_number: int
    entity_count: int
    description: str


class TwinStateChanged(TwinDomainEvent):
    event_type: str = Field(default="TwinStateChanged")
    twin_id: str
    entity_id: str
    entity_type: EntityType
    old_status: str
    new_status: str
    reason: StateTransitionReason
    risk_score: float
    health_score: float


class SimulationStarted(TwinDomainEvent):
    event_type: str = Field(default="SimulationStarted")
    twin_id: str
    simulation_id: str
    simulation_type: SimulationType
    title: str


class SimulationCompleted(TwinDomainEvent):
    event_type: str = Field(default="SimulationCompleted")
    twin_id: str
    simulation_id: str
    simulation_type: SimulationType
    status: SimulationStatus
    confidence: float
    latency_ms: float


class ScenarioGenerated(TwinDomainEvent):
    event_type: str = Field(default="ScenarioGenerated")
    twin_id: str
    scenario_id: str
    scenario_type: ScenarioType
    probability: float
    confidence: float


class OptimizationCompleted(TwinDomainEvent):
    event_type: str = Field(default="OptimizationCompleted")
    twin_id: str
    optimization_id: str
    target: OptimizationTarget
    improvement_pct: float | None
    latency_ms: float


class ReplayStarted(TwinDomainEvent):
    event_type: str = Field(default="ReplayStarted")
    twin_id: str
    replay_id: str
    start_timestamp: str
    end_timestamp: str
    replay_by: str


class ReplayCompleted(TwinDomainEvent):
    event_type: str = Field(default="ReplayCompleted")
    twin_id: str
    replay_id: str
    total_frames: int
    events_replayed_count: int
    duration_seconds: float


class PlanningGenerated(TwinDomainEvent):
    event_type: str = Field(default="PlanningGenerated")
    twin_id: str
    plan_id: str
    plan_type: PlanType
    entity_id: str
    action_count: int
    confidence: float


TWIN_EVENT_TOPICS = {
    "TwinCreated": "twin.created",
    "TwinUpdated": "twin.updated",
    "TwinSnapshotCreated": "twin.snapshot.created",
    "TwinStateChanged": "twin.state.changed",
    "SimulationStarted": "twin.simulation.started",
    "SimulationCompleted": "twin.simulation.completed",
    "ScenarioGenerated": "twin.scenario.generated",
    "OptimizationCompleted": "twin.optimization.completed",
    "ReplayStarted": "twin.replay.started",
    "ReplayCompleted": "twin.replay.completed",
    "PlanningGenerated": "twin.planning.generated",
}
