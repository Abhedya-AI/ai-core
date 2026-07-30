"""
app/services/workflow_service.py — Supervisor Workflow Service.

Direct interface to run a Supervisor workflow for any arbitrary query.
Used by the /api/v1/workflows endpoint — the general-purpose AI query interface.

Tracks workflow state per task_id for status polling.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.modules.agents import AgentRegistry, SupervisorAgent
from app.modules.agents.core.orchestrator import AgentOrchestrator
from app.modules.auth.models import Principal
from app.services.base import BaseService

log = get_logger("services.workflow")


class WorkflowRecord:
    """Tracks state of a Supervisor workflow run."""

    def __init__(self, task_id: str, query: str, requested_by: str) -> None:
        self.task_id = task_id
        self.query = query
        self.requested_by = requested_by
        self.status = "RUNNING"
        self.started_at = datetime.now(timezone.utc)
        self.completed_at: datetime | None = None
        self.results: list[dict[str, Any]] = []
        self.error: str | None = None
        self.execution_time_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "query": self.query,
            "requested_by": self.requested_by,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time_ms": self.execution_time_ms,
            "results": self.results,
            "error": self.error,
        }


class WorkflowStore:
    _instance: "WorkflowStore | None" = None

    def __init__(self) -> None:
        self._workflows: dict[str, WorkflowRecord] = {}

    @classmethod
    def get_instance(cls) -> "WorkflowStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def save(self, record: WorkflowRecord) -> None:
        self._workflows[record.task_id] = record

    def get(self, task_id: str) -> WorkflowRecord | None:
        return self._workflows.get(task_id)

    def list_recent(self, limit: int = 20) -> list[WorkflowRecord]:
        return list(reversed(list(self._workflows.values())))[:limit]


class WorkflowService(BaseService):
    """Executes Supervisor workflows and tracks their state."""

    def __init__(
        self,
        store: WorkflowStore | None = None,
        registry: AgentRegistry | None = None,
    ) -> None:
        self._store = store or WorkflowStore.get_instance()
        self._registry = registry or AgentRegistry.get_instance()

    async def run_workflow(
        self,
        query: str,
        *,
        intent: str = "GENERAL_SAFETY",
        zone_id: str | None = None,
        target_entity_id: str | None = None,
        principal: Principal | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a Supervisor workflow for the given query.

        Returns:
            WorkflowRecord dict with results.
        """
        ctx = self._build_context(
            query=query,
            intent=intent,
            principal=principal,
            zone_id=zone_id,
            target_entity_id=target_entity_id,
            metadata=metadata or {},
        )

        record = WorkflowRecord(
            task_id=ctx.task_id,
            query=query,
            requested_by=principal.user_id if principal else "anonymous",
        )
        self._store.save(record)

        start = time.perf_counter()
        try:
            supervisor = SupervisorAgent(registry=self._registry)
            plan = await supervisor.create_plan(ctx)
            orchestrator = AgentOrchestrator(registry=self._registry)
            results, _ = await orchestrator.execute_plan(plan, ctx)

            record.results = [
                {
                    "agent": r.agent_name,
                    "success": r.success,
                    "confidence": r.confidence,
                    "evidence": r.evidence,
                    "recommendations": r.recommendations,
                    "explanation": r.explanation,
                    "output_data": r.output_data,
                }
                for r in results
            ]
            record.status = "COMPLETED"
        except Exception as exc:
            log.error(f"Workflow {ctx.task_id} failed: {exc}")
            record.status = "FAILED"
            record.error = str(exc)
        finally:
            record.execution_time_ms = int((time.perf_counter() - start) * 1000)
            record.completed_at = datetime.now(timezone.utc)
            self._store.save(record)

        return record.to_dict()

    async def get_workflow(self, task_id: str) -> dict[str, Any]:
        from app.api.exceptions import NotFoundError
        record = self._store.get(task_id)
        if not record:
            raise NotFoundError(message=f"Workflow '{task_id}' not found.")
        return record.to_dict()

    async def list_workflows(self, limit: int = 20) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self._store.list_recent(limit)]


_workflow_svc: WorkflowService | None = None


def get_workflow_service() -> WorkflowService:
    global _workflow_svc
    if _workflow_svc is None:
        _workflow_svc = WorkflowService()
    return _workflow_svc
