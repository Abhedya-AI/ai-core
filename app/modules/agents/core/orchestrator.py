"""orchestrator.py — Multi-Agent Orchestrator."""

import asyncio
import time
from typing import Any

from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.infrastructure.kafka.registry import Topics
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.registry import AgentRegistry

log = get_logger("agents.orchestrator")


class ExecutionStage(BaseModel):
    """Stage containing agents that run in parallel."""

    stage_name: str
    agent_names: list[str] = Field(default_factory=list)


class ExecutionPlan(BaseModel):
    """Plan constructed by Supervisor Agent specifying execution stages."""

    task: str
    stages: list[ExecutionStage] = Field(default_factory=list)


class AgentOrchestrator:
    """
    Coordinates multi-agent execution plans.

    Runs stage 1 agents concurrently, passes results to stage 2,
    aggregates results, and emits domain events via EventBus.
    """

    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self._registry = registry or AgentRegistry.get()
        self._event_bus = EventBus.get()

    async def execute_plan(self, plan: ExecutionPlan, context: AgentContext) -> list[AgentResult]:
        """
        Execute an ExecutionPlan constructed by Supervisor.

        Args:
            plan: Structured ExecutionPlan with parallel stages.
            context: Shared AgentContext.

        Returns:
            list of AgentResult objects from all executed agents.
        """
        start_time = time.perf_counter()
        log.info(f"Orchestrator starting execution plan for task: '{plan.task}' ({len(plan.stages)} stages)")
        all_results: list[AgentResult] = []

        for stage_idx, stage in enumerate(plan.stages, 1):
            log.info(f"Executing Stage {stage_idx}: '{stage.stage_name}' with agents: {stage.agent_names}")

            # Gather active agent instances for this stage
            agents_to_run = []
            for name in stage.agent_names:
                agent = self._registry.get_agent(name)
                if agent:
                    agents_to_run.append(agent)
                else:
                    log.warning(f"Agent '{name}' requested in plan but not registered")

            if not agents_to_run:
                continue

            # Run stage agents concurrently via asyncio.gather
            stage_results: list[AgentResult] = await asyncio.gather(
                *[agent.execute(context) for agent in agents_to_run],
                return_exceptions=False,
            )

            all_results.extend(stage_results)

            # Publish agent domain events
            for res in stage_results:
                for event in res.events:
                    await self._event_bus.publish(
                        topic=event.get("topic", Topics.WORKER_STATUS_UPDATED),
                        payload=event.get("payload", {}),
                        key=context.task_id,
                    )

        exec_time = int((time.perf_counter() - start_time) * 1000)
        log.info(f"Orchestrator completed plan execution in {exec_time}ms ({len(all_results)} agent outputs)")
        return all_results
