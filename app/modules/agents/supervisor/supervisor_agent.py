"""supervisor_agent.py — Master Supervisor Agent (Sprint 3 Milestone 3.10).

The Supervisor Agent is the operational brain of ABHEDYA.

It never performs domain work itself — its job is to think, plan, coordinate, monitor, and adapt.

Full Lifecycle Orchestration:
  1. Task Analysis — extract intent, target zone/entity, required capabilities
  2. Dynamic Capability Matching — match requirements to registered agents via AgentRegistry
  3. Execution DAG Planning — build topological sequential/parallel/conditional stages
  4. Workflow Scheduling & Execution — run stages concurrently or sequentially under timeout controls
  5. Shared Execution Memory — cache intermediate graph/docs/predictions/risk/timeline across steps
  6. Transient Failure Retries — retry transient errors with exponential backoff & jitter
  7. Human-in-the-Loop (HITL) Checkpoints — approval gates for high-impact emergency actions
  8. Output Conflict Resolution — resolve contradicting claims using source authority / confidence
  9. Result Aggregation — merge all agent outputs into a unified Incident Report DTO
 10. Orchestration Explanation — generate human-auditable execution statement
 11. EventBus Publication — publish WorkflowStarted/Updated/Completed/Failed events
 12. Knowledge Graph Metadata Persistence — record investigation node and USED_AGENT relations
"""

import time

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_registry import AgentRegistry
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.execution_plan import ExecutionPlan
from app.modules.agents.core.types import Capability
from app.modules.agents.supervisor.aggregator import ResultAggregator
from app.modules.agents.supervisor.conflict_resolver import ConflictResolver
from app.modules.agents.supervisor.events import SupervisorEventGenerator
from app.modules.agents.supervisor.execution_engine import WorkflowExecutionEngine
from app.modules.agents.supervisor.explanation import OrchestrationExplanationGenerator
from app.modules.agents.supervisor.models import (
    SupervisorAgentResult,
    WorkflowState,
)
from app.modules.agents.supervisor.planner import PlanningEngine
from app.modules.agents.supervisor.providers.event_provider import EventProvider
from app.modules.agents.supervisor.providers.graph_provider import GraphProvider
from app.modules.agents.supervisor.telemetry import TelemetryCollector

log = get_logger("agents.supervisor")


