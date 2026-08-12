from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.modules.hazard_propagation.domain.enums import (
    HazardType, PropagationState, ExposureLevel, ContainmentStatus,
    EvacuationStatus, CascadeStatus, BarrierType, HazardSeverity,
    PropagationModelType, SimulationStatus, NodeType, HazardRecommendationType
)
from app.core.logging import get_logger

log = get_logger(__name__)

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _uuid() -> str:
    return str(uuid.uuid4())

class HazardNode(BaseModel):
    model_config = ConfigDict(frozen=True)
    node_id: str = Field(default_factory=_uuid)
    node_type: NodeType
    label: str
    zone_id: str | None = None
    equipment_id: str | None = None
    coordinates: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    current_hazard_level: float = Field(default=0.0, ge=0.0, le=1.0)
    is_safe: bool = True
    barriers: list[str] = Field(default_factory=list)
    
    @computed_field
    def severity(self) -> HazardSeverity:
        return HazardSeverity.from_score(self.current_hazard_level)
        
    @computed_field
    def requires_evacuation(self) -> bool:
        return self.severity.evacuation_required

class HazardEdge(BaseModel):
    model_config = ConfigDict(frozen=True)
    edge_id: str = Field(default_factory=_uuid)
    source_node_id: str
    target_node_id: str
    distance_meters: float = Field(default=10.0, ge=0.0)
    resistance: float = Field(default=0.0, ge=0.0, le=1.0)
    edge_type: str = "ADJACENCY"
    is_blocked: bool = False
    barrier_ids: list[str] = Field(default_factory=list)
    
    @computed_field
    def effective_resistance(self) -> float:
        return min(1.0, max(self.resistance, 1.0 if self.is_blocked else 0.0))

class HazardState(BaseModel):
    model_config = ConfigDict(frozen=True)
    state_id: str = Field(default_factory=_uuid)
    hazard_id: str
    hazard_type: HazardType
    timestamp: str = Field(default_factory=_now_iso)
    node_id: str
    intensity: float = Field(default=0.0, ge=0.0, le=1.0)
    concentration_ppm: float = Field(default=0.0, ge=0.0)
    temperature_celsius: float = 25.0
    pressure_bar: float = 1.0
    velocity_ms: float = Field(default=0.0, ge=0.0)
    area_m2: float = Field(default=0.0, ge=0.0)
    state: PropagationState
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    
    @computed_field
    def severity(self) -> HazardSeverity:
        return HazardSeverity.from_score(self.intensity)

class HazardPropagation(BaseModel):
    model_config = ConfigDict(frozen=True)
    propagation_id: str = Field(default_factory=_uuid)
    hazard_type: HazardType
    source_node_id: str
    source_zone_id: str = ""
    initial_intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    initial_concentration_ppm: float = Field(default=0.0, ge=0.0)
    state: PropagationState = PropagationState.INITIALIZING
    severity: HazardSeverity
    affected_nodes: list[str] = Field(default_factory=list)
    affected_zones: list[str] = Field(default_factory=list)
    propagation_speed_ms: float = Field(default=1.0, ge=0.0)
    wind_speed_ms: float = Field(default=0.0, ge=0.0)
    wind_direction_deg: float = Field(default=0.0, ge=0.0, le=360.0)
    model_type: PropagationModelType = PropagationModelType.GRAPH_DIFFUSION
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    started_at: str = Field(default_factory=_now_iso)
    updated_at: str = Field(default_factory=_now_iso)
    context: dict[str, Any] = Field(default_factory=dict)
    
    @computed_field
    def is_critical(self) -> bool:
        return self.severity in (HazardSeverity.CRITICAL, HazardSeverity.CATASTROPHIC)
        
    @computed_field
    def affected_count(self) -> int:
        return len(self.affected_nodes)

class PropagationTimeline(BaseModel):
    model_config = ConfigDict(frozen=True)
    timeline_id: str = Field(default_factory=_uuid)
    propagation_id: str
    entries: list[dict[str, Any]] = Field(default_factory=list)
    start_time: str = Field(default_factory=_now_iso)
    latest_time: str = Field(default_factory=_now_iso)
    total_steps: int = 0
    
    @computed_field
    def duration_minutes(self) -> int:
        st = datetime.fromisoformat(self.start_time.replace('Z', '+00:00'))
        lt = datetime.fromisoformat(self.latest_time.replace('Z', '+00:00'))
        return max(0, int((lt - st).total_seconds() / 60))

