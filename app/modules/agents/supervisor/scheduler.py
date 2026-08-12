"""scheduler.py — Execution Stage Scheduler.

Schedules and controls execution stage invocations with support for:
  - Parallel vs Sequential execution
  - Per-stage timeouts
  - Task cancellation
  - Priority execution
"""

import asyncio
from typing import Any, Callable

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent

log = get_logger("agents.supervisor.scheduler")


class StageScheduler:
    """
    Stage Scheduler enforcing timeouts, cancellations, and parallel concurrency.
    """

    def __init__(self, default_timeout_seconds: float = 60.0) -> None:
        self.default_timeout_seconds = default_timeout_seconds
        self._cancelled_tasks: set[str] = set()

    def cancel_task(self, task_id: str) -> None:
        """Mark a task as cancelled."""
        self._cancelled_tasks.add(task_id)
        log.warning(f"StageScheduler: cancelled task_id='{task_id}'")

    def is_cancelled(self, task_id: str) -> bool:
        """Return True if task is cancelled."""
        return task_id in self._cancelled_tasks

    async def run_stage(
        self,
        agents: list[BaseAgent],
        context: AgentContext,
        allow_parallel: bool = True,
        timeout_seconds: float | None = None,
    ) -> list[AgentResult]:
        """
        Run a group of agents sequentially or in parallel under timeout controls.

        Args:
            agents: List of BaseAgent instances to execute.
            context: Shared AgentContext.
            allow_parallel: Whether to run concurrently via asyncio.gather.
            timeout_seconds: Stage timeout in seconds.

        Returns:
            List of AgentResult objects.
        """
        if self.is_cancelled(context.task_id):
            log.warning(f"StageScheduler: skipping stage for cancelled task '{context.task_id}'")
            return [
                AgentResult(
                    agent_name=a.name,
                    success=False,
                    explanation="Task execution was cancelled by Supervisor.",
                )
                for a in agents
            ]

        timeout = timeout_seconds or self.default_timeout_seconds

        try:
            if allow_parallel and len(agents) > 1:
                log.info(f"StageScheduler: executing {len(agents)} agents in PARALLEL (timeout={timeout}s)")
                results = await asyncio.wait_for(
                    asyncio.gather(*[a.execute(context) for a in agents], return_exceptions=True),
                    timeout=timeout,
                )
                processed: list[AgentResult] = []
                for idx, res in enumerate(results):
                    if isinstance(res, Exception):
                        log.error(f"StageScheduler: agent '{agents[idx].name}' raised: {res}")
                        processed.append(
                            AgentResult(
                                agent_name=agents[idx].name,
                                success=False,
                                explanation=f"Execution error: {res}",
                            )
                        )
                    else:
                        processed.append(res)
                return processed

            else:
                log.info(f"StageScheduler: executing {len(agents)} agents SEQUENTIALLY")
                results = []
                for a in agents:
                    if self.is_cancelled(context.task_id):
                        break
                    res = await asyncio.wait_for(a.execute(context), timeout=timeout)
                    results.append(res)
                return results

        except asyncio.TimeoutError:
            log.error(f"StageScheduler: stage timed out after {timeout}s")
            return [
                AgentResult(
                    agent_name=a.name,
                    success=False,
                    explanation=f"Stage execution timed out after {timeout}s",
                )
                for a in agents
            ]
