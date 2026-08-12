from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.modules.hazard_propagation.domain.enums import (
    HazardType, PropagationState, ExposureLevel, EvacuationStatus, 
    CascadeStatus, HazardSeverity, PropagationModelType, SimulationStatus
)

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _uuid() -> str:
    return str(uuid.uuid4())

class HazardDomainEvent(BaseModel):
    model_config = ConfigDict(frozen=True)
    event_id: str = Field(default_factory=_uuid)
    event_type: str = Field(...)
    timestamp: str = Field(default_factory=_now_iso)
    source: str = Field(default="hazard_propagation")
    correlation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class HazardDetected(HazardDomainEvent):
    event_type: str = Field(default="HazardDetected")
    propagation_id: str
    hazard_type: HazardType
    source_node_id: str
    source_zone_id: str
    initial_intensity: float
    severity: HazardSeverity

class PropagationStarted(HazardDomainEvent):
    event_type: str = Field(default="PropagationStarted")
    propagation_id: str
    hazard_type: HazardType
    source_node_id: str
    model_type: PropagationModelType

class PropagationUpdated(HazardDomainEvent):
    event_type: str = Field(default="PropagationUpdated")
    propagation_id: str
    hazard_type: HazardType
    affected_node_count: int
    current_intensity: float
    state: PropagationState

class ExposureThresholdExceeded(HazardDomainEvent):
    event_type: str = Field(default="ExposureThresholdExceeded")
    propagation_id: str
    zone_id: str
    exposure_level: ExposureLevel
    worker_count_at_risk: int
    concentration_ppm: float
    hazard_type: HazardType

class ContainmentGenerated(HazardDomainEvent):
    event_type: str = Field(default="ContainmentGenerated")
    propagation_id: str
    plan_id: str
    hazard_type: HazardType
    action_count: int
    estimated_containment_time_minutes: float
    confidence: float

class EvacuationGenerated(HazardDomainEvent):
    event_type: str = Field(default="EvacuationGenerated")
    propagation_id: str
    recommendation_id: str
    evacuation_status: EvacuationStatus
    zones_to_evacuate: list[str]
    worker_count: int

class CascadeDetected(HazardDomainEvent):
    event_type: str = Field(default="CascadeDetected")
    propagation_id: str
    cascade_id: str
    trigger_hazard_type: HazardType
    resulting_hazard_type: HazardType
    probability: float
    stages: int

class SimulationCompleted(HazardDomainEvent):
    event_type: str = Field(default="SimulationCompleted")
    simulation_id: str
    scenario_id: str
    status: SimulationStatus
    peak_affected_workers: int
    containment_effectiveness: float
    latency_ms: float

class PropagationCompleted(HazardDomainEvent):
    event_type: str = Field(default="PropagationCompleted")
    propagation_id: str
    hazard_type: HazardType
    final_state: PropagationState
    affected_zone_count: int
    affected_worker_count: int
    containment_plan_generated: bool
    evacuation_generated: bool
    latency_ms: float

HAZARD_EVENT_TOPICS = {
    "HazardDetected": "hazard.detected",
    "PropagationStarted": "hazard.propagation.started",
    "PropagationUpdated": "hazard.propagation.updated",
    "ExposureThresholdExceeded": "hazard.exposure.exceeded",
    "ContainmentGenerated": "hazard.containment.generated",
    "EvacuationGenerated": "hazard.evacuation.generated",
    "CascadeDetected": "hazard.cascade.detected",
    "SimulationCompleted": "hazard.simulation.completed",
    "PropagationCompleted": "hazard.propagation.completed",
}
