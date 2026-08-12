"""
use_cases/context_use_cases.py — Graph Context Assembly Use Case (LLM / GraphRAG).
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.modules.knowledge.application.dto.context_dto import (
    ContextRequest,
    GraphContext,
)
from app.modules.knowledge.services.context_service import ContextService

log = get_logger("knowledge.use_case.context")


class AssembleContextUseCase:
    """Use case: Extract and assemble graph context structure for LLM / GraphRAG integration."""

    def __init__(self, service: ContextService | None = None) -> None:
        self._service = service or ContextService()

    async def execute(self, request: ContextRequest) -> GraphContext:
        """Assemble graph context for a root node."""
        return await self._service.assemble_context(request)
