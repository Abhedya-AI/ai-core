"""
api/dependencies.py — FastAPI Dependency Injection Providers for Knowledge Module.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.modules.knowledge.application.use_cases import (
    AnalyzeImpactUseCase,
    AssembleContextUseCase,
    ComputeAnalyticsUseCase,
    ComputeCentralityUseCase,
    CreateNodeUseCase,
    CreateRelationshipUseCase,
    DeleteNodeUseCase,
    DeleteRelationshipUseCase,
    DetectCommunitiesUseCase,
    FindNodeUseCase,
    NeighborhoodUseCase,
    SearchKnowledgeGraphUseCase,
    ShortestPathUseCase,
    SyncGraphBatchUseCase,
    SyncGraphNodeUseCase,
    TraverseGraphUseCase,
    UpdateNodeUseCase,
)
from app.modules.knowledge.infrastructure.repositories.analytics_repository import (
    AnalyticsRepository,
)
from app.modules.knowledge.infrastructure.repositories.base_repository import (
    BaseNeo4jRepository,
)
from app.modules.knowledge.infrastructure.repositories.history_repository import (
    HistoryRepository,
)
from app.modules.knowledge.infrastructure.repositories.ontology_repository import (
    OntologyRepository,
)
from app.modules.knowledge.infrastructure.repositories.traversal_repository import (
    TraversalRepository,
)
from app.modules.knowledge.services.context_service import ContextService
from app.modules.knowledge.services.graph_analytics_service import GraphAnalyticsService
from app.modules.knowledge.services.graph_cache_service import GraphCacheService
from app.modules.knowledge.services.graph_history_service import GraphHistoryService
from app.modules.knowledge.services.graph_search_service import GraphSearchService
from app.modules.knowledge.services.graph_sync_service import GraphSyncService
from app.modules.knowledge.services.knowledge_service import KnowledgeService

# ── Repositories ──────────────────────────────────────────────────────────────

def get_base_repo() -> BaseNeo4jRepository:
    return BaseNeo4jRepository()

def get_traversal_repo() -> TraversalRepository:
    return TraversalRepository()

def get_analytics_repo() -> AnalyticsRepository:
    return AnalyticsRepository()

def get_ontology_repo() -> OntologyRepository:
    return OntologyRepository()

def get_history_repo() -> HistoryRepository:
    return HistoryRepository()

# ── Services ──────────────────────────────────────────────────────────────────

def get_cache_service() -> GraphCacheService:
    return GraphCacheService()

def get_sync_service(
    repo: Annotated[BaseNeo4jRepository, Depends(get_base_repo)],
) -> GraphSyncService:
    return GraphSyncService(repo=repo)

def get_history_service(
    repo: Annotated[HistoryRepository, Depends(get_history_repo)],
) -> GraphHistoryService:
    return GraphHistoryService(history_repo=repo)

def get_context_service(
    traversal_repo: Annotated[TraversalRepository, Depends(get_traversal_repo)],
    cache: Annotated[GraphCacheService, Depends(get_cache_service)],
) -> ContextService:
    return ContextService(traversal_repo=traversal_repo, cache_service=cache)

def get_search_service(
    repo: Annotated[BaseNeo4jRepository, Depends(get_base_repo)],
) -> GraphSearchService:
    return GraphSearchService(repo=repo)

def get_analytics_service(
    analytics_repo: Annotated[AnalyticsRepository, Depends(get_analytics_repo)],
    traversal_repo: Annotated[TraversalRepository, Depends(get_traversal_repo)],
    cache: Annotated[GraphCacheService, Depends(get_cache_service)],
) -> GraphAnalyticsService:
    return GraphAnalyticsService(
        analytics_repo=analytics_repo,
        traversal_repo=traversal_repo,
        cache_service=cache,
    )

def get_knowledge_service() -> KnowledgeService:
    return KnowledgeService()

# ── Use Cases ─────────────────────────────────────────────────────────────────

def get_create_node_use_case(
    repo: Annotated[BaseNeo4jRepository, Depends(get_base_repo)],
    cache: Annotated[GraphCacheService, Depends(get_cache_service)],
) -> CreateNodeUseCase:
    return CreateNodeUseCase(repo=repo, cache=cache)

def get_update_node_use_case(
    repo: Annotated[BaseNeo4jRepository, Depends(get_base_repo)],
    history: Annotated[GraphHistoryService, Depends(get_history_service)],
    cache: Annotated[GraphCacheService, Depends(get_cache_service)],
) -> UpdateNodeUseCase:
    return UpdateNodeUseCase(repo=repo, history=history, cache=cache)

def get_delete_node_use_case(
    repo: Annotated[BaseNeo4jRepository, Depends(get_base_repo)],
    cache: Annotated[GraphCacheService, Depends(get_cache_service)],
) -> DeleteNodeUseCase:
    return DeleteNodeUseCase(repo=repo, cache=cache)

def get_find_node_use_case(
    repo: Annotated[BaseNeo4jRepository, Depends(get_base_repo)],
    cache: Annotated[GraphCacheService, Depends(get_cache_service)],
) -> FindNodeUseCase:
    return FindNodeUseCase(repo=repo, cache=cache)

def get_create_relationship_use_case(
    repo: Annotated[BaseNeo4jRepository, Depends(get_base_repo)],
) -> CreateRelationshipUseCase:
    return CreateRelationshipUseCase(repo=repo)

def get_delete_relationship_use_case(
    repo: Annotated[BaseNeo4jRepository, Depends(get_base_repo)],
) -> DeleteRelationshipUseCase:
    return DeleteRelationshipUseCase(repo=repo)

def get_traverse_use_case(
    repo: Annotated[TraversalRepository, Depends(get_traversal_repo)],
) -> TraverseGraphUseCase:
    return TraverseGraphUseCase(repo=repo)

def get_shortest_path_use_case(
    repo: Annotated[TraversalRepository, Depends(get_traversal_repo)],
    cache: Annotated[GraphCacheService, Depends(get_cache_service)],
) -> ShortestPathUseCase:
    return ShortestPathUseCase(repo=repo, cache=cache)

def get_neighborhood_use_case(
    repo: Annotated[TraversalRepository, Depends(get_traversal_repo)],
    cache: Annotated[GraphCacheService, Depends(get_cache_service)],
) -> NeighborhoodUseCase:
    return NeighborhoodUseCase(repo=repo, cache=cache)

def get_compute_analytics_use_case(
    service: Annotated[GraphAnalyticsService, Depends(get_analytics_service)],
) -> ComputeAnalyticsUseCase:
    return ComputeAnalyticsUseCase(service=service)

def get_assemble_context_use_case(
    service: Annotated[ContextService, Depends(get_context_service)],
) -> AssembleContextUseCase:
    return AssembleContextUseCase(service=service)

def get_sync_node_use_case(
    service: Annotated[GraphSyncService, Depends(get_sync_service)],
) -> SyncGraphNodeUseCase:
    return SyncGraphNodeUseCase(service=service)

def get_sync_batch_use_case(
    service: Annotated[GraphSyncService, Depends(get_sync_service)],
) -> SyncGraphBatchUseCase:
    return SyncGraphBatchUseCase(service=service)

def get_search_use_case(
    service: Annotated[GraphSearchService, Depends(get_search_service)],
) -> SearchKnowledgeGraphUseCase:
    return SearchKnowledgeGraphUseCase(service=service)