class PropagationForecast(BaseModel):
    model_config = ConfigDict(frozen=True)
    forecast_id: str = Field(default_factory=_uuid)
    propagation_id: str
    hazard_type: HazardType
    source_node_id: str
    time_horizons: dict[str, dict[str, Any]] = Field(default_factory=dict)
    peak_intensity_at_horizon: dict[str, float] = Field(default_factory=dict)
    containment_probability_at_horizon: dict[str, float] = Field(default_factory=dict)
    generated_at: str = Field(default_factory=_now_iso)
    
    @computed_field
    def worst_horizon(self) -> str:
        if not self.peak_intensity_at_horizon:
            return "unknown"
        return max(self.peak_intensity_at_horizon.items(), key=lambda x: x[1])[0]

class ExposureZone(BaseModel):
    model_config = ConfigDict(frozen=True)
    zone_id: str
    zone_name: str = ""
    exposure_level: ExposureLevel
    exposure_score: float = Field(default=0.0, ge=0.0, le=1.0)
    worker_count_at_risk: int = Field(default=0, ge=0)
    equipment_count_at_risk: int = Field(default=0, ge=0)
    concentration_ppm: float = Field(default=0.0, ge=0.0)
    temperature_celsius: float = 25.0
    time_to_unsafe_minutes: float | None = None
    ppe_adequacy_score: float = Field(default=1.0, ge=0.0, le=1.0)
    hazard_types_present: list[str] = Field(default_factory=list)

class ExposurePath(BaseModel):
    model_config = ConfigDict(frozen=True)
    path_id: str = Field(default_factory=_uuid)
    source_node_id: str
    target_node_id: str
    path_nodes: list[str] = Field(default_factory=list)
    path_length_meters: float = Field(default=0.0, ge=0.0)
    cumulative_exposure_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exposure_level: ExposureLevel
    time_to_reach_minutes: float = Field(default=0.0, ge=0.0)
    is_evacuation_safe: bool = True

class ExposureAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)
    assessment_id: str = Field(default_factory=_uuid)
    propagation_id: str
    exposed_zones: list[ExposureZone] = Field(default_factory=list)
    exposed_worker_ids: list[str] = Field(default_factory=list)
    exposed_equipment_ids: list[str] = Field(default_factory=list)
    exposure_paths: list[ExposurePath] = Field(default_factory=list)
    max_exposure_level: ExposureLevel = ExposureLevel.NONE
    overall_exposure_score: float = Field(default=0.0, ge=0.0, le=1.0)
    workers_requiring_evacuation: int = Field(default=0, ge=0)
    workers_in_lethal_zone: int = Field(default=0, ge=0)
    time_to_critical_exposure_minutes: float | None = None
    graphrag_citations: list[str] = Field(default_factory=list)
    risk_references: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=_now_iso)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)

class ContainmentBarrier(BaseModel):
    model_config = ConfigDict(frozen=True)
    barrier_id: str = Field(default_factory=_uuid)
    barrier_type: BarrierType
    zone_id: str | None = None
    equipment_id: str | None = None
    location_description: str = ""
    is_active: bool = True
    resistance_factor: float = Field(default=0.7, ge=0.0, le=1.0)
    deployment_time_minutes: float = Field(default=5.0, ge=0.0)
    operator_required: bool = True
    status: ContainmentStatus = ContainmentStatus.NOT_STARTED

class ContainmentPlan(BaseModel):
    model_config = ConfigDict(frozen=True)
    plan_id: str = Field(default_factory=_uuid)
    propagation_id: str
    hazard_type: HazardType
    status: ContainmentStatus = ContainmentStatus.PLANNING
    actions: list[dict[str, Any]] = Field(default_factory=list)
    barriers: list[ContainmentBarrier] = Field(default_factory=list)
    isolation_zones: list[str] = Field(default_factory=list)
    shutdown_equipment: list[str] = Field(default_factory=list)
    estimated_containment_time_minutes: float = Field(default=30.0, ge=0.0)
    estimated_effectiveness: float = Field(default=0.8, ge=0.0, le=1.0)
    graphrag_citations: list[str] = Field(default_factory=list)
    kg_node_refs: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=_now_iso)
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    
    @computed_field
    def priority_actions(self) -> list[dict]:
        return self.actions[:3]
        
    @computed_field
    def requires_emergency_services(self) -> bool:
        return any(a.get("type") == "EMERGENCY_SERVICES" for a in self.actions)

