"""memory_provider.py — Memory Provider Wrapper."""

from typing import Any

from app.modules.agents.supervisor.memory import SupervisorExecutionMemory


class MemoryProvider:
    """Wraps SupervisorExecutionMemory access."""

    def __init__(self, task_id: str) -> None:
        self.memory = SupervisorExecutionMemory(task_id=task_id)

    def cache_result(self, agent_name: str, data: dict[str, Any]) -> None:
        self.memory.cache_output(agent_name, data)

    def get_cached(self, agent_name: str) -> dict[str, Any] | None:
        return self.memory.get_output(agent_name)
