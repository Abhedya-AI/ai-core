"""explanation.py — Orchestration Explanation Generator.

Produces human-auditable explanations detailing the exact sequence of agent steps executed
and why each was chosen by the Supervisor.
"""

from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.execution_plan import ExecutionPlan


class OrchestrationExplanationGenerator:
    """Generates human-readable orchestration summaries for operators."""

    @staticmethod
    def generate_explanation(
        plan: ExecutionPlan,
        results: list[AgentResult],
        intent_value: str,
    ) -> str:
        """
        Build an orchestration explanation text.

        Args:
            plan: ExecutionPlan constructed by Supervisor.
            results: List of completed AgentResult objects.
            intent_value: Intent string (e.g. 'EMERGENCY_INVESTIGATION').

        Returns:
            Human-readable explanation statement.
        """
        lines = [
            f"Supervisor evaluated task intent as '{intent_value}' and constructed a {len(plan.stages)}-stage execution plan."
        ]

        executed_map = {r.agent_name: r for r in results if r.success}

        for idx, stage in enumerate(plan.stages, start=1):
            agents_ran = [a for a in stage.agent_names if a in executed_map]
            mode = "in parallel" if stage.allow_parallel and len(agents_ran) > 1 else "sequentially"
            if agents_ran:
                lines.append(f"Stage {idx} ({stage.stage_name}): Executed {', '.join(agents_ran)} {mode}.")

        lines.append(f"Successfully aggregated outputs from {len(executed_map)} specialized agent(s).")
        return " ".join(lines)
