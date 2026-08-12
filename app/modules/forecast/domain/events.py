from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _uuid() -> str:
    return str(uuid.uuid4())

class ForecastDomainEvent(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    event_id: str = Field(default_factory=_uuid)
    event_type: str = Field(default="ForecastDomainEvent")
    timestamp: str = Field(default_factory=_now_iso)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ForecastGenerated(ForecastDomainEvent):
    event_type: str = Field(default="ForecastGenerated")
    forecast_id: str
    entity_id: str
    forecast_type: str

class ScenarioGenerated(ForecastDomainEvent):
    event_type: str = Field(default="ScenarioGenerated")
    scenario_id: str
    entity_id: str
    forecast_type: str

class ForecastUpdated(ForecastDomainEvent):
    event_type: str = Field(default="ForecastUpdated")
    forecast_id: str
    entity_id: str
    updates: dict[str, Any]

class MaintenanceForecastCreated(ForecastDomainEvent):
    event_type: str = Field(default="MaintenanceForecastCreated")
    result_id: str
    equipment_id: str
    rul_hours: float | None

class ResourceForecastCreated(ForecastDomainEvent):
    event_type: str = Field(default="ResourceForecastCreated")
    result_id: str
    resource_type: str

class ForecastThresholdExceeded(ForecastDomainEvent):
    event_type: str = Field(default="ForecastThresholdExceeded")
    forecast_id: str
    metric_name: str
    value: float
    threshold: float

class ForecastCompleted(ForecastDomainEvent):
    event_type: str = Field(default="ForecastCompleted")
    result_id: str
    entity_id: str

FORECAST_EVENT_TOPICS = {
    "ForecastGenerated": "forecast.generated",
    "ScenarioGenerated": "forecast.scenario.generated",
    "ForecastUpdated": "forecast.updated",
    "MaintenanceForecastCreated": "forecast.maintenance.created",
    "ResourceForecastCreated": "forecast.resource.created",
    "ForecastThresholdExceeded": "forecast.threshold.exceeded",
    "ForecastCompleted": "forecast.completed",
}
