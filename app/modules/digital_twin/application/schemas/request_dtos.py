from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Any

class TwinCreateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    plant_id: str
    name: str
    sync_mode: str = "REAL_TIME"
    description: str | None = None

class OptimizationRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    target: str
    constraints: dict[str, Any] = Field(default_factory=dict)
    
class SimulationRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    simulation_type: str
    parameters: dict[str, Any]
    
class PlanRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    plan_type: str
    horizon_days: int = 7
    context: dict[str, Any] = Field(default_factory=dict)
