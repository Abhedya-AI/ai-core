"""base_agent.py — Abstract Base Agent definition."""

import time
from abc import ABC, abstractmethod

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult


class BaseAgent(ABC):
    """
    Abstract base class for all ABHEDYA specialized AI Agents.

    Standardizes capability checking, execution logging, error handling,
    and result generation.
    """

    name: str = "BaseAgent"
    description: str = "Base agent specification"

    def __init__(self) -> None:
        self.log = get_logger(f"agents.{self.name.lower()}")

    @abstractmethod
    async def can_handle(self, context: AgentContext) -> bool:
        """Determine if this agent should participate in the given context task."""

    @abstractmethod
    async def _run(self, context: AgentContext) -> AgentResult:
        """Internal agent execution logic implemented by subclasses."""

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute agent with timing metrics and error safety wrapper.
        """
        start_time = time.perf_counter()
        self.log.info(f"Agent '{self.name}' starting task '{context.task_id}'")
        try:
            result = await self._run(context)
            exec_time = int((time.perf_counter() - start_time) * 1000)
            result.execution_time_ms = exec_time
            self.log.info(f"Agent '{self.name}' finished in {exec_time}ms (success={result.success})")
            return result
        except Exception as exc:
            exec_time = int((time.perf_counter() - start_time) * 1000)
            self.log.error(f"Agent '{self.name}' failed: {exc}", exc_info=True)
            return AgentResult(
                agent_name=self.name,
                success=False,
                confidence=0.0,
                execution_time_ms=exec_time,
                explanation=f"Agent '{self.name}' execution failed: {exc}",
            )
