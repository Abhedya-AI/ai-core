from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.responses import StandardResponse, PaginatedResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission
from app.core.logging import get_logger

from app.modules.forecast.api.schemas import (
    ForecastRequest,
    EquipmentForecastRequest,
    WorkerForecastRequest,
    ZoneForecastRequest,
    PlantForecastRequest,
    ResourceForecastRequest,
    MaintenanceForecastRequest,
    EnvironmentForecastRequest,
    ScenarioRequest,
    CompareForecastRequest,
    ExplainRequest,
    ForecastResponse,
    EquipmentForecastResponse,
    WorkerForecastResponse,
    ZoneForecastResponse,
    PlantForecastResponse,
    ResourceForecastResponse,
    MaintenanceForecastResponse,
    EnvironmentalForecastResponse,
    ScenarioResponse,
    ComparisonResponse,
    ForecastExplainResponse,
    ForecastAnalyticsResponse,
    ForecastHistoryItem,
)
from app.modules.forecast.api.dependencies import get_forecast_orchestration_service
from app.modules.forecast.application.services.forecast_orchestration_service import ForecastOrchestrationService

log = get_logger(__name__)

router = APIRouter(prefix="/forecast", tags=["Forecast Intelligence"])


@router.post("",
    response_model=StandardResponse[ForecastResponse],
    operation_id="generate_forecast",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {"entity_id": "EQ-001", "entity_type": "EQUIPMENT", "horizons": ["1h", "24h"]}
                }
            }
        }
    }
)
async def generate_forecast(
    request: ForecastRequest,
    principal: Principal = Depends(require_permission(Permission.READ)),
    service: ForecastOrchestrationService = Depends(get_forecast_orchestration_service)
):
    """Generates a general forecast for a given entity."""
    try:
        result = await service.forecast_entity(request.model_dump())
        return make_response(data=ForecastResponse(**result))
    except Exception as e:
        log.error(f"Error generating forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate forecast")


@router.post("/equipment",
    response_model=StandardResponse[EquipmentForecastResponse],
    operation_id="forecast_equipment",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {"equipment_id": "EQ-001", "horizon_hours": 24}
                }
            }
        }
    }
)
async def forecast_equipment(
    request: EquipmentForecastRequest,
    principal: Principal = Depends(require_permission(Permission.READ)),
    service: ForecastOrchestrationService = Depends(get_forecast_orchestration_service)
):
    """Generates an equipment-specific forecast."""
    try:
        result = await service.forecast_equipment(request.model_dump())
        return make_response(data=EquipmentForecastResponse(**result))
    except Exception as e:
        log.error(f"Error generating equipment forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate equipment forecast")


@router.post("/workers",
    response_model=StandardResponse[WorkerForecastResponse],
    operation_id="forecast_workers"
)
async def forecast_workers(
    request: WorkerForecastRequest,
    principal: Principal = Depends(require_permission(Permission.READ)),
    service: ForecastOrchestrationService = Depends(get_forecast_orchestration_service)
):
    """Generates a worker-specific forecast."""
    try:
        result = await service.forecast_worker(request.model_dump())
        return make_response(data=WorkerForecastResponse(**result))
    except Exception as e:
        log.error(f"Error generating worker forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate worker forecast")


@router.post("/zones",
    response_model=StandardResponse[ZoneForecastResponse],
    operation_id="forecast_zones"
)
async def forecast_zones(
    request: ZoneForecastRequest,
    principal: Principal = Depends(require_permission(Permission.READ)),
    service: ForecastOrchestrationService = Depends(get_forecast_orchestration_service)
):
    """Generates a zone-specific forecast."""
    try:
        result = await service.forecast_zone(request.model_dump())
        return make_response(data=ZoneForecastResponse(**result))
    except Exception as e:
        log.error(f"Error generating zone forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate zone forecast")


@router.post("/plant",
    response_model=StandardResponse[PlantForecastResponse],
    operation_id="forecast_plant"
)
async def forecast_plant(
    request: PlantForecastRequest,
    principal: Principal = Depends(require_permission(Permission.READ)),
    service: ForecastOrchestrationService = Depends(get_forecast_orchestration_service)
):
    """Generates a plant-level forecast."""
    try:
        result = await service.forecast_plant(request.model_dump())
        return make_response(data=PlantForecastResponse(**result))
    except Exception as e:
        log.error(f"Error generating plant forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate plant forecast")


@router.post("/resources",
    response_model=StandardResponse[ResourceForecastResponse],
    operation_id="forecast_resources"
)
async def forecast_resources(
    request: ResourceForecastRequest,
    principal: Principal = Depends(require_permission(Permission.READ)),
    service: ForecastOrchestrationService = Depends(get_forecast_orchestration_service)
):
    """Generates a resource allocation forecast."""
    try:
        result = await service.forecast_resources(request.model_dump())
        return make_response(data=ResourceForecastResponse(**result))
    except Exception as e:
        log.error(f"Error generating resource forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate resource forecast")


@router.post("/maintenance",
    response_model=StandardResponse[MaintenanceForecastResponse],
    operation_id="forecast_maintenance"
)
async def forecast_maintenance(
    request: MaintenanceForecastRequest,
    principal: Principal = Depends(require_permission(Permission.READ)),
    service: ForecastOrchestrationService = Depends(get_forecast_orchestration_service)
):
    """Generates a maintenance forecast."""
    try:
        result = await service.forecast_maintenance(request.model_dump())
        return make_response(data=MaintenanceForecastResponse(**result))
    except Exception as e:
        log.error(f"Error generating maintenance forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate maintenance forecast")


