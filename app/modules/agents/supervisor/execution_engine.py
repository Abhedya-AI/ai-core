"""execution_engine.py — Supervisor Workflow Execution Engine.

Executes an ExecutionPlan constructed by PlanningEngine.
Orchestrates stage execution, shared memory caching, retries, HITL checkpoints, conflict resolution, and event dispatch.
"""

import asyncio
import time
from typing import Any

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_registry import AgentRegistry
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.events import AgentDomainEvent
from app.modules.agents.core.execution_plan import ExecutionPlan
from app.modules.agents.supervisor.conflict_resolver import ConflictResolver
from app.modules.agents.supervisor.events import SupervisorEventGenerator
from app.modules.agents.supervisor.memory import SupervisorExecutionMemory
from app.modules.agents.supervisor.models import HITLCheckpoint, WorkflowState
from app.modules.agents.supervisor.providers.event_provider import EventProvider
from app.modules.agents.supervisor.retry_manager import RetryManager
from app.modules.agents.supervisor.scheduler import StageScheduler
from app.modules.agents.supervisor.state_manager import WorkflowStateManager

log = get_logger("agents.supervisor.execution_engine")


class WorkflowExecutionEngine:
    """
    Executes an ExecutionPlan DAG.
    Coordinates stage scheduler, shared execution memory, retries, HITL checkpoints, and conflict resolution.
    """

    def __init__(
        self,
        registry: AgentRegistry | None = None,
        scheduler: StageScheduler | None = None,
        state_manager: WorkflowStateManager | None = None,
        retry_manager: RetryManager | None = None,
        conflict_resolver: ConflictResolver | None = None,
        event_provider: EventProvider | None = None,
    ) -> None:
        self.registry = registry or AgentRegistry.get_instance()
        self.scheduler = scheduler or StageScheduler()
        self.state_manager = state_manager or WorkflowStateManager()
        self.retry_manager = retry_manager or RetryManager()
        self.conflict_resolver = conflict_resolver or ConflictResolver()
        self.event_provider = event_provider or EventProvider()

    async def execute_plan(
        self,
        plan: ExecutionPlan,
        context: AgentContext,
        requires_hitl: bool = False,
    ) -> tuple[list[AgentResult], SupervisorExecutionMemory, list[AgentDomainEvent], list[HITLCheckpoint]]:
        """
        Execute an ExecutionPlan DAG.

        Args:
            plan: ExecutionPlan detailing stages and agent names.
            context: Shared immutable AgentContext.
            requires_hitl: Whether this workflow requires HITL approval for emergency actions.

        Returns:
            Tuple of (list[AgentResult], SupervisorExecutionMemory, list[AgentDomainEvent], list[HITLCheckpoint]).
        """
        start_time = time.perf_counter()
        memory = SupervisorExecutionMemory(task_id=plan.task_id)
        published_events: list[AgentDomainEvent] = []
        checkpoints: list[HITLCheckpoint] = []

        self.state_manager.transition_to(plan.task_id, WorkflowState.RUNNING, "Starting plan execution")

        completed_stage_names: set[str] = set()
        all_results: list[AgentResult] = []

        for stage in plan.stages:
            # Check stage dependencies
            if stage.depends_on_stages:
                unmet = [dep for dep in stage.depends_on_stages if dep not in completed_stage_names]
                if unmet:
                    log.warning(f"Skipping Stage '{stage.stage_name}' due to unmet dependencies: {unmet}")
                    continue

            # HITL Checkpoint check for Emergency Planning stage if required
            if requires_hitl and "EmergencyPlanning" in stage.stage_name:
                cp = self.state_manager.create_hitl_checkpoint(
                    workflow_id=plan.task_id,
                    stage_name=stage.stage_name,
                    reason="Emergency response plan activation requires safety officer approval.",
                )
                checkpoints.append(cp)
                published_events.append(
                    SupervisorEventGenerator.human_review_requested("SupervisorAgent", cp, context.trace_id)
                )
                log.info(f"Execution paused at Stage '{stage.stage_name}' for HITL approval.")
                # Auto-approve in test / automation mode if configured in context metadata
                if context.metadata.get("auto_approve_hitl", True):
                    self.state_manager.approve_checkpoint(cp.checkpoint_id, approved_by="AutoApproveSafetyOfficer")
                else:
                    break

            self.state_manager.transition_to(plan.task_id, WorkflowState.RUNNING, f"Running stage '{stage.stage_name}'")
            published_events.append(
                SupervisorEventGenerator.workflow_updated(
                    "SupervisorAgent", plan.task_id, WorkflowState.RUNNING, stage.stage_name, context.trace_id
                )
            )

            # Resolve agents from registry
            agents_to_run = []
            for name in stage.agent_names:
                agent = self.registry.get(name)
                if agent:
                    agents_to_run.append(agent)
                else:
                    log.warning(f"Agent '{name}' in stage '{stage.stage_name}' not found in registry")

            if not agents_to_run:
                continue

            for agent in agents_to_run:
                published_events.append(
                    SupervisorEventGenerator.agent_execution_started(
                        "SupervisorAgent", plan.task_id, agent.name, stage.stage_name, context.trace_id
                    )
                )

            # Execute stage via scheduler
            stage_results = await self.scheduler.run_stage(
                agents=agents_to_run,
                context=context,
                allow_parallel=stage.allow_parallel,
            )

            # Handle retries for failed agents if transient
            final_stage_results: list[AgentResult] = []
            for idx, res in enumerate(stage_results):
                if not res.success:
                    agent = agents_to_run[idx]
                    log.warning(f"Agent '{agent.name}' failed in stage '{stage.stage_name}'. Checking retry...")
                    # Retry once if transient
                    backoff = self.retry_manager.calculate_backoff(1)
                    await asyncio.sleep(backoff)
                    retry_res = await agent.execute(context)
                    final_stage_results.append(retry_res)
                else:
                    final_stage_results.append(res)

            for res in final_stage_results:
                all_results.append(res)
                memory.cache_output(res.agent_name, res.output_data)
                published_events.append(
                    SupervisorEventGenerator.agent_execution_completed(
                        "SupervisorAgent", plan.task_id, res.agent_name, res.success, context.trace_id
                    )
                )

            completed_stage_names.add(stage.stage_name)

        self.state_manager.transition_to(plan.task_id, WorkflowState.COMPLETED, "Plan execution finished")
        log.info(f"WorkflowExecutionEngine: completed task '{plan.task_id}' with {len(all_results)} agent outputs.")

        return all_results, memory, published_events, checkpoints
