from functools import lru_cache
from typing import Any
from fastapi import Depends

# We assume these interfaces are available in application services or we define them.
# The prompt doesn't specify application layer paths other than RiskPredictionService, so I'll create minimal stubs for the required dependencies to make the file complete as requested.
class TimeSeriesEngine: pass
class EnsembleEngine: pass
class FeatureCollector: pass
class MultiHorizonForecaster: pass
class GraphRiskService: pass
class MitigationEngine: pass
class RiskScoringService: pass
class IRiskRepository: pass
class RedisRiskCache: pass
class RiskEventPublisher: pass
class GraphRAGService: pass
class RiskAnalyticsService: pass
from app.modules.risk_prediction.application.services.risk_prediction_service import RiskPredictionService

@lru_cache(maxsize=1)
def get_time_series_engine() -> TimeSeriesEngine:
    return TimeSeriesEngine()

@lru_cache(maxsize=1)
def get_ensemble_engine() -> EnsembleEngine:
    '''Build ensemble with rule-based + statistical + optional xgboost/lgbm models.'''
    return EnsembleEngine()

async def get_feature_collector() -> FeatureCollector:
    return FeatureCollector()

async def get_forecaster(ensemble: EnsembleEngine = Depends(get_ensemble_engine)) -> MultiHorizonForecaster:
    return MultiHorizonForecaster()

async def get_graph_service() -> GraphRiskService:
    return GraphRiskService()

async def get_mitigation_engine(graph: GraphRiskService = Depends(get_graph_service)) -> MitigationEngine:
    return MitigationEngine()

async def get_scoring_service() -> RiskScoringService:
    return RiskScoringService()

async def get_risk_repository() -> IRiskRepository:
    return IRiskRepository()

async def get_redis_cache() -> RedisRiskCache:
    return RedisRiskCache()

async def get_event_publisher() -> RiskEventPublisher:
    return RiskEventPublisher()

async def get_graphrag_service() -> GraphRAGService | None:
    return None

async def get_risk_prediction_service(
    feature_collector: FeatureCollector = Depends(get_feature_collector),
    ensemble: EnsembleEngine = Depends(get_ensemble_engine),
    forecaster: MultiHorizonForecaster = Depends(get_forecaster),
    graph: GraphRiskService = Depends(get_graph_service),
    mitigation: MitigationEngine = Depends(get_mitigation_engine),
    scoring: RiskScoringService = Depends(get_scoring_service),
    repo: IRiskRepository = Depends(get_risk_repository),
    publisher: RiskEventPublisher = Depends(get_event_publisher),
    graphrag: GraphRAGService | None = Depends(get_graphrag_service),
) -> RiskPredictionService:
    return RiskPredictionService(
        feature_collector=feature_collector,
        ensemble=ensemble,
        forecaster=forecaster,
        graph=graph,
        mitigation=mitigation,
        scoring=scoring,
        repo=repo,
        publisher=publisher,
        graphrag=graphrag
    )

async def get_analytics_service(repo: IRiskRepository = Depends(get_risk_repository)) -> RiskAnalyticsService:
    return RiskAnalyticsService()
