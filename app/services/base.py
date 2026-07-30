"""
app/services/base.py — BaseService Abstract Class.

All Application Services inherit from this to get:
  - Standardized AgentContext building from request data + principal
  - Consistent error wrapping from AgentResult → AbhedyaException
  - Trace ID propagation
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from app.api.exceptions import AgentExecutionError
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.auth.models import Principal


class BaseService:
    """Abstract base for all Application Services."""

    def _build_context(
        self,
        query: str,
        *,
        intent: str = "GENERAL_SAFETY",
        principal: Principal | None = None,
        target_entity_id: str | None = None,
        zone_id: str | None = None,
        trace_id: str | None = None,
        graph_snapshot: dict[str, Any] | None = None,
        documents: list[dict[str, Any]] | None = None,
        sensor_data: list[dict[str, Any]] | None = None,
        predictions: list[dict[str, Any]] | None = None,
        vision_events: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentContext:
        """
        Build an immutable AgentContext from HTTP request data and principal.

        Embeds the caller's identity into the context for downstream agents.
        """
        user_context: dict[str, Any] = {}
        if principal:
            user_context = {
                "user_id": principal.user_id,
                "roles": principal.roles,
                "org_id": principal.org_id,
                "plant_id": principal.plant_id,
                "zone_ids": principal.zone_ids,
                "department": principal.department,
                "shift": principal.shift,
            }

        return AgentContext(
            task_id=str(uuid.uuid4()),
            trace_id=trace_id or str(uuid.uuid4()),
            query=query,
            intent=intent,
            target_entity_id=target_entity_id,
            zone_id=zone_id,
            graph_snapshot=graph_snapshot or {},
            documents=documents or [],
            sensor_data=sensor_data or [],
            predictions=predictions or [],
            vision_events=vision_events or [],
            user_context=user_context,
            metadata=metadata or {},
        )

    def _ensure_success(self, result: AgentResult, agent_name: str) -> AgentResult:
        """
        Raise AgentExecutionError if the agent result indicates failure.

        Args:
            result: AgentResult from agent.execute().
            agent_name: Name for error message.

        Returns:
            result unchanged if successful.
        """
        if not result.success:
            raise AgentExecutionError(
                message=f"{agent_name} failed: {result.explanation}",
                details={"agent": agent_name, "explanation": result.explanation},
            )
        return result
