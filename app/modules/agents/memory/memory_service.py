"""memory_service.py — Execution memory service for agent reasoning histories."""

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.redis.cache import CacheService
from app.modules.agents.core.agent_result import AgentResult

log = get_logger("agents.memory")


class AgentMemoryService:
    """
    Execution memory service maintaining historical agent outputs,
    decisions made, and cached graph context.
    """

    def __init__(self, cache_service: CacheService | None = None) -> None:
        self._cache = cache_service or CacheService(prefix="agent_memory")
        self._local_history: dict[str, list[dict[str, Any]]] = {}

    async def store_result(self, task_id: str, result: AgentResult) -> None:
        """Store an agent execution result in execution memory."""
        data = result.model_dump()
        self._local_history.setdefault(task_id, []).append(data)
        await self._cache.set(f"{task_id}:{result.agent_name}", data, ttl=3600)
        log.info(f"Stored memory for task '{task_id}', agent '{result.agent_name}'")

    async def get_task_history(self, task_id: str) -> list[dict[str, Any]]:
        """Retrieve execution history for a task."""
        return self._local_history.get(task_id, [])