class CascadeFailure(BaseModel):
    model_config = ConfigDict(frozen=True)
    cascade_id: str = Field(default_factory=_uuid)
    trigger_hazard_id: str
    trigger_node_id: str
    cascade_type: str
    trigger_hazard_type: HazardType
    resulting_hazard_type: HazardType
    probability: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    time_to_cascade_minutes: float = Field(default=5.0, ge=0.0)
    affected_nodes: list[str] = Field(default_factory=list)
    cascade_chain: list[dict[str, Any]] = Field(default_factory=list)
    status: CascadeStatus = CascadeStatus.POTENTIAL
    detected_at: str = Field(default_factory=_now_iso)
    
    @computed_field
    def is_high_probability(self) -> bool:
        return self.probability > 0.5

class DominoEffect(BaseModel):
    model_config = ConfigDict(frozen=True)
    domino_id: str = Field(default_factory=_uuid)
    propagation_id: str
    stages: list[CascadeFailure] = Field(default_factory=list)
    worst_resulting_hazard: HazardType | None = None
    estimated_impact_radius_meters: float = Field(default=0.0, ge=0.0)
    affected_zone_ids: list[str] = Field(default_factory=list)
    affected_worker_count: int = Field(default=0, ge=0)
    detected_at: str = Field(default_factory=_now_iso)
    
    @computed_field
    def total_stages(self) -> int:
        return len(self.stages)
        
    @computed_field
    def total_cascade_probability(self) -> float:
        if not self.stages:
            return 0.0
        prob = 1.0
        for stage in self.stages:
            prob *= stage.probability
        return prob
        
    @computed_field
    def is_catastrophic(self) -> bool:
        return self.total_cascade_probability > 0.3 and self.total_stages >= 3

class CriticalAsset(BaseModel):
    model_config = ConfigDict(frozen=True)
    asset_id: str
    asset_type: str
    label: str
    zone_id: str | None = None
    criticality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    dependency_count: int = Field(default=0, ge=0)
    failure_impact_score: float = Field(default=0.0, ge=0.0, le=1.0)
    hazard_vulnerability: dict[str, float] = Field(default_factory=dict)
    is_single_point_of_failure: bool = False
    redundancy_level: int = Field(default=0, ge=0)
    
    @computed_field
    def overall_risk(self) -> float:
        return min(1.0, self.criticality_score * self.failure_impact_score)

class HazardScenario(BaseModel):
    model_config = ConfigDict(frozen=True)
    scenario_id: str = Field(default_factory=_uuid)
    scenario_name: str
    hazard_type: HazardType
    source_node_id: str
    initial_intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    wind_speed_ms: float = Field(default=0.0, ge=0.0)
    wind_direction_deg: float = Field(default=0.0, ge=0.0, le=360.0)
    containment_active: bool = False
    barriers_active: list[str] = Field(default_factory=list)
    modified_conditions: dict[str, Any] = Field(default_factory=dict)
    description: str = ""
    created_at: str = Field(default_factory=_now_iso)

class PropagationSimulation(BaseModel):
    model_config = ConfigDict(frozen=True)
    simulation_id: str = Field(default_factory=_uuid)
    scenario: HazardScenario
    status: SimulationStatus = SimulationStatus.PENDING
    result_nodes: dict[str, dict[str, Any]] = Field(default_factory=dict)
    containment_effectiveness: float = Field(default=0.0, ge=0.0, le=1.0)
    peak_affected_workers: int = Field(default=0, ge=0)
    peak_affected_zones: int = Field(default=0, ge=0)
    evacuation_required_zones: list[str] = Field(default_factory=list)
    simulation_time_steps: int = Field(default=0, ge=0)
    time_horizon_minutes: int = Field(default=60, ge=0)
    started_at: str = Field(default_factory=_now_iso)
    completed_at: str | None = None
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    
    @computed_field
    def is_complete(self) -> bool:
        return self.status == SimulationStatus.COMPLETED

class ImpactAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)
    assessment_id: str = Field(default_factory=_uuid)
    propagation_id: str
    affected_worker_count: int = Field(default=0, ge=0)
    workers_in_danger: int = Field(default=0, ge=0)
    workers_requiring_evacuation: int = Field(default=0, ge=0)
    affected_equipment_count: int = Field(default=0, ge=0)
    critical_equipment_affected: int = Field(default=0, ge=0)
    affected_zone_count: int = Field(default=0, ge=0)
    production_impact_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    environmental_impact_score: float = Field(default=0.0, ge=0.0, le=1.0)
    economic_impact_score: float = Field(default=0.0, ge=0.0)
    estimated_recovery_hours: float = Field(default=0.0, ge=0.0)
    severity: HazardSeverity
    graphrag_citations: list[str] = Field(default_factory=list)
    risk_references: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=_now_iso)
    
    @computed_field
    def requires_immediate_action(self) -> bool:
        return self.severity in (HazardSeverity.CRITICAL, HazardSeverity.CATASTROPHIC) or self.workers_in_danger > 0

class EvacuationRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)
    recommendation_id: str = Field(default_factory=_uuid)
    propagation_id: str
    evacuation_status: EvacuationStatus
    zones_to_evacuate: list[str] = Field(default_factory=list)
    zones_to_shelter_in_place: list[str] = Field(default_factory=list)
    safe_paths: list[ExposurePath] = Field(default_factory=list)
    blocked_paths: list[ExposurePath] = Field(default_factory=list)
    assembly_points: list[dict[str, Any]] = Field(default_factory=list)
    priority_workers: list[str] = Field(default_factory=list)
    estimated_evacuation_time_minutes: float = Field(default=15.0, ge=0.0)
    worker_count_to_evacuate: int = Field(default=0, ge=0)
    graphrag_citations: list[str] = Field(default_factory=list)
    kg_node_refs: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=_now_iso)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    
    @computed_field
    def is_urgent(self) -> bool:
        return self.evacuation_status == EvacuationStatus.MANDATORY

class PropagationRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)
    recommendation_id: str = Field(default_factory=_uuid)
    propagation_id: str
    recommendation_type: HazardRecommendationType
    priority: str = "HIGH"
    title: str
    description: str
    rationale: str
    target_zones: list[str] = Field(default_factory=list)
    target_equipment: list[str] = Field(default_factory=list)
    estimated_effectiveness: float = Field(default=0.7, ge=0.0, le=1.0)
    time_to_implement_minutes: float = Field(default=10.0, ge=0.0)
    operators_required: int = Field(default=1, ge=0)
    resources: list[str] = Field(default_factory=list)
    graphrag_citations: list[str] = Field(default_factory=list)
    kg_node_refs: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=_now_iso)
    
    @computed_field
    def is_immediate(self) -> bool:
        return self.priority == "IMMEDIATE"

class HazardPropagationResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    result_id: str = Field(default_factory=_uuid)
    propagation_id: str
    hazard_type: HazardType
    propagation: HazardPropagation
    timeline: PropagationTimeline | None = None
    forecast: PropagationForecast | None = None
    exposure_assessment: ExposureAssessment | None = None
    impact_assessment: ImpactAssessment | None = None
    containment_plan: ContainmentPlan | None = None
    evacuation_recommendation: EvacuationRecommendation | None = None
    domino_effect: DominoEffect | None = None
    recommendations: list[PropagationRecommendation] = Field(default_factory=list)
    graphrag_citations: list[str] = Field(default_factory=list)
    kg_traversal_path: list[str] = Field(default_factory=list)
    risk_references: list[str] = Field(default_factory=list)
    forecast_references: list[str] = Field(default_factory=list)
    rca_references: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    model_type: PropagationModelType = PropagationModelType.GRAPH_DIFFUSION
    generated_at: str = Field(default_factory=_now_iso)
    latency_ms: float = Field(default=0.0, ge=0.0)
    
    @computed_field
    def requires_immediate_action(self) -> bool:
        return self.propagation.severity in (HazardSeverity.CRITICAL, HazardSeverity.CATASTROPHIC)
        
    @computed_field
    def overall_severity(self) -> HazardSeverity:
        return self.propagation.severity
