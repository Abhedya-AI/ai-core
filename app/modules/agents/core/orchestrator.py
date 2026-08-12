"""orchestrator.py — Production Multi-Agent Orchestrator."""

import asyncio
import time
from typing import Any

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.infrastructure.kafka.registry import Topics
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_registry import AgentRegistry
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.events import AgentDomainEvent
from app.modules.agents.core.execution_plan import ExecutionPlan, ExecutionStage
from app.modules.agents.core.memory import AgentExecutionMemory

log = get_logger("agents.orchestrator")


class AgentOrchestrator:
    """
    Production-grade Agent Orchestrator.

    Resolves stage dependencies, executes parallel agent groups, handles stage retries,
    aggregates execution memory, and dispatches domain events to EventBus.
    """

    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self._registry = registry or AgentRegistry.get_instance()
        self._event_bus = EventBus.get()

    async def execute_plan(self, plan: ExecutionPlan, context: AgentContext) -> tuple[list[AgentResult], AgentExecutionMemory]:
        """
        Execute an ExecutionPlan constructed by Supervisor.

        Args:
            plan: ExecutionPlan detailing stages and dependencies.
            context: Shared immutable AgentContext.

        Returns:
            tuple[list[AgentResult], AgentExecutionMemory]
        """
        start_time = time.perf_counter()
        log.info(f"Orchestrator starting task '{plan.task_id}': '{plan.task_statement}' ({len(plan.stages)} stages)")

        memory = AgentExecutionMemory(task_id=plan.task_id)
        completed_stage_names: set[str] = set()
        all_results: list[AgentResult] = []

        for stage in plan.stages:
            # Check stage dependencies
            if stage.depends_on_stages:
                unmet = [dep for dep in stage.depends_on_stages if dep not in completed_stage_names]
                if unmet:
                    log.warning(f"Skipping Stage '{stage.stage_name}' due to unmet dependencies: {unmet}")
                    continue

            log.info(f"Executing Stage '{stage.stage_name}' (agents: {stage.agent_names}, parallel={stage.allow_parallel})")

            agents_to_run = []
            for name in stage.agent_names:
                agent = self._registry.get(name)
                if agent:
                    agents_to_run.append(agent)
                else:
                    log.warning(f"Agent '{name}' requested in plan but not found in registry")

            if not agents_to_run:
                continue

            if stage.allow_parallel:
                stage_results: list[AgentResult] = await asyncio.gather(
                    *[agent.execute(context) for agent in agents_to_run],
                    return_exceptions=False,
                )
            else:
                stage_results = []
                for agent in agents_to_run:
                    res = await agent.execute(context)
                    stage_results.append(res)

            all_results.extend(stage_results)
            completed_stage_names.add(stage.stage_name)

            # Store results in execution memory and publish events
            for res in stage_results:
                memory.intermediate_results[res.agent_name] = res.output_data
                for event in res.events:
                    await self._event_bus.publish(
                        topic=Topics.WORKER_STATUS_UPDATED,
                        payload=event.model_dump(),
                        key=context.task_id,
                    )

        exec_time = int((time.perf_counter() - start_time) * 1000)
        log.info(f"Orchestrator finished task '{plan.task_id}' in {exec_time}ms ({len(all_results)} agent outputs)")
        return all_results, memory
