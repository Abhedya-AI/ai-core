from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.modules.digital_twin.domain.enums import (
    TwinStatus, SyncMode, SyncSource, SyncStatus, SimulationType,
    SimulationStatus, ScenarioType, OptimizationTarget, OptimizationStatus,
    ReplayStatus, PlanType, TwinEventType, HealthStatus, EntityType,
    StateTransitionReason, ConfidenceLevel
)

def _now_iso() -> str: 
    return datetime.now(timezone.utc).isoformat()

def _uuid() -> str: 
    return str(uuid.uuid4())

class TwinMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)
    sync_latency_ms: float
    simulation_latency_ms: float
    optimization_latency_ms: float
    replay_latency_ms: float
    snapshot_latency_ms: float
    kg_sync_latency_ms: float
    graphrag_latency_ms: float
    total_syncs: int
    failed_syncs: int
    total_simulations: int
    total_scenarios: int
    total_optimizations: int
    total_replays: int
    uptime_seconds: float
    last_updated: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def sync_success_rate(self) -> float:
        if self.total_syncs == 0:
            return 1.0
        return max(0.0, 1.0 - (self.failed_syncs / self.total_syncs))

    @computed_field
    @property
    def overall_health(self) -> HealthStatus:
        return HealthStatus.from_score(self.sync_success_rate)


class SyncStatusRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    source: SyncSource
    status: SyncStatus
    last_sync_at: str | None
    last_success_at: str | None
    error_message: str | None
    sync_count: int
    failure_count: int
    latency_ms: float

    @computed_field
    @property
    def is_healthy(self) -> bool:
        return self.status == SyncStatus.COMPLETED and self.failure_count < 3


class TwinHealth(BaseModel):
    model_config = ConfigDict(frozen=True)
    twin_id: str
    overall_status: HealthStatus
    sync_statuses: list[SyncStatusRecord]
    active_simulations: int
    active_replays: int
    entity_count: int
    snapshot_count: int
    last_full_sync_at: str | None
    last_snapshot_at: str | None
    metrics: TwinMetrics
    generated_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def is_operational(self) -> bool:
        return self.overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]


class TwinVersion(BaseModel):
    model_config = ConfigDict(frozen=True)
    version_id: str = Field(default_factory=_uuid)
    twin_id: str
    version_number: int
    description: str
    snapshot_id: str | None
    created_at: str = Field(default_factory=_now_iso)
    created_by: str
    change_summary: dict[str, Any]


class TwinState(BaseModel):
    model_config = ConfigDict(frozen=True)
    state_id: str = Field(default_factory=_uuid)
    entity_id: str
    entity_type: EntityType
    status: str
    health_score: float
    risk_score: float
    last_sensor_reading: dict[str, Any]
    last_vision_reading: dict[str, Any]
    risk_data: dict[str, Any]
    forecast_data: dict[str, Any]
    hazard_data: dict[str, Any]
    metadata: dict[str, Any]
    version: int
    transition_reason: StateTransitionReason
    previous_state_id: str | None
    updated_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def health_status(self) -> HealthStatus:
        return HealthStatus.from_score(self.health_score)

    @computed_field
    @property
    def requires_attention(self) -> bool:
        return self.risk_score > 0.6 or self.health_score < 0.4


class TwinSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    snapshot_id: str = Field(default_factory=_uuid)
    twin_id: str
    version_number: int
    plant_state: dict[str, Any]
    zone_states: dict[str, Any]
    equipment_states: dict[str, Any]
    worker_states: dict[str, Any]
    sensor_states: dict[str, Any]
    camera_states: dict[str, Any]
    hazard_states: dict[str, Any]
    resource_states: dict[str, Any]
    sync_statuses: list[SyncStatusRecord]
    metrics: TwinMetrics
    total_entities: int
    created_at: str = Field(default_factory=_now_iso)
    created_by: str
    description: str

    @computed_field
    @property
    def entity_count(self) -> int:
        return (len(self.zone_states) + len(self.equipment_states) + 
                len(self.worker_states) + len(self.sensor_states) + 
                len(self.camera_states) + len(self.hazard_states) + 
                len(self.resource_states) + (1 if self.plant_state else 0))

    @computed_field
    @property
    def age_seconds(self) -> float:
        try:
            created = datetime.fromisoformat(self.created_at)
            now = datetime.now(timezone.utc)
            return (now - created).total_seconds()
        except ValueError:
            return 0.0


