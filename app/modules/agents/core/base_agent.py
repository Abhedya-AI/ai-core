"""base_agent.py — Production BaseAgent specification with retries & lifecycle tracking."""

import asyncio
import time
from abc import ABC, abstractmethod

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.exceptions import NonRetryableAgentException, RetryableAgentException
from app.modules.agents.core.lifecycle import LifecycleTracker
from app.modules.agents.core.telemetry import AgentTelemetry
from app.modules.agents.core.types import AgentLifecycleState, Capability


class BaseAgent(ABC):
    """
    Abstract base class for all ABHEDYA specialized AI Agents.

    Provides strict lifecycle state tracking, versioning, capability declarations,
    exponential backoff retries for transient errors, and telemetry capture.
    """

    name: str = "BaseAgent"
    version: str = "1.0.0"
    description: str = "Base agent specification"
    capabilities: list[Capability] = []
    max_retries: int = 2
    retry_backoff_sec: float = 0.2

    def __init__(self) -> None:
        self.log = get_logger(f"agents.{self.name.lower()}")
        self.lifecycle = LifecycleTracker(self.name)

    @abstractmethod
    async def can_handle(self, context: AgentContext) -> bool:
        """Determine if this agent should participate in the given task."""

    @abstractmethod
    async def _run(self, context: AgentContext) -> AgentResult:
        """Internal agent logic implemented by subclasses."""

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute agent following standard lifecycle state transitions and retry policy.
        """
        start_time = time.perf_counter()
        self.lifecycle.transition_to(AgentLifecycleState.VALIDATED)
        self.lifecycle.transition_to(AgentLifecycleState.READY)
        self.lifecycle.transition_to(AgentLifecycleState.RUNNING)

        retries = 0
        while True:
            try:
                result = await self._run(context)
                exec_time = int((time.perf_counter() - start_time) * 1000)
                result.execution_time_ms = exec_time

                if result.telemetry is None:
                    result.telemetry = AgentTelemetry(
                        agent_name=self.name,
                        execution_time_ms=exec_time,
                        confidence=result.confidence,
                        retries_count=retries,
                        events_published=len(result.events),
                    )

                self.lifecycle.transition_to(AgentLifecycleState.COMPLETED)
                return result

            except RetryableAgentException as exc:
                retries += 1
                if retries <= self.max_retries:
                    self.log.warning(f"Agent '{self.name}' hit retryable error: {exc}. Retrying ({retries}/{self.max_retries})...")
                    self.lifecycle.transition_to(AgentLifecycleState.RETRYING)
                    await asyncio.sleep(self.retry_backoff_sec * (2 ** (retries - 1)))
                else:
                    exec_time = int((time.perf_counter() - start_time) * 1000)
                    self.log.error(f"Agent '{self.name}' exhausted retries: {exc}")
                    self.lifecycle.transition_to(AgentLifecycleState.FAILED)
                    return AgentResult(
                        agent_name=self.name,
                        success=False,
                        confidence=0.0,
                        execution_time_ms=exec_time,
                        explanation=f"Exhausted retries due to error: {exc}",
                        telemetry=AgentTelemetry(agent_name=self.name, execution_time_ms=exec_time, errors_count=1, retries_count=retries),
                    )

            except (NonRetryableAgentException, Exception) as exc:
                exec_time = int((time.perf_counter() - start_time) * 1000)
                self.log.error(f"Agent '{self.name}' non-retryable failure: {exc}")
                self.lifecycle.transition_to(AgentLifecycleState.FAILED)
                return AgentResult(
                    agent_name=self.name,
                    success=False,
                    confidence=0.0,
                    execution_time_ms=exec_time,
                    explanation=f"Agent failed with error: {exc}",
                    telemetry=AgentTelemetry(agent_name=self.name, execution_time_ms=exec_time, errors_count=1),
                )
