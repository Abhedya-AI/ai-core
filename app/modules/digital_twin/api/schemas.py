from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any

class InitializeTwinRequest(BaseModel):
    plant_id: str
    plant_name: str
    sync_mode: str = "REAL_TIME"
    description: str = ""

class SynchronizeRequest(BaseModel):
    sources: Optional[List[str]] = None
    context: Dict[str, Any] = {}

class GetStateRequest(BaseModel):
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None

class OverrideStateRequest(BaseModel):
    entity_id: str
    entity_type: str
    overrides: Dict[str, Any]
    reason: str

class CreateSnapshotRequest(BaseModel):
    description: str
    created_by: str = "system"

class RunSimulationRequest(BaseModel):
    simulation_type: str
    parameters: Dict[str, Any]
    title: str
    description: str = ""

class GenerateScenariosRequest(BaseModel):
    entity_id: str
    entity_type: str
    context: Dict[str, Any] = {}

class CompareScenariosRequest(BaseModel):
    scenario_ids: List[str]

class RunOptimizationRequest(BaseModel):
    target: str
    constraints: Dict[str, Any] = {}

class StartReplayRequest(BaseModel):
    replay_by: str
    start_timestamp: str
    end_timestamp: str
    speed_multiplier: float = 1.0

class ControlReplayRequest(BaseModel):
    action: str
    speed_multiplier: Optional[float] = None
    target_timestamp: Optional[str] = None

class GeneratePlanRequest(BaseModel):
    plan_type: str
    entity_id: Optional[str] = None
    horizon_days: int = 30
    context: Dict[str, Any] = {}

class TwinResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    twin_id: str
    plant_id: str
    plant_name: str
    status: str
    sync_mode: str
    current_version: int
    is_active: bool
    is_synchronized: bool
    created_at: str
    updated_at: str

class TwinHealthResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    twin_id: str
    overall_status: str
    active_simulations: int
    entity_count: int
    last_full_sync_at: str
    is_operational: bool
    metrics: Dict[str, float]

class StateResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    entity_id: str
    entity_type: str
    health_score: float
    risk_score: float
    status: str
    updated_at: str
    requires_attention: bool

class SnapshotResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    snapshot_id: str
    twin_id: str
    version_number: int
    total_entities: int
    created_at: str
    description: str
    age_seconds: int

class SyncStatusResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    source: str
    status: str
    last_sync_at: str
    failure_count: int
    is_healthy: bool
    latency_ms: float

class SimulationResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    simulation_id: str
    twin_id: str
    simulation_type: str
    status: str
    title: str
    confidence: float
    latency_ms: float
    created_at: str

class ScenarioResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    scenario_id: str
    twin_id: str
    scenario_type: str
    title: str
    probability: float
    confidence: float
    risk_delta: float
    created_at: str

class OptimizationResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    optimization_id: str
    twin_id: str
    target: str
    status: str
    improvement_score: float
    latency_ms: float
    created_at: str

class ReplayResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    replay_id: str
    twin_id: str
    status: str
    replay_by: str
    progress_pct: float
    speed_multiplier: float
    created_at: str

class PlanResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    plan_id: str
    twin_id: str
    plan_type: str
    entity_id: Optional[str]
    confidence: float
    created_at: str

class AnalyticsResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    overall_health_score: float
    zones_healthy: int
    zones_degraded: int
    equipment_healthy: int
    workers_safe: int
    active_hazards: int

class VersionResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    version_id: str
    twin_id: str
    version_number: int
    created_at: str
    description: str

class ExplainResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    entity_id: str
    entity_type: str
    current_state: Dict[str, Any]
    explanation: str
    graphrag_citations: List[str]
    recommendations: List[str]
    confidence: float
