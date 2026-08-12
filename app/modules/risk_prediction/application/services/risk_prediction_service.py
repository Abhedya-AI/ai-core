import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Protocol

from app.core.logging import get_logger
from app.modules.risk_prediction.domain.enums import (
    AssessmentStatus, EntityType, ForecastHorizon,
    RiskLevel, RiskType, TrendDirection
)
from app.modules.risk_prediction.domain.models import (
    CompositeRisk, EquipmentRisk, MitigationPlan, PlantRisk,
    RiskAssessment, RiskConfidence, RiskEvidence, RiskFactor, RiskForecast,
    RiskPrediction, RiskRecommendation, RiskScenario, RiskScore, RiskTimeline,
    RiskTrend, RiskWindow, WorkerRisk, ZoneRisk
)
from app.modules.risk_prediction.domain.events import (
    PredictionCompleted, RiskCalculated, RiskEscalated, RiskForecastGenerated, RiskThresholdExceeded
)

from app.modules.risk_prediction.application.services.risk_scoring_service import RiskScoringService

log = get_logger(__name__)

class FeatureCollector(Protocol):
    async def collect(self, entity_id: str, entity_type: EntityType, sensor_ids: list[str]) -> Any: ...

class EnsembleEngine(Protocol):
    async def predict(self, feature_vector: Any, risk_type: RiskType) -> Any: ...

class MultiHorizonForecaster(Protocol):
    async def forecast(self, assessment: RiskAssessment, horizons: list[ForecastHorizon]) -> RiskForecast: ...

class GraphRiskService(Protocol):
    async def get_context(self, entity_id: str) -> Any: ...

class MitigationEngine(Protocol):
    async def generate_plan(self, assessment: RiskAssessment) -> MitigationPlan: ...

class IRiskRepository(Protocol):
    async def save_assessment(self, assessment: RiskAssessment) -> None: ...
    async def get_latest_assessment(self, entity_id: str, risk_type: RiskType) -> RiskAssessment | None: ...
    async def get_risk_history(self, entity_id: str, limit: int = 10) -> RiskTimeline: ...

class RiskEventPublisher(Protocol):
    async def publish(self, event: Any) -> None: ...

class GraphRAGService(Protocol):
    async def get_context(self, entity_id: str) -> str: ...

