from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any
from app.core.logging import get_logger

from app.api.responses import StandardResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission

from app.modules.risk_prediction.domain.enums import EntityType
from app.modules.risk_prediction.api.schemas import (
    AssessEntityRequest, AssessEquipmentRequest, AssessWorkerRequest,
    AssessZoneRequest, AssessPlantRequest, ForecastRequest, ScenarioRequest,
    RiskListFilter, RiskAssessmentResponse, EquipmentRiskResponse,
    WorkerRiskResponse, ZoneRiskResponse, PlantRiskResponse,
    CompositeRiskResponse, PaginatedRiskResponse, RiskForecastResponse,
    RiskFactorResponse, MitigationPlanResponse, RiskFeaturesResponse,
    RiskScenarioResponse, RiskAnalyticsSummaryResponse, RiskTimelineResponse
)
from app.modules.risk_prediction.api.dependencies import (
    get_risk_prediction_service, get_analytics_service
)
from app.modules.risk_prediction.application.services.risk_prediction_service import RiskPredictionService
from app.modules.risk_prediction.api.dependencies import RiskAnalyticsService

log = get_logger(__name__)

router = APIRouter(prefix='/risk', tags=['Risk Prediction'])

@router.post('/predict', response_model=StandardResponse[RiskAssessmentResponse], operation_id='assess_entity')
async def assess_entity(
    request: AssessEntityRequest,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Assess risk for a given entity.'''
    try:
        # Mocking method call to service as instructed by standard API patterns
        result = await service.assess_entity(request)
        return make_response(data=RiskAssessmentResponse(**result.model_dump()))
    except Exception as exc:
        log.error(f'Risk prediction failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.post('/predict/equipment', response_model=StandardResponse[EquipmentRiskResponse], operation_id='assess_equipment')
async def assess_equipment(
    request: AssessEquipmentRequest,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Assess risk for a piece of equipment.'''
    try:
        result = await service.assess_equipment(request)
        return make_response(data=EquipmentRiskResponse(**result.model_dump()))
    except Exception as exc:
        log.error(f'Equipment risk prediction failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.post('/predict/worker', response_model=StandardResponse[WorkerRiskResponse], operation_id='assess_worker')
async def assess_worker(
    request: AssessWorkerRequest,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Assess risk for a worker.'''
    try:
        result = await service.assess_worker(request)
        return make_response(data=WorkerRiskResponse(**result.model_dump()))
    except Exception as exc:
        log.error(f'Worker risk prediction failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.post('/predict/zone', response_model=StandardResponse[ZoneRiskResponse], operation_id='assess_zone')
async def assess_zone(
    request: AssessZoneRequest,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Assess risk for a specific zone.'''
    try:
        result = await service.assess_zone(request)
        return make_response(data=ZoneRiskResponse(**result.model_dump()))
    except Exception as exc:
        log.error(f'Zone risk prediction failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.post('/predict/plant', response_model=StandardResponse[PlantRiskResponse], operation_id='assess_plant')
async def assess_plant(
    request: AssessPlantRequest,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Assess risk for the entire plant.'''
    try:
        result = await service.assess_plant(request)
        return make_response(data=PlantRiskResponse(**result.model_dump()))
    except Exception as exc:
        log.error(f'Plant risk prediction failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.post('/predict/composite', response_model=StandardResponse[CompositeRiskResponse], operation_id='compute_composite_risk')
async def compute_composite_risk(
    request: AssessEntityRequest,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Compute a composite risk across multiple underlying assessments.'''
    try:
        result = await service.compute_composite_risk(request)
        return make_response(data=CompositeRiskResponse(**result.model_dump()))
    except Exception as exc:
        log.error(f'Composite risk prediction failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/history', response_model=StandardResponse[PaginatedRiskResponse], operation_id='list_assessments')
async def list_assessments(
    filter: RiskListFilter = Depends(),
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''List historical risk assessments.'''
    try:
        result = await service.list_assessments(filter)
        return make_response(data=PaginatedRiskResponse(**result.model_dump()))
    except Exception as exc:
        log.error(f'List assessments failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/history/{id}', response_model=StandardResponse[RiskAssessmentResponse], operation_id='get_assessment')
async def get_assessment(
    id: str,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Get a specific risk assessment by ID.'''
    try:
        result = await service.get_assessment(id)
        if not result:
            raise HTTPException(status_code=404, detail="Assessment not found")
        return make_response(data=RiskAssessmentResponse(**result.model_dump()))
    except HTTPException:
        raise
    except Exception as exc:
        log.error(f'Get assessment failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.post('/forecast', response_model=StandardResponse[RiskForecastResponse], operation_id='generate_forecast')
async def generate_forecast(
    request: ForecastRequest,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Generate or retrieve a risk forecast.'''
    try:
        result = await service.generate_forecast(request)
        return make_response(data=RiskForecastResponse(**result.model_dump()))
    except Exception as exc:
        log.error(f'Forecast generation failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/forecast/{entity_type}/{entity_id}', response_model=StandardResponse[RiskForecastResponse], operation_id='get_cached_forecast')
async def get_cached_forecast(
    entity_type: EntityType,
    entity_id: str,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Get cached forecast for an entity.'''
    try:
        result = await service.get_cached_forecast(entity_type, entity_id)
        if not result:
            raise HTTPException(status_code=404, detail="Forecast not found")
        return make_response(data=RiskForecastResponse(**result.model_dump()))
    except HTTPException:
        raise
    except Exception as exc:
        log.error(f'Get cached forecast failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/factors', response_model=StandardResponse[list[RiskFactorResponse]], operation_id='list_top_factors')
async def list_top_factors(
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''List top risk factors across entities.'''
    try:
        result = await service.list_top_factors()
        return make_response(data=[RiskFactorResponse(**r.model_dump()) for r in result])
    except Exception as exc:
        log.error(f'List top factors failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/factors/{entity_id}', response_model=StandardResponse[list[RiskFactorResponse]], operation_id='get_entity_factors')
async def get_entity_factors(
    entity_id: str,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Get risk factors for a specific entity.'''
    try:
        result = await service.get_entity_factors(entity_id)
        return make_response(data=[RiskFactorResponse(**r.model_dump()) for r in result])
    except Exception as exc:
        log.error(f'Get entity factors failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.post('/mitigation', response_model=StandardResponse[MitigationPlanResponse], operation_id='generate_mitigation')
async def generate_mitigation(
    request: AssessEntityRequest,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Generate mitigation plan for an entity.'''
    try:
        result = await service.generate_mitigation(request)
        return make_response(data=MitigationPlanResponse(**result.model_dump()))
    except Exception as exc:
        log.error(f'Generate mitigation failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/mitigation/{plan_id}', response_model=StandardResponse[MitigationPlanResponse], operation_id='get_mitigation_plan')
async def get_mitigation_plan(
    plan_id: str,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Retrieve a specific mitigation plan.'''
    try:
        result = await service.get_mitigation_plan(plan_id)
        if not result:
            raise HTTPException(status_code=404, detail="Plan not found")
        return make_response(data=MitigationPlanResponse(**result.model_dump()))
    except HTTPException:
        raise
    except Exception as exc:
        log.error(f'Get mitigation plan failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/features/{entity_type}/{entity_id}', response_model=StandardResponse[RiskFeaturesResponse], operation_id='get_feature_vector')
async def get_feature_vector(
    entity_type: EntityType,
    entity_id: str,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Get feature vector details.'''
    try:
        result = await service.get_feature_vector(entity_type, entity_id)
        if not result:
            raise HTTPException(status_code=404, detail="Features not found")
        return make_response(data=RiskFeaturesResponse(**result.model_dump()))
    except HTTPException:
        raise
    except Exception as exc:
        log.error(f'Get feature vector failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.post('/scenarios', response_model=StandardResponse[RiskScenarioResponse], operation_id='create_scenario')
async def create_scenario(
    request: ScenarioRequest,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Create a what-if scenario.'''
    try:
        result = await service.create_scenario(request)
        return make_response(data=RiskScenarioResponse(**result.model_dump()))
    except Exception as exc:
        log.error(f'Create scenario failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/scenarios/{entity_type}/{entity_id}', response_model=StandardResponse[list[RiskScenarioResponse]], operation_id='list_scenarios')
async def list_scenarios(
    entity_type: EntityType,
    entity_id: str,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''List scenarios for an entity.'''
    try:
        result = await service.list_scenarios(entity_type, entity_id)
        return make_response(data=[RiskScenarioResponse(**r.model_dump()) for r in result])
    except Exception as exc:
        log.error(f'List scenarios failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/scenarios/{scenario_id}', response_model=StandardResponse[RiskScenarioResponse], operation_id='get_scenario')
async def get_scenario(
    scenario_id: str,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Get a specific scenario.'''
    try:
        result = await service.get_scenario(scenario_id)
        if not result:
            raise HTTPException(status_code=404, detail="Scenario not found")
        return make_response(data=RiskScenarioResponse(**result.model_dump()))
    except HTTPException:
        raise
    except Exception as exc:
        log.error(f'Get scenario failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/explain/{assessment_id}', response_model=StandardResponse[Any], operation_id='get_explainability')
async def get_explainability(
    assessment_id: str,
    service: RiskPredictionService = Depends(get_risk_prediction_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Get explainability breakdown for an assessment.'''
    try:
        result = await service.get_explainability(assessment_id)
        if not result:
            raise HTTPException(status_code=404, detail="Assessment not found")
        return make_response(data=result)
    except HTTPException:
        raise
    except Exception as exc:
        log.error(f'Get explainability failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/analytics/summary', response_model=StandardResponse[RiskAnalyticsSummaryResponse], operation_id='get_analytics_summary')
async def get_analytics_summary(
    service: RiskAnalyticsService = Depends(get_analytics_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Aggregate risk dashboard data.'''
    try:
        result = await service.get_analytics_summary()
        return make_response(data=RiskAnalyticsSummaryResponse(**result.model_dump()))
    except Exception as exc:
        log.error(f'Get analytics summary failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/analytics/trends/{entity_type}/{entity_id}', response_model=StandardResponse[RiskTimelineResponse], operation_id='get_risk_trend')
async def get_risk_trend(
    entity_type: EntityType,
    entity_id: str,
    service: RiskAnalyticsService = Depends(get_analytics_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Get risk trend for an entity.'''
    try:
        result = await service.get_risk_trend(entity_type, entity_id)
        if not result:
            raise HTTPException(status_code=404, detail="Trend not found")
        return make_response(data=RiskTimelineResponse(**result.model_dump()))
    except HTTPException:
        raise
    except Exception as exc:
        log.error(f'Get risk trend failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/analytics/distribution', response_model=StandardResponse[Any], operation_id='get_risk_distribution')
async def get_risk_distribution(
    service: RiskAnalyticsService = Depends(get_analytics_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Get risk level distribution.'''
    try:
        result = await service.get_risk_distribution()
        return make_response(data=result)
    except Exception as exc:
        log.error(f'Get risk distribution failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/analytics/top', response_model=StandardResponse[list[Any]], operation_id='get_top_risks')
async def get_top_risks(
    limit: int = Query(default=10, ge=1, le=100),
    service: RiskAnalyticsService = Depends(get_analytics_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Get top N highest risk entities.'''
    try:
        result = await service.get_top_risks(limit)
        return make_response(data=result)
    except Exception as exc:
        log.error(f'Get top risks failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/analytics/zone-map/{plant_id}', response_model=StandardResponse[Any], operation_id='get_zone_map')
async def get_zone_map(
    plant_id: str,
    service: RiskAnalyticsService = Depends(get_analytics_service),
    principal: Principal = Depends(require_permission(Permission.READ))
):
    '''Get zone risk map for a plant.'''
    try:
        result = await service.get_zone_map(plant_id)
        return make_response(data=result)
    except Exception as exc:
        log.error(f'Get zone map failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))
