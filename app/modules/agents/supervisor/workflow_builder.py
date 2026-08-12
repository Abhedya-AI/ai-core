"""workflow_builder.py — ExecutionPlan Workflow Builder.

Converts intent analysis, matched capabilities, and resolved dependencies
into a multi-stage ExecutionPlan.
"""

from app.core.logging import get_logger
from app.modules.agents.core.execution_plan import ExecutionPlan, ExecutionStage
from app.modules.agents.supervisor.dependency_resolver import DependencyResolver
from app.modules.agents.supervisor.models import WorkflowIntent
from app.modules.agents.supervisor.task_analyzer import TaskAnalysisResult

log = get_logger("agents.supervisor.workflow_builder")


class WorkflowBuilder:
    """
    Assembles ExecutionPlan objects containing sequential, parallel, and conditional stages.
    """

    def __init__(self, dependency_resolver: DependencyResolver | None = None) -> None:
        self.dependency_resolver = dependency_resolver or DependencyResolver()

    def build_plan(
        self,
        task_id: str,
        task_statement: str,
        analysis: TaskAnalysisResult,
        matched_agent_names: list[str],
    ) -> ExecutionPlan:
        """
        Build an ExecutionPlan DAG from analyzed task requirements.

        Args:
            task_id: Task identifier.
            task_statement: User prompt or task description.
            analysis: TaskAnalysisResult from TaskAnalyzer.
            matched_agent_names: List of agent names covering required capabilities.

        Returns:
            ExecutionPlan detailing parallel and sequential stages.
        """
        # Resolve topological execution stages
        stage_groups = self.dependency_resolver.resolve_stages(matched_agent_names)

        stages: list[ExecutionStage] = []
        completed_stage_names: list[str] = []

        for idx, group in enumerate(stage_groups, start=1):
            stage_name = f"Stage_{idx}_{_get_stage_label(group, analysis.intent)}"
            allow_parallel = len(group) > 1

            depends_on = list(completed_stage_names[-1:]) if completed_stage_names else []

            stage = ExecutionStage(
                stage_name=stage_name,
                agent_names=group,
                depends_on_stages=depends_on,
                allow_parallel=allow_parallel,
            )
            stages.append(stage)
            completed_stage_names.append(stage_name)

        plan = ExecutionPlan(
            task_id=task_id,
            task_statement=task_statement,
            stages=stages,
        )

        log.info(
            f"WorkflowBuilder: constructed ExecutionPlan for task '{task_id}' "
            f"({len(stages)} stages, {sum(len(s.agent_names) for s in stages)} agent invocations)"
        )
        return plan


def _get_stage_label(group: list[str], intent: WorkflowIntent) -> str:
    """Generate human-readable label for execution stage."""
    if "VisionAgent" in group or "DocumentAgent" in group:
        return "Observation_and_Ingestion"
    if "RiskAgent" in group or "PredictionAgent" in group:
        return "Risk_and_Prediction"
    if "RootCauseAgent" in group:
        return "RootCause_Investigation"
    if "ComplianceAgent" in group:
        return "Compliance_Evaluation"
    if "EmergencyAgent" in group:
        return "Emergency_Planning"
    if "NotificationAgent" in group:
        return "Notification_Dispatch"
    return "Analysis"