class DigitalTwin(BaseModel):
    model_config = ConfigDict(frozen=True)
    twin_id: str = Field(default_factory=_uuid)
    plant_id: str
    plant_name: str
    status: TwinStatus
    sync_mode: SyncMode
    current_version: int
    latest_snapshot_id: str | None
    health: TwinHealth | None
    active_simulations: list[str]
    active_scenarios: list[str]
    active_replays: list[str]
    sync_sources: list[SyncSource]
    created_at: str = Field(default_factory=_now_iso)
    updated_at: str = Field(default_factory=_now_iso)
    description: str

    @computed_field
    @property
    def is_active(self) -> bool:
        return self.status == TwinStatus.ACTIVE

    @computed_field
    @property
    def is_synchronized(self) -> bool:
        return self.health is not None and self.health.is_operational


class SensorTwin(BaseModel):
    model_config = ConfigDict(frozen=True)
    sensor_id: str
    sensor_name: str
    sensor_type: str
    zone_id: str
    equipment_id: str | None
    current_value: float | None
    unit: str
    min_value: float
    max_value: float
    threshold_low: float
    threshold_high: float
    is_online: bool
    is_anomalous: bool
    last_reading_at: str | None
    reading_history: list[dict[str, Any]]
    health_score: float
    risk_contribution: float
    updated_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def is_in_threshold(self) -> bool:
        if self.current_value is None:
            return False
        return self.threshold_low <= self.current_value <= self.threshold_high

    @computed_field
    @property
    def normalized_value(self) -> float:
        if self.current_value is None or (self.max_value - self.min_value) == 0:
            return 0.0
        val = (self.current_value - self.min_value) / (self.max_value - self.min_value)
        return max(0.0, min(1.0, val))


class CameraTwin(BaseModel):
    model_config = ConfigDict(frozen=True)
    camera_id: str
    camera_name: str
    zone_id: str
    location: dict[str, float]
    is_online: bool
    is_recording: bool
    last_frame_at: str | None
    detected_workers: list[str]
    detected_violations: list[str]
    occupancy_count: int
    ppe_compliance_rate: float
    restricted_zone_violations: int
    fire_detection_active: bool
    smoke_detection_active: bool
    updated_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def has_active_alerts(self) -> bool:
        return len(self.detected_violations) > 0 or self.restricted_zone_violations > 0 or self.fire_detection_active or self.smoke_detection_active


class EquipmentTwin(BaseModel):
    model_config = ConfigDict(frozen=True)
    equipment_id: str
    equipment_name: str
    equipment_type: str
    zone_id: str
    floor_id: str
    building_id: str
    status: str
    health_score: float
    risk_score: float
    utilization_pct: float
    rul_hours: float | None
    last_maintenance_at: str | None
    next_maintenance_at: str | None
    maintenance_urgency: str
    anomalous_sensors: list[str]
    sensor_ids: list[str]
    dependency_ids: list[str]
    failure_probability: dict[str, float]
    current_load: float
    rated_capacity: float
    updated_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def is_critical(self) -> bool:
        return self.health_score < 0.3 or self.risk_score > 0.7

    @computed_field
    @property
    def capacity_utilization_pct(self) -> float:
        if self.rated_capacity <= 0:
            return 0.0
        return self.current_load / self.rated_capacity


class WorkerTwin(BaseModel):
    model_config = ConfigDict(frozen=True)
    worker_id: str
    worker_name: str
    worker_role: str
    current_zone_id: str
    previous_zone_id: str | None
    location: dict[str, float]
    safety_score: float
    exposure_risk_score: float
    fatigue_index: float
    ppe_compliant: bool
    ppe_items: list[str]
    hours_on_shift: float
    last_break_at: str | None
    emergency_contact: str
    certifications: list[str]
    active_tasks: list[str]
    updated_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def requires_evacuation(self) -> bool:
        return self.exposure_risk_score > 0.7 or self.safety_score < 0.3

    @computed_field
    @property
    def shift_health(self) -> str:
        if self.fatigue_index > 0.8:
            return "CRITICAL"
        if self.fatigue_index > 0.6:
            return "DEGRADED"
        return "HEALTHY"


class ZoneTwin(BaseModel):
    model_config = ConfigDict(frozen=True)
    zone_id: str
    zone_name: str
    zone_type: str
    floor_id: str
    building_id: str
    plant_id: str
    health_score: float
    risk_score: float
    hazard_probability: dict[str, float]
    worker_ids: list[str]
    equipment_ids: list[str]
    sensor_ids: list[str]
    camera_ids: list[str]
    occupancy: int
    max_occupancy: int
    environmental_data: dict[str, Any]
    is_restricted: bool
    is_hazard_active: bool
    evacuation_required: bool
    updated_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def occupancy_pct(self) -> float:
        if self.max_occupancy <= 0:
            return 0.0
        return self.occupancy / self.max_occupancy

    @computed_field
    @property
    def is_overcrowded(self) -> bool:
        return self.occupancy > self.max_occupancy

    @computed_field
    @property
    def overall_status(self) -> HealthStatus:
        return HealthStatus.from_score(self.health_score)


