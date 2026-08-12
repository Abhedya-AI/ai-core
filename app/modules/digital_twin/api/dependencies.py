from __future__ import annotations
from typing import Annotated
from fastapi import Depends

try:
    from app.modules.digital_twin.application.services.digital_twin_orchestration_service import DigitalTwinOrchestrationService
except ImportError:
    class DigitalTwinOrchestrationService:
        def __init__(self, graphrag_service=None, knowledge_service=None):
            self.graphrag_service = graphrag_service
            self.knowledge_service = knowledge_service

_twin_service_instance: DigitalTwinOrchestrationService | None = None

def _get_or_create_twin_service() -> DigitalTwinOrchestrationService:
    global _twin_service_instance
    if _twin_service_instance is None:
        try:
            from app.modules.graphrag.services.graphrag_service import GraphRAGService
            graphrag = GraphRAGService()
        except Exception:
            graphrag = None
        try:
            from app.modules.knowledge.services.knowledge_service import KnowledgeService
            knowledge = KnowledgeService()
        except Exception:
            knowledge = None
        
        _twin_service_instance = DigitalTwinOrchestrationService(
            graphrag_service=graphrag,
            knowledge_service=knowledge,
        )
    return _twin_service_instance

def get_twin_service() -> DigitalTwinOrchestrationService:
    """Singleton pattern for the main service."""
    return _get_or_create_twin_service()

TwinServiceDep = Annotated[DigitalTwinOrchestrationService, Depends(get_twin_service)]
