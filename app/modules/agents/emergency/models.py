"""models.py — Emergency Response Intelligence Agent Domain Models & DTOs."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.modules.agents.core.agent_result import AgentResult


class PriorityLevel(str, Enum):
    """Emergency response priority levels."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EmergencyAction(BaseModel):
    """Dependency-aware emergency action item."""

    step_id: int
    action_type: str = Field(..., description="e.g. SHUT_VALVE, TRIGGER_ALARM, EVACUATE, DISPATCH_TEAM")
    description: str
    target_entity: str
    priority: PriorityLevel = PriorityLevel.HIGH
    dependencies: list[int] = Field(default_factory=list, description="Step IDs required before this action")
    estimated_duration_min: float = 2.0


class EvacuationRoute(BaseModel):
    """Dynamic evacuation path for a specific zone."""

    zone_id: str
    occupant_count: int = 0
    recommended_exit: str
    path: list[str] = Field(default_factory=list)
    blocked_exits: list[str] = Field(default_factory=list)
    estimated_evacuation_min: float = 4.0
    hazard_avoided: bool = True


class ResourceAssignment(BaseModel):
    """Responder or equipment allocation item."""

    resource_id: str
    resource_type: str = Field(..., description="FIRE_TEAM, MEDICAL_TEAM, HAZMAT_TEAM, MAINTENANCE_CREW")
    assigned_zone: str
    priority: int = 1
    eta_minutes: float = 2.0
    status: str = "DISPATCHED"


class IncidentState(BaseModel):
    """Aggregated operational incident state from multi-agent context."""

    incident_id: str
    severity: str = "CRITICAL"
    affected_zone: str = "ZONE-B"
    affected_workers_count: int = 12
    active_hazards: list[str] = Field(default_factory=list)
    blocked_exits: list[str] = Field(default_factory=list)
    risk_level: str = "CRITICAL"
    prediction_time_horizon_min: float = 15.0


class SituationModel(BaseModel):
    """Shared operational picture driving downstream emergency planning."""

    zone_id: str
    occupants: int
    active_hazards: list[str]
    accessible_exits: list[str]
    hazard_spread_risk: str
    overall_threat_score: float = Field(default=88.5, ge=0.0, le=100.0)


class EmergencyPlan(BaseModel):
    """Ordered dependency-aware emergency execution plan."""

    plan_id: str
    target_zone: str
    actions: list[EmergencyAction] = Field(default_factory=list)
    evacuation_routes: list[EvacuationRoute] = Field(default_factory=list)
    resource_assignments: list[ResourceAssignment] = Field(default_factory=list)
    overall_priority: PriorityLevel = PriorityLevel.CRITICAL
    is_replanned: bool = False


class EmergencyAgentResult(AgentResult):
    """Domain-extended result returned by Emergency Response Intelligence Agent."""

    incident_state: IncidentState = Field(default_factory=IncidentState)
    situation_model: SituationModel = Field(default_factory=SituationModel)
    emergency_plan: EmergencyPlan = Field(default_factory=EmergencyPlan)
    evacuation_routes: list[EvacuationRoute] = Field(default_factory=list)
    resource_assignments: list[ResourceAssignment] = Field(default_factory=list)
    categorized_actions: dict[str, list[str]] = Field(default_factory=dict)