class FloorTwin(BaseModel):
    model_config = ConfigDict(frozen=True)
    floor_id: str
    floor_name: str
    floor_number: int
    building_id: str
    plant_id: str
    zone_ids: list[str]
    equipment_count: int
    worker_count: int
    health_score: float
    risk_score: float
    has_active_hazard: bool
    evacuation_required: bool
    updated_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def status(self) -> HealthStatus:
        return HealthStatus.from_score(self.health_score)


class BuildingTwin(BaseModel):
    model_config = ConfigDict(frozen=True)
    building_id: str
    building_name: str
    plant_id: str
    floor_ids: list[str]
    zone_ids: list[str]
    equipment_count: int
    worker_count: int
    health_score: float
    risk_score: float
    has_active_hazard: bool
    emergency_status: str
    updated_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def status(self) -> HealthStatus:
        return HealthStatus.from_score(self.health_score)


class PlantTwin(BaseModel):
    model_config = ConfigDict(frozen=True)
    plant_id: str
    plant_name: str
    twin_id: str
    building_ids: list[str]
    floor_ids: list[str]
    zone_ids: list[str]
    overall_health_score: float
    overall_risk_score: float
    operational_stability_score: float
    emergency_readiness_score: float
    compliance_score: float
    worker_count: int
    equipment_count: int
    sensor_count: int
    camera_count: int
    active_hazards: list[str]
    critical_zones: list[str]
    critical_equipment: list[str]
    updated_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def status(self) -> HealthStatus:
        return HealthStatus.from_score(self.overall_health_score)

    @computed_field
    @property
    def is_emergency_active(self) -> bool:
        return self.overall_risk_score > 0.8 or len(self.active_hazards) > 0


class HazardTwin(BaseModel):
    model_config = ConfigDict(frozen=True)
    hazard_id: str
    hazard_type: str
    source_zone_id: str
    affected_zones: list[str]
    propagation_state: str
    severity: str
    current_intensity: float
    containment_status: str
    affected_worker_count: int
    affected_equipment_count: int
    propagation_probability: dict[str, float]
    risk_score: float
    started_at: str
    last_updated: str = Field(default_factory=_now_iso)
    estimated_containment_at: str | None
    graphrag_citations: list[str]
    kg_node_id: str | None

    @computed_field
    @property
    def is_critical(self) -> bool:
        return self.severity in ["HIGH", "CRITICAL"] or self.current_intensity > 0.7

    @computed_field
    @property
    def is_contained(self) -> bool:
        return self.containment_status == "CONTAINED"


class ResourceTwin(BaseModel):
    model_config = ConfigDict(frozen=True)
    resource_id: str
    resource_name: str
    resource_type: str
    zone_id: str | None
    quantity_available: float
    quantity_total: float
    unit: str
    is_critical: bool
    last_replenished_at: str | None
    consumption_rate: float
    estimated_depletion_hours: float | None
    updated_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def availability_pct(self) -> float:
        if self.quantity_total <= 0:
            return 0.0
        return self.quantity_available / self.quantity_total

    @computed_field
    @property
    def is_depleted(self) -> bool:
        return self.quantity_available <= 0

    @computed_field
    @property
    def requires_replenishment(self) -> bool:
        return self.availability_pct < 0.2


class TwinEvent(BaseModel):
    model_config = ConfigDict(frozen=True)
    event_id: str = Field(default_factory=_uuid)
    twin_id: str
    event_type: TwinEventType
    entity_id: str | None
    entity_type: EntityType | None
    description: str
    severity: str
    old_state: dict[str, Any] | None
    new_state: dict[str, Any] | None
    source: SyncSource | None
    triggered_at: str = Field(default_factory=_now_iso)
    acknowledged: bool
    acknowledged_at: str | None
    metadata: dict[str, Any]

    @computed_field
    @property
    def age_seconds(self) -> float:
        try:
            triggered = datetime.fromisoformat(self.triggered_at)
            now = datetime.now(timezone.utc)
            return (now - triggered).total_seconds()
        except ValueError:
            return 0.0


