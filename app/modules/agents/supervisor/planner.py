"""planner.py — Planning Engine Facade.

Combines TaskAnalyzer, CapabilityMatcher, and WorkflowBuilder into a unified PlanningEngine.
"""

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_registry import AgentRegistry
from app.modules.agents.core.execution_plan import ExecutionPlan
from app.modules.agents.supervisor.capability_matcher import CapabilityMatcher
from app.modules.agents.supervisor.task_analyzer import TaskAnalysisResult, TaskAnalyzer
from app.modules.agents.supervisor.workflow_builder import WorkflowBuilder

log = get_logger("agents.supervisor.planner")


class PlanningEngine:
    """
    Master planning facade for the Supervisor Agent.

    Analyzes context task, matches capabilities dynamically, and builds an ExecutionPlan.
    """

    def __init__(
        self,
        task_analyzer: TaskAnalyzer | None = None,
        capability_matcher: CapabilityMatcher | None = None,
        workflow_builder: WorkflowBuilder | None = None,
        registry: AgentRegistry | None = None,
    ) -> None:
        self.task_analyzer = task_analyzer or TaskAnalyzer()
        self.capability_matcher = capability_matcher or CapabilityMatcher(registry=registry)
        self.workflow_builder = workflow_builder or WorkflowBuilder()

    def create_execution_plan(
        self,
        context: AgentContext,
    ) -> tuple[ExecutionPlan, TaskAnalysisResult]:
        """
        Analyze context and construct ExecutionPlan DAG.

        Args:
            context: Shared immutable AgentContext.

        Returns:
            Tuple of (ExecutionPlan, TaskAnalysisResult).
        """
        log.info(f"PlanningEngine: creating plan for task '{context.task_id}'")

        # 1. Analyze Task
        analysis = self.task_analyzer.analyze(context)

        # 2. Match Capabilities dynamically via AgentRegistry
        agent_names = self.capability_matcher.resolve_agent_names(analysis.required_capabilities)

        # Fallback if no agents match capabilities
        if not agent_names:
            log.warning("PlanningEngine: no agents matched required capabilities — using fallback.")
            agent_names = ["RiskAgent", "NotificationAgent"]

        # 3. Build Workflow ExecutionPlan
        plan = self.workflow_builder.build_plan(
            task_id=context.task_id,
            task_statement=context.query,
            analysis=analysis,
            matched_agent_names=agent_names,
        )

        return plan, analysis