class SupervisorAgent(BaseAgent):
    """
    Master Supervisor Agent — Milestone 3.10.

    Decides which agents participate, execution order, parallel groups, shared memory caching,
    conflict resolution, retries, HITL checkpoints, and result aggregation.
    """

    name: str = "SupervisorAgent"
    version: str = "1.0.0"
    description: str = (
        "Operational brain of ABHEDYA orchestrating specialized agents via DAG execution plans, "
        "shared memory caching, conflict resolution, HITL checkpoints, and unified report aggregation."
    )
    capabilities: list[Capability] = [
        Capability.GRAPH_SEARCH,
        Capability.DOCUMENT_SEARCH,
        Capability.RISK_ANALYSIS,
        Capability.PREDICTION,
        Capability.ROOT_CAUSE,
        Capability.EMERGENCY,
        Capability.COMPLIANCE,
        Capability.NOTIFICATION,
    ]

    def __init__(self, registry: AgentRegistry | None = None) -> None:
        super().__init__()
        self.registry = registry or AgentRegistry.get_instance()
        self.planner = PlanningEngine(registry=self.registry)
        self.execution_engine = WorkflowExecutionEngine(registry=self.registry)
        self.aggregator = ResultAggregator()
        self.conflict_resolver = ConflictResolver()
        self.explanation_generator = OrchestrationExplanationGenerator()
        self.telemetry_collector = TelemetryCollector()
        self.graph_provider = GraphProvider()
        self.event_provider = EventProvider()

    async def can_handle(self, context: AgentContext) -> bool:
        """Supervisor Agent can handle any multi-agent execution context."""
        return True

    async def create_plan(self, context: AgentContext) -> ExecutionPlan:
        """
        Public contract for creating an ExecutionPlan from an AgentContext.

        Args:
            context: Shared immutable AgentContext.

        Returns:
            ExecutionPlan detailing parallel and sequential stages.
        """
        plan, _ = self.planner.create_execution_plan(context)
        return plan

    async def _run(self, context: AgentContext) -> AgentResult:
        """
        Execute full Supervisor orchestration workflow.
        """
        total_start = time.perf_counter()

        # ─────────────────────────────────────────────────
        # 1. Planning Phase
        # ─────────────────────────────────────────────────
        plan_start = time.perf_counter()
        plan, analysis = self.planner.create_execution_plan(context)
        planning_time_ms = int((time.perf_counter() - plan_start) * 1000)

        log.info(
            f"SupervisorAgent: planned task '{plan.task_id}' with intent={analysis.intent.value} "
            f"({len(plan.stages)} stages, {sum(len(s.agent_names) for s in plan.stages)} total agent calls)"
        )

        workflow_events = [
            SupervisorEventGenerator.workflow_started(
                self.name, plan.task_id, analysis.intent.value, len(plan.stages), context.trace_id
            )
        ]

        # ─────────────────────────────────────────────────
        # 2. Execution Phase
        # ─────────────────────────────────────────────────
        exec_start = time.perf_counter()
        agent_results, memory, exec_events, checkpoints = await self.execution_engine.execute_plan(
            plan=plan,
            context=context,
            requires_hitl=analysis.requires_hitl,
        )
        execution_time_ms = int((time.perf_counter() - exec_start) * 1000)
        workflow_events.extend(exec_events)

        # ─────────────────────────────────────────────────
        # 3. Conflict Resolution Phase
        # ─────────────────────────────────────────────────
        conflicts = self.conflict_resolver.resolve_conflicts(agent_results)

        # ─────────────────────────────────────────────────
        # 4. Result Aggregation Phase
        # ─────────────────────────────────────────────────
        aggregated_report = self.aggregator.aggregate(
            workflow_id=plan.task_id,
            intent=analysis.intent,
            results=agent_results,
            conflicts=conflicts,
            checkpoints=checkpoints,
        )

        # ─────────────────────────────────────────────────
        # 5. Explanation & Telemetry Phase
        # ─────────────────────────────────────────────────
        explanation = self.explanation_generator.generate_explanation(
            plan=plan,
            results=agent_results,
            intent_value=analysis.intent.value,
        )

        telemetry = self.telemetry_collector.collect(
            workflow_id=plan.task_id,
            planning_time_ms=planning_time_ms,
            execution_time_ms=execution_time_ms,
            results=agent_results,
            stages_count=len(plan.stages),
            cache_hits=memory.hits_count,
        )

        # ─────────────────────────────────────────────────
        # 6. Publish Workflow Completed Event & Persist KG
        # ─────────────────────────────────────────────────
        executed_agents = [r.agent_name for r in agent_results if r.success]
        completed_event = SupervisorEventGenerator.workflow_completed(
            self.name, plan.task_id, aggregated_report.overall_confidence, executed_agents, context.trace_id
        )
        workflow_events.append(completed_event)

        # Persist Knowledge Graph investigation node & relations asynchronously
        await self.graph_provider.persist_investigation_metadata(
            workflow_id=plan.task_id,
            agents_used=executed_agents,
            intent=analysis.intent.value,
        )

        # Dispatch all events to EventBus
        await self.event_provider.publish_events(workflow_events, key=plan.task_id)

        evidence = [
            f"Analyzed intent as '{analysis.intent.value}' and built a {len(plan.stages)}-stage ExecutionPlan",
            f"Executed {len(executed_agents)} specialized agents ({telemetry.parallel_efficiency:.0%} parallel efficiency)",
            f"Resolved {len(conflicts)} output conflicts across agents",
            f"Shared memory cache hits: {memory.hits_count}",
        ]
        if checkpoints:
            evidence.append(f"Passed {len(checkpoints)} Human-in-the-Loop (HITL) approval checkpoint(s)")

        recommendations = aggregated_report.recommendations or [
            "Review aggregated incident report and recommendations in ABHEDYA dashboard."
        ]

        return SupervisorAgentResult(
            agent_name=self.name,
            success=True,
            confidence=aggregated_report.overall_confidence,
            workflow_id=plan.task_id,
            intent=analysis.intent,
            workflow_state=WorkflowState.COMPLETED,
            evidence=evidence,
            recommendations=recommendations,
            events=workflow_events,
            explanation=explanation,
            aggregated_report=aggregated_report,
            execution_summary=explanation,
            orchestration_telemetry=telemetry,
            output_data=aggregated_report.model_dump(),
        )
