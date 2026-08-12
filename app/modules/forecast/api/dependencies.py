from __future__ import annotations

from functools import lru_cache
from fastapi import Depends

from app.modules.forecast.application.services.forecast_orchestration_service import ForecastOrchestrationService
from app.modules.forecast.infrastructure.repositories.postgres_forecast_repository import PostgresForecastRepository
from app.modules.forecast.infrastructure.cache.redis_forecast_cache import RedisForecastCache
from app.modules.forecast.application.events.forecast_event_publisher import ForecastEventPublisher


@lru_cache(maxsize=1)
def get_forecast_repository() -> PostgresForecastRepository:
    """Provides singleton instance of PostgresForecastRepository."""
    return PostgresForecastRepository()


@lru_cache(maxsize=1)
def get_forecast_cache() -> RedisForecastCache:
    """Provides singleton instance of RedisForecastCache."""
    return RedisForecastCache()


@lru_cache(maxsize=1)
def get_event_publisher() -> ForecastEventPublisher:
    """Provides singleton instance of ForecastEventPublisher."""
    return ForecastEventPublisher()


async def get_graphrag_service():
    """Provides GraphRAGService if available."""
    try:
        from app.modules.graphrag.services.graphrag_service import GraphRAGService
        return GraphRAGService()
    except Exception:
        return None


async def get_knowledge_service():
    """Provides KnowledgeService if available."""
    try:
        from app.modules.knowledge.services.knowledge_service import KnowledgeService
        return KnowledgeService()
    except Exception:
        return None


async def get_forecast_orchestration_service(
    repo: PostgresForecastRepository = Depends(get_forecast_repository),
    publisher: ForecastEventPublisher = Depends(get_event_publisher),
    graphrag=Depends(get_graphrag_service),
    knowledge=Depends(get_knowledge_service),
) -> ForecastOrchestrationService:
    """Provides configured instance of ForecastOrchestrationService."""
    return ForecastOrchestrationService(
        repository=repo,
        event_publisher=publisher,
        graphrag_service=graphrag,
        knowledge_service=knowledge,
    )
