from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class PropagationRequest:
    hazard_type: str
    source_node_id: str
    initial_intensity: float
    nodes: dict[str, Any] = field(default_factory=dict)
    edges: list[dict[str, Any]] = field(default_factory=list)
    wind_speed_ms: float = 0.0
    wind_direction_deg: float = 0.0
    time_steps: int = 60
    context: dict[str, Any] = field(default_factory=dict)

@dataclass
class ExposureRequest:
    propagation_id: str
    hazard_type: str
    affected_nodes: dict[str, Any]
    worker_ids: list[str] = field(default_factory=list)
    zone_ids: list[str] = field(default_factory=list)
    equipment_ids: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

@dataclass
class ContainmentRequest:
    propagation_id: str
    hazard_type: str
    source_node_id: str
    affected_nodes: dict[str, Any]
    severity: str
    context: dict[str, Any] = field(default_factory=dict)

@dataclass
class EvacuationRequest:
    propagation_id: str
    zone_ids: list[str]
    worker_ids: list[str]
    hazard_intensities: dict[str, float]
    context: dict[str, Any] = field(default_factory=dict)

@dataclass
class SimulationRequest:
    scenario_name: str
    hazard_type: str
    source_node_id: str
    initial_intensity: float
    time_horizon_minutes: int = 60
    containment_active: bool = False
    modified_conditions: dict[str, Any] = field(default_factory=dict)
