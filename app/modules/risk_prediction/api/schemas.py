from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.modules.risk_prediction.domain.enums import (
    AssessmentStatus, EntityType, FeatureCategory, ForecastHorizon,
    MitigationPriority, MitigationType, ModelType, RiskLevel, RiskType, TrendDirection
)

class AssessEntityRequest(BaseModel):
    entity_id: str
    entity_type: EntityType
    sensor_ids: list[str] = Field(default_factory=list)
    risk_types: list[RiskType] | None = None
    generate_forecast: bool = True
    generate_mitigation: bool = True
    
    model_config = ConfigDict(
        json_schema_extra={
            'example': {
                'entity_id': 'EQ-001',
                'entity_type': 'EQUIPMENT',
                'sensor_ids': ['TEMP-001', 'PRESS-002'],
                'generate_forecast': True,
                'generate_mitigation': True,
            }
        }
    )

class AssessEquipmentRequest(BaseModel):
    equipment_id: str
    sensor_ids: list[str]
    equipment_type: str = ''
    equipment_name: str = ''

class AssessWorkerRequest(BaseModel):
    worker_id: str
    zone_id: str
    sensor_ids: list[str] = Field(default_factory=list)

class AssessZoneRequest(BaseModel):
    zone_id: str
    zone_name: str = ''
    equipment_ids: list[str] = Field(default_factory=list)
    sensor_ids: list[str] = Field(default_factory=list)

class AssessPlantRequest(BaseModel):
    plant_id: str
    plant_name: str = ''
    zone_ids: list[str]

class ForecastRequest(BaseModel):
    entity_id: str
    entity_type: EntityType
    sensor_ids: list[str] = Field(default_factory=list)
    horizons: list[ForecastHorizon] | None = None

class ScenarioRequest(BaseModel):
    entity_id: str
    entity_type: EntityType
    sensor_ids: list[str] = Field(default_factory=list)
    scenario_name: str
    description: str = ''
    modified_conditions: dict[str, float]

class RiskListFilter(BaseModel):
    entity_type: EntityType | None = None
    entity_id: str | None = None
    hours: int = Field(default=24, ge=1, le=720)
    min_risk_level: RiskLevel | None = None
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=200)
    sort_by: str = Field(default='timestamp')
    sort_order: str = Field(default='desc')

# Response Schemas

class RiskScoreResponse(BaseModel):
    overall_score: float
    probability: float
    confidence: float
    uncertainty: float
    level: RiskLevel
    trend: TrendDirection | None = None
    historical_percentile: float | None = None
    
    model_config = ConfigDict(from_attributes=True)

class RiskFactorResponse(BaseModel):
    id: str
    name: str
    description: str
    contribution_weight: float
    category: str
    current_value: float | None = None
    threshold: float | None = None
    
    model_config = ConfigDict(from_attributes=True)

class RiskEvidenceResponse(BaseModel):
    id: str
    source_type: str
    source_id: str
    description: str
    relevance_score: float
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RiskConfidenceResponse(BaseModel):
    score: float
    factors: list[str]
    missing_data_ratio: float
    model_uncertainty: float
    
    model_config = ConfigDict(from_attributes=True)

class RiskPredictionResponse(BaseModel):
    id: str
    model_type: ModelType
    risk_type: RiskType
    score: RiskScoreResponse
    factors: list[RiskFactorResponse]
    evidence: list[RiskEvidenceResponse]
    confidence_metrics: RiskConfidenceResponse
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RiskWindowResponse(BaseModel):
    start_time: datetime
    end_time: datetime
    horizon: ForecastHorizon
    
    model_config = ConfigDict(from_attributes=True)

class RiskForecastResponse(BaseModel):
    id: str
    entity_id: str
    entity_type: EntityType
    base_timestamp: datetime
    windows: list[RiskWindowResponse]
    predictions: dict[ForecastHorizon, RiskPredictionResponse]
    
    model_config = ConfigDict(from_attributes=True)

class RiskRecommendationResponse(BaseModel):
    id: str
    title: str
    description: str
    mitigation_type: MitigationType
    priority: MitigationPriority
    estimated_impact: float
    required_actions: list[str]
    
    model_config = ConfigDict(from_attributes=True)

class MitigationPlanResponse(BaseModel):
    id: str
    assessment_id: str
    recommendations: list[RiskRecommendationResponse]
    created_at: datetime
    status: str
    
    model_config = ConfigDict(from_attributes=True)

class RiskAssessmentResponse(BaseModel):
    id: str
    entity_id: str
    entity_type: EntityType
    timestamp: datetime
    status: AssessmentStatus
    overall_risk: RiskScoreResponse
    predictions: list[RiskPredictionResponse]
    forecast: RiskForecastResponse | None = None
    mitigation_plan: MitigationPlanResponse | None = None
    
    model_config = ConfigDict(from_attributes=True)

class EquipmentRiskResponse(RiskAssessmentResponse):
    equipment_type: str
    equipment_name: str
    maintenance_status: str | None = None

class WorkerRiskResponse(RiskAssessmentResponse):
    zone_id: str
    fatigue_level: float | None = None
    exposure_time: float | None = None

class ZoneRiskResponse(RiskAssessmentResponse):
    zone_name: str
    active_equipment_count: int
    worker_count: int

class PlantRiskResponse(RiskAssessmentResponse):
    plant_name: str
    critical_zones: list[str]

class CompositeRiskResponse(RiskAssessmentResponse):
    contributing_assessments: list[str]
    aggregation_method: str

class RiskScenarioResponse(BaseModel):
    id: str
    scenario_name: str
    description: str
    base_assessment_id: str
    modified_conditions: dict[str, float]
    simulated_assessment: RiskAssessmentResponse
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RiskTrendResponse(BaseModel):
    timestamp: datetime
    risk_level: RiskLevel
    score: float
    
    model_config = ConfigDict(from_attributes=True)

class RiskTimelineResponse(BaseModel):
    entity_id: str
    entity_type: EntityType
    start_time: datetime
    end_time: datetime
    trends: dict[RiskType, list[RiskTrendResponse]]
    
    model_config = ConfigDict(from_attributes=True)

class RiskAnalyticsSummaryResponse(BaseModel):
    total_assessments: int
    critical_entities: int
    high_risk_entities: int
    trend_summary: dict[str, int]
    risk_distribution: dict[RiskLevel, int]
    
    model_config = ConfigDict(from_attributes=True)

class RiskFeaturesResponse(BaseModel):
    entity_id: str
    entity_type: EntityType
    timestamp: datetime
    features: dict[str, Any]
    feature_importance: dict[str, float] | None = None
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedRiskResponse(BaseModel):
    items: list[RiskAssessmentResponse]
    total: int
    offset: int
    limit: int
    has_more: bool
    
    model_config = ConfigDict(from_attributes=True)
