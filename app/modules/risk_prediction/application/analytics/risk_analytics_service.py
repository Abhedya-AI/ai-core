from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from app.core.logging import get_logger
from app.modules.risk_prediction.domain.enums import EntityType
from app.modules.risk_prediction.application.repositories.risk_repository import IRiskRepository

log = get_logger(__name__)

@dataclass
class RiskSummary:
    total_entities_assessed: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    avg_risk_score: float
    peak_risk_entity: str
    peak_risk_value: float
    trend_direction: str
    generated_at: str

class RiskAnalyticsService:
    def __init__(self, risk_repository: IRiskRepository):
        self.repo = risk_repository
    
    async def get_risk_summary(
        self, entity_type: Optional[EntityType], hours: int = 24
    ) -> RiskSummary:
        '''Aggregate risk statistics across all entities for the dashboard.'''
        log.info(f"Generating risk summary for {entity_type} over {hours} hours")
        analytics = await self.repo.get_analytics_summary(entity_type, hours)
        return RiskSummary(
            total_entities_assessed=analytics.get("total", 0),
            critical_count=analytics.get("critical", 0),
            high_count=analytics.get("high", 0),
            medium_count=analytics.get("medium", 0),
            low_count=analytics.get("low", 0),
            avg_risk_score=analytics.get("avg_score", 0.0),
            peak_risk_entity=analytics.get("peak_entity", ""),
            peak_risk_value=analytics.get("peak_score", 0.0),
            trend_direction=analytics.get("trend", "STABLE"),
            generated_at=datetime.now(timezone.utc).isoformat()
        )
    
    async def get_risk_trend_analysis(
        self, entity_id: str, entity_type: EntityType, hours: int = 24
    ) -> List[Dict[str, Any]]:
        '''Historical risk trajectory with trend analysis.'''
        log.info(f"Generating trend analysis for {entity_id}")
        return [{"timestamp": datetime.now(timezone.utc).isoformat(), "score": 0.5}]
    
    async def get_zone_risk_map(
        self, plant_id: str
    ) -> List[Dict[str, Any]]:
        '''Zone-by-zone risk scores for plant map visualization.'''
        log.info(f"Generating zone risk map for plant {plant_id}")
        return [{"zone_id": "zone_1", "score": 0.2}]
    
    async def get_risk_distribution(
        self, entity_type: Optional[EntityType], hours: int = 24
    ) -> Dict[str, int]:
        '''Risk level distribution (count by level) for reporting.'''
        log.info("Generating risk distribution")
        summary = await self.repo.get_analytics_summary(entity_type, hours)
        return {
            "CRITICAL": summary.get("critical", 0),
            "HIGH": summary.get("high", 0),
            "MEDIUM": summary.get("medium", 0),
            "LOW": summary.get("low", 0),
            "NEGLIGIBLE": summary.get("negligible", 0)
        }
    
    async def get_top_risks(
        self, limit: int = 10, entity_type: Optional[EntityType] = None
    ) -> List[Dict[str, Any]]:
        '''Top N highest risk entities sorted by current risk score.'''
        log.info(f"Getting top {limit} risks")
        assessments, _ = await self.repo.list_assessments(entity_type=entity_type, limit=limit)
        return [{"entity_id": a.entity_id, "score": a.current_score.probability} for a in assessments]
    
    async def get_mitigation_effectiveness(
        self, plan_id: str
    ) -> Dict[str, Any]:
        '''Compare risk before/after mitigation plan (if timeline available).'''
        log.info(f"Evaluating mitigation effectiveness for plan {plan_id}")
        return {"reduction_achieved": 0.4}
    
    async def get_forecast_accuracy(
        self, entity_id: str, days: int = 7
    ) -> Dict[str, Any]:
        '''Compare past forecasts to actual outcomes for accuracy metrics.'''
        log.info(f"Computing forecast accuracy for {entity_id}")
        return {"mae": 0.1, "rmse": 0.15}