class TwinSimulation(BaseModel):
    model_config = ConfigDict(frozen=True)
    simulation_id: str = Field(default_factory=_uuid)
    twin_id: str
    simulation_type: SimulationType
    status: SimulationStatus
    title: str
    description: str
    input_parameters: dict[str, Any]
    result: dict[str, Any] | None
    timeline: list[dict[str, Any]]
    assumptions: list[str]
    kg_paths: list[str]
    graphrag_citations: list[str]
    risk_references: list[str]
    forecast_references: list[str]
    hazard_references: list[str]
    confidence: float
    alternative_scenarios: list[str]
    recommended_actions: list[str]
    latency_ms: float
    created_at: str = Field(default_factory=_now_iso)
    completed_at: str | None

    @computed_field
    @property
    def is_complete(self) -> bool:
        return self.status in [SimulationStatus.COMPLETED, SimulationStatus.FAILED, SimulationStatus.CANCELLED]

    @computed_field
    @property
    def duration_seconds(self) -> float | None:
        if not self.completed_at:
            return None
        try:
            created = datetime.fromisoformat(self.created_at)
            completed = datetime.fromisoformat(self.completed_at)
            return (completed - created).total_seconds()
        except ValueError:
            return None


class TwinScenario(BaseModel):
    model_config = ConfigDict(frozen=True)
    scenario_id: str = Field(default_factory=_uuid)
    twin_id: str
    scenario_type: ScenarioType
    title: str
    description: str
    simulation_id: str | None
    predicted_outcome: dict[str, Any]
    probability: float
    confidence: float
    conditions: dict[str, Any]
    key_drivers: list[str]
    risk_delta: float
    health_delta: float
    graphrag_citations: list[str]
    created_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def confidence_level(self) -> ConfidenceLevel:
        return ConfidenceLevel.from_score(self.confidence)

    @computed_field
    @property
    def is_high_risk(self) -> bool:
        return self.risk_delta > 0.3


class TwinOptimization(BaseModel):
    model_config = ConfigDict(frozen=True)
    optimization_id: str = Field(default_factory=_uuid)
    twin_id: str
    target: OptimizationTarget
    status: OptimizationStatus
    title: str
    objective: str
    constraints: dict[str, Any]
    solution: dict[str, Any] | None
    improvement_score: float | None
    baseline_score: float
    optimized_score: float | None
    optimization_steps: list[dict[str, Any]]
    graphrag_citations: list[str]
    risk_references: list[str]
    reasoning: str
    recommended_actions: list[str]
    latency_ms: float
    created_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def improvement_pct(self) -> float | None:
        if self.baseline_score == 0 and self.optimized_score:
            return float('inf')
        if self.optimized_score is not None:
            return ((self.optimized_score - self.baseline_score) / abs(self.baseline_score)) * 100
        return None

    @computed_field
    @property
    def is_significant(self) -> bool:
        return (self.improvement_score or 0.0) > 0.1


class TwinReplay(BaseModel):
    model_config = ConfigDict(frozen=True)
    replay_id: str = Field(default_factory=_uuid)
    twin_id: str
    status: ReplayStatus
    title: str
    replay_by: str
    start_timestamp: str
    end_timestamp: str
    current_timestamp: str | None
    speed_multiplier: float
    total_frames: int
    current_frame: int
    snapshot_ids: list[str]
    events_replayed: list[str]
    created_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def progress_pct(self) -> float:
        if self.total_frames <= 0:
            return 0.0
        return (self.current_frame / self.total_frames) * 100

    @computed_field
    @property
    def duration_seconds(self) -> float:
        try:
            start = datetime.fromisoformat(self.start_timestamp)
            end = datetime.fromisoformat(self.end_timestamp)
            return (end - start).total_seconds()
        except ValueError:
            return 0.0


class TwinRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)
    recommendation_id: str = Field(default_factory=_uuid)
    twin_id: str
    entity_id: str
    entity_type: EntityType
    title: str
    description: str
    rationale: str
    priority: str
    recommendation_type: str
    estimated_impact: float
    graphrag_citations: list[str]
    kg_node_refs: list[str]
    risk_references: list[str]
    created_at: str = Field(default_factory=_now_iso)
    expires_at: str | None

    @computed_field
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        try:
            expires = datetime.fromisoformat(self.expires_at)
            now = datetime.now(timezone.utc)
            return now > expires
        except ValueError:
            return False

    @computed_field
    @property
    def is_high_priority(self) -> bool:
        return self.priority in ["IMMEDIATE", "URGENT"]
