from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, ConfigDict


class ForecastRequest(BaseModel):
    entity_id: str
    entity_type: str = "EQUIPMENT"  # EQUIPMENT, WORKER, ZONE, PLANT, RESOURCE
    forecast_types: list[str] = Field(default_factory=list)  # empty = all applicable
    horizons: list[str] = Field(default_factory=lambda: ["1h", "6h", "24h"])
    context: dict[str, Any] = Field(default_factory=dict)


class EquipmentForecastRequest(BaseModel):
    equipment_id: str
    current_health: float = Field(default=1.0, ge=0.0, le=1.0)
    sensor_trends: list[float] = Field(default_factory=list)
    maintenance_history: list[dict[str, Any]] = Field(default_factory=list)
    horizon_hours: int = Field(default=24, ge=1, le=720)
    context: dict[str, Any] = Field(default_factory=dict)


class WorkerForecastRequest(BaseModel):
    worker_id: str
    worker_count: int = Field(default=1, ge=1)
    current_zone_id: str = ""
    current_hour: int = Field(default=0, ge=0, le=23)
    horizon_hours: int = Field(default=24, ge=1, le=168)
    context: dict[str, Any] = Field(default_factory=dict)


class ZoneForecastRequest(BaseModel):
    zone_id: str
    zone_name: str = ""
    worker_count: int = Field(default=0, ge=0)
    equipment_ids: list[str] = Field(default_factory=list)
    sensor_data: dict[str, Any] = Field(default_factory=dict)
    horizon_hours: int = Field(default=24, ge=1, le=720)
    context: dict[str, Any] = Field(default_factory=dict)


class PlantForecastRequest(BaseModel):
    plant_id: str
    plant_name: str = ""
    zone_ids: list[str] = Field(default_factory=list)
    equipment_ids: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class ResourceForecastRequest(BaseModel):
    worker_count: int = Field(default=10, ge=0)
    equipment_ids: list[str] = Field(default_factory=list)
    utilization_data: dict[str, float] = Field(default_factory=dict)
    health_scores: dict[str, float] = Field(default_factory=dict)
    horizon_hours: int = Field(default=24, ge=1, le=720)
    context: dict[str, Any] = Field(default_factory=dict)


class MaintenanceForecastRequest(BaseModel):
    equipment_id: str
    equipment_type: str = ""
    current_health: float = Field(default=1.0, ge=0.0, le=1.0)
    sensor_trends: list[float] = Field(default_factory=list)
    maintenance_history: list[dict[str, Any]] = Field(default_factory=list)
    horizon_hours: int = Field(default=168, ge=1, le=8760)
    context: dict[str, Any] = Field(default_factory=dict)


class EnvironmentForecastRequest(BaseModel):
    zone_id: str
    current_temperature: float = Field(default=25.0)
    current_humidity: float = Field(default=50.0, ge=0.0, le=100.0)
    current_gas_concentration: float = Field(default=0.0, ge=0.0)
    current_aqi: float = Field(default=50.0, ge=0.0)
    current_dust_ppm: float = Field(default=0.0, ge=0.0)
    current_smoke_ppm: float = Field(default=0.0, ge=0.0)
    equipment_heat_watts: float = Field(default=0.0, ge=0.0)
    horizon_hours: int = Field(default=24, ge=1, le=720)
    context: dict[str, Any] = Field(default_factory=dict)


class ScenarioRequest(BaseModel):
    entity_id: str
    forecast_type: str = "EQUIPMENT_HEALTH"
    horizon: str = "24h"
    base_forecast_value: float = Field(default=0.5, ge=0.0, le=1.0)
    base_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    context: dict[str, Any] = Field(default_factory=dict)


class CompareForecastRequest(BaseModel):
    entity_id: str
    forecast_type: str
    horizon: str = "24h"
    context: dict[str, Any] = Field(default_factory=dict)


class ExplainRequest(BaseModel):
    forecast_id: str
    include_graphrag: bool = True
    include_kg_paths: bool = True


class ForecastListFilter(BaseModel):
    entity_id: str | None = None
    forecast_type: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = "generated_at"
    sort_order: str = "desc"


# Response schemas
class ForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")


class EquipmentForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")


class WorkerForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")


class ZoneForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")


class PlantForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")


class ResourceForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")


class MaintenanceForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")


class EnvironmentalForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")


class ScenarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")


class ComparisonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")


class ForecastExplainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")


class ForecastAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")


class ForecastHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")


class PaginatedForecastHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")
    total: int
    page: int
    page_size: int
    items: list[ForecastHistoryItem]