class RiskPredictionService:
    def __init__(
        self,
        feature_collector: Any,
        ensemble_engine: Any,
        forecaster: Any,
        graph_service: Any,
        mitigation_engine: Any,
        scoring_service: RiskScoringService,
        risk_repository: Any,
        event_publisher: Any,
        graphrag_service: Any | None = None,
    ):
        self.feature_collector = feature_collector
        self.ensemble_engine = ensemble_engine
        self.forecaster = forecaster
        self.graph_service = graph_service
        self.mitigation_engine = mitigation_engine
        self.scoring_service = scoring_service
        self.risk_repository = risk_repository
        self.event_publisher = event_publisher
        self.graphrag_service = graphrag_service
        
    async def assess_entity(
        self,
        entity_id: str,
        entity_type: EntityType,
        sensor_ids: list[str],
        risk_types: list[RiskType] | None = None,
        generate_forecast: bool = True,
        generate_mitigation: bool = True,
    ) -> RiskAssessment:
        start_time = time.monotonic()
        
        try:
            # Collect features
            feature_vector = await self.feature_collector.collect(entity_id, entity_type, sensor_ids)
            
            # Get contexts
            graph_context_task = self.graph_service.get_context(entity_id)
            graphrag_context_task = self.graphrag_service.get_context(entity_id) if self.graphrag_service else self._mock_context()
            graph_context, graphrag_context = await asyncio.gather(graph_context_task, graphrag_context_task)
            
            if not risk_types:
                risk_types = [RiskType.COMPOSITE]
                
            evidence_list = await self._build_evidence_list(feature_vector, graphrag_context, graph_context)
            
            predictions = []
            for r_type in risk_types:
                ensemble_output = await self._run_ensemble_prediction(feature_vector, r_type)
                
                # compute score
                conf = self.scoring_service.compute_confidence(
                    getattr(feature_vector, "completeness", {}),
                    getattr(ensemble_output, "confidences", [])
                )
                
                score = self.scoring_service.compute_risk_score(
                    raw_probability=getattr(ensemble_output, "probability", 0.1),
                    confidence=conf,
                    uncertainty=self.scoring_service.compute_uncertainty(getattr(ensemble_output, "probabilities", [])),
                    risk_type=r_type
                )
                
                top_factors = self.scoring_service.extract_top_factors(
                    getattr(ensemble_output, "feature_importance", {}),
                    feature_vector
                )
                
                explanation = self.scoring_service.build_explanation(
                    score, top_factors, evidence_list, r_type, entity_type
                )
                
                pred = RiskPrediction(
                    type=r_type,
                    score=score,
                    factors=top_factors,
                    explanation=explanation
                )
                predictions.append(pred)

            previous_assessment = await self.risk_repository.get_latest_assessment(entity_id, RiskType.COMPOSITE)
            
            # Simple trend computation
            trend = RiskTrend(direction=TrendDirection.STABLE, slope=0.0)
            
            assessment = RiskAssessment(
                id=str(uuid.uuid4()),
                entity_id=entity_id,
                entity_type=entity_type,
                timestamp=datetime.now(timezone.utc).isoformat(),
                status=AssessmentStatus.COMPLETED,
                predictions=predictions,
                evidence=evidence_list,
                trend=trend
            )
            
            if generate_forecast:
                try:
                    assessment.forecast = await self.forecaster.forecast(assessment, [ForecastHorizon.ONE_HOUR, ForecastHorizon.SIX_HOUR])
                    await self.event_publisher.publish(RiskForecastGenerated(entity_id=entity_id, forecast_id=assessment.forecast.id))
                except Exception as e:
                    log.error(f"Failed to generate forecast: {e}")
                    
            if generate_mitigation:
                try:
                    assessment.mitigation_plan = await self.mitigation_engine.generate_plan(assessment)
                except Exception as e:
                    log.error(f"Failed to generate mitigation plan: {e}")
                    
            await self.risk_repository.save_assessment(assessment)
            
            # Publish events
            await self.event_publisher.publish(RiskCalculated(entity_id=entity_id, assessment_id=assessment.id))
            
            latency = time.monotonic() - start_time
            await self.event_publisher.publish(PredictionCompleted(entity_id=entity_id, assessment_id=assessment.id, latency_ms=latency * 1000))
            
            await self._check_threshold_and_escalate(assessment, previous_assessment)
            
            return assessment
            
        except Exception as e:
            log.error(f"Failed assessment for {entity_id}: {e}")
            raise
    
    async def _mock_context(self) -> str:
        return ""

    async def assess_equipment(
        self,
        equipment_id: str,
        sensor_ids: list[str],
        equipment_type: str = '',
        equipment_name: str = '',
    ) -> EquipmentRisk:
        assessment = await self.assess_entity(
            entity_id=equipment_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=sensor_ids,
            risk_types=[RiskType.EQUIPMENT_FAILURE]
        )
        return EquipmentRisk(
            assessment=assessment,
            equipment_id=equipment_id,
            equipment_type=equipment_type,
            equipment_name=equipment_name
        )
        
    async def assess_worker(
        self,
        worker_id: str,
        zone_id: str,
        sensor_ids: list[str],
    ) -> WorkerRisk:
        assessment = await self.assess_entity(
            entity_id=worker_id,
            entity_type=EntityType.WORKER,
            sensor_ids=sensor_ids,
            risk_types=[RiskType.WORKER_INJURY]
        )
        return WorkerRisk(
            assessment=assessment,
            worker_id=worker_id,
            zone_id=zone_id
        )
        
    async def assess_zone(
        self,
        zone_id: str,
        zone_name: str,
        equipment_ids: list[str],
        sensor_ids: list[str],
    ) -> ZoneRisk:
        assessment = await self.assess_entity(
            entity_id=zone_id,
            entity_type=EntityType.ZONE,
            sensor_ids=sensor_ids,
            risk_types=[RiskType.OPERATIONAL, RiskType.ENVIRONMENTAL]
        )
        return ZoneRisk(
            assessment=assessment,
            zone_id=zone_id,
            zone_name=zone_name,
            equipment_ids=equipment_ids
        )
        
    async def assess_plant(
        self,
        plant_id: str,
        plant_name: str,
        zone_ids: list[str],
    ) -> PlantRisk:
        assessment = await self.assess_entity(
            entity_id=plant_id,
            entity_type=EntityType.PLANT,
            sensor_ids=[],
            risk_types=[RiskType.COMPOSITE]
        )
        return PlantRisk(
            assessment=assessment,
            plant_id=plant_id,
            plant_name=plant_name,
            zone_ids=zone_ids
        )
        
    async def compute_composite_risk(
        self,
        entity_id: str,
        entity_type: EntityType,
        sensor_ids: list[str],
    ) -> CompositeRisk:
        assessment = await self.assess_entity(
            entity_id=entity_id,
            entity_type=entity_type,
            sensor_ids=sensor_ids,
            risk_types=[RiskType.COMPOSITE]
        )
        return CompositeRisk(
            assessment=assessment,
            entity_id=entity_id
        )
        
    async def run_scenario(
        self,
        entity_id: str,
        entity_type: EntityType,
        sensor_ids: list[str],
        scenario_name: str,
        modified_conditions: dict[str, float],
    ) -> RiskScenario:
        # Mock logic since we are not fully implementing the scenario engine in this service
        return RiskScenario(
            id=str(uuid.uuid4()),
            name=scenario_name,
            assessment=None,  # Would be an assessment based on modified conditions
            modified_conditions=modified_conditions
        )
        
    async def get_risk_forecast(
        self,
        entity_id: str,
        entity_type: EntityType,
        sensor_ids: list[str],
        horizons: list[ForecastHorizon] | None = None,
    ) -> RiskForecast:
        assessment = await self.risk_repository.get_latest_assessment(entity_id, RiskType.COMPOSITE)
        if not assessment:
            assessment = await self.assess_entity(entity_id, entity_type, sensor_ids, generate_forecast=False, generate_mitigation=False)
        return await self.forecaster.forecast(assessment, horizons or [ForecastHorizon.ONE_HOUR])
        
    async def _run_ensemble_prediction(
        self,
        feature_vector: Any,
        risk_type: RiskType,
    ) -> Any:
        return await self.ensemble_engine.predict(feature_vector, risk_type)
        
    async def _build_evidence_list(
        self,
        feature_vector: Any,
        graphrag_context: str,
        graph_context: Any,
    ) -> list[RiskEvidence]:
        return []
        
    async def _check_threshold_and_escalate(
        self,
        assessment: RiskAssessment,
        previous_assessment: RiskAssessment | None,
    ) -> None:
        if previous_assessment:
            # Need to compare max risk score level
            pass