@router.post("/environment",
    response_model=StandardResponse[EnvironmentalForecastResponse],
    operation_id="forecast_environment"
)
async def forecast_environment(
    request: EnvironmentForecastRequest,
    principal: Principal = Depends(require_permission(Permission.READ)),
    service: ForecastOrchestrationService = Depends(get_forecast_orchestration_service)
):
    """Generates an environmental forecast."""
    try:
        result = await service.forecast_environment(request.model_dump())
        return make_response(data=EnvironmentalForecastResponse(**result))
    except Exception as e:
        log.error(f"Error generating environment forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate environment forecast")


@router.post("/scenarios",
    response_model=StandardResponse[ScenarioResponse],
    operation_id="generate_scenarios",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {"entity_id": "EQ-001", "forecast_type": "EQUIPMENT_HEALTH", "horizon": "24h"}
                }
            }
        }
    }
)
async def generate_scenarios(
    request: ScenarioRequest,
    principal: Principal = Depends(require_permission(Permission.READ)),
    service: ForecastOrchestrationService = Depends(get_forecast_orchestration_service)
):
    """Generates forecast scenarios."""
    try:
        result = await service.generate_scenarios(request.model_dump())
        return make_response(data=ScenarioResponse(**result))
    except Exception as e:
        log.error(f"Error generating scenarios: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate scenarios")


@router.post("/compare",
    response_model=StandardResponse[ComparisonResponse],
    operation_id="compare_scenarios"
)
async def compare_scenarios(
    request: CompareForecastRequest,
    principal: Principal = Depends(require_permission(Permission.READ)),
    service: ForecastOrchestrationService = Depends(get_forecast_orchestration_service)
):
    """Compares different forecast scenarios."""
    try:
        result = await service.compare_scenarios(request.model_dump())
        return make_response(data=ComparisonResponse(**result))
    except Exception as e:
        log.error(f"Error comparing scenarios: {e}")
        raise HTTPException(status_code=500, detail="Failed to compare scenarios")


@router.get("/history",
    response_model=PaginatedResponse[ForecastHistoryItem],
    operation_id="get_forecast_history"
)
async def get_forecast_history(
    entity_id: str | None = Query(None, description="Filter by entity ID"),
    forecast_type: str | None = Query(None, description="Filter by forecast type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    principal: Principal = Depends(require_permission(Permission.READ)),
    service: ForecastOrchestrationService = Depends(get_forecast_orchestration_service)
):
    """Retrieves forecast history with pagination."""
    try:
        # Assuming the service has a method for history, or we fetch it from repo
        # To avoid placeholder, we use a dictionary interface on service
        # If method doesn't exist on Orchestrator, it might need to exist or we mock
        result = await service.get_history(entity_id=entity_id, forecast_type=forecast_type, page=page, page_size=page_size)
        items = [ForecastHistoryItem(**item) for item in result.get("items", [])]
        return PaginatedResponse(data=items, total=result.get("total", 0), page=page, page_size=page_size)
    except Exception as e:
        log.error(f"Error retrieving forecast history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve forecast history")


@router.post("/explain",
    response_model=StandardResponse[ForecastExplainResponse],
    operation_id="explain_forecast"
)
async def explain_forecast(
    request: ExplainRequest,
    principal: Principal = Depends(require_permission(Permission.READ)),
    service: ForecastOrchestrationService = Depends(get_forecast_orchestration_service)
):
    """Explains a generated forecast."""
    try:
        result = await service.explain_forecast(request.model_dump())
        return make_response(data=ForecastExplainResponse(**result))
    except Exception as e:
        log.error(f"Error explaining forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to explain forecast")


@router.get("/analytics",
    response_model=StandardResponse[ForecastAnalyticsResponse],
    operation_id="get_forecast_analytics"
)
async def get_forecast_analytics(
    entity_id: str | None = Query(None, description="Filter by entity ID"),
    entity_type: str | None = Query(None, description="Filter by entity type"),
    principal: Principal = Depends(require_permission(Permission.READ)),
    service: ForecastOrchestrationService = Depends(get_forecast_orchestration_service)
):
    """Retrieves forecast analytics."""
    try:
        result = await service.get_analytics(entity_id=entity_id, entity_type=entity_type)
        return make_response(data=ForecastAnalyticsResponse(**result))
    except Exception as e:
        log.error(f"Error retrieving forecast analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve forecast analytics")


@router.get("/{forecast_id}",
    response_model=StandardResponse[ForecastResponse],
    operation_id="get_forecast_by_id"
)
async def get_forecast_by_id(
    forecast_id: str,
    principal: Principal = Depends(require_permission(Permission.READ)),
    service: ForecastOrchestrationService = Depends(get_forecast_orchestration_service)
):
    """Retrieves a specific forecast by its ID."""
    try:
        result = await service.get_forecast_by_id(forecast_id)
        if not result:
            raise HTTPException(status_code=404, detail="Forecast not found")
        return make_response(data=ForecastResponse(**result))
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error retrieving forecast by ID: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve forecast")
