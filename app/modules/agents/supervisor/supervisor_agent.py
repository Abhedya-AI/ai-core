"""supervisor_agent.py — Supervisor Agent constructing multi-agent execution plans."""

from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.execution_plan import ExecutionPlan, ExecutionStage
from app.modules.agents.core.types import Capability
from app.modules.graphrag.query.parser import QueryParser


class SupervisorAgent(BaseAgent):
    """
    Supervisor Agent responsible for intent analysis and planning agent execution stages.

    Decides which agents participate in parallel or sequential stages based on task intent.
    """

    name: str = "SupervisorAgent"
    version: str = "1.0.0"
    description: str = "Analyzes query intent and plans multi-agent execution stages."
    capabilities: list[Capability] = [
        Capability.GRAPH_SEARCH,
        Capability.DOCUMENT_SEARCH,
        Capability.RISK_ANALYSIS,
    ]

    async def can_handle(self, context: AgentContext) -> bool:
        return True

    async def create_plan(self, context: AgentContext) -> ExecutionPlan:
        """
        Analyze context task query and plan multi-stage execution.

        Returns:
            ExecutionPlan detailing parallel and sequential stages.
        """
        parsed = QueryParser.parse(context.query)
        q_lower = context.query.lower()

        stage1_agents = ["RiskAgent", "ComplianceAgent", "DocumentAgent"]

        if any(w in q_lower for w in ["camera", "cctv", "vision", "video", "see", "look"]):
            stage1_agents.append("VisionAgent")

        if any(w in q_lower for w in ["predict", "forecast", "future", "health"]):
            stage1_agents.append("PredictionAgent")

        stage2_agents = []
        if any(w in q_lower for w in ["incident", "root cause", "explosion", "failure"]):
            stage2_agents.append("RootCauseAgent")

        stage3_agents = ["EmergencyAgent"]
        stage4_agents = ["NotificationAgent"]

        stages = [
            ExecutionStage(stage_name="Analysis", agent_names=stage1_agents, allow_parallel=True),
        ]

        if stage2_agents:
            stages.append(
                ExecutionStage(
                    stage_name="RootCauseInvestigation",
                    agent_names=stage2_agents,
                    depends_on_stages=["Analysis"],
                    allow_parallel=False,
                )
            )

        stages.append(
            ExecutionStage(
                stage_name="EmergencyPlanning",
                agent_names=stage3_agents,
                depends_on_stages=["Analysis"],
                allow_parallel=False,
            )
        )
        stages.append(
            ExecutionStage(
                stage_name="NotificationDispatch",
                agent_names=stage4_agents,
                depends_on_stages=["EmergencyPlanning"],
                allow_parallel=False,
            )
        )

        return ExecutionPlan(
            task_id=context.task_id,
            task_statement=context.query,
            stages=stages,
        )

    async def _run(self, context: AgentContext) -> AgentResult:
        plan = await self.create_plan(context)
        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=0.98,
            evidence=[f"Created execution plan with {len(plan.stages)} stages"],
            explanation=f"Supervisor planned execution stages across {sum(len(s.agent_names) for s in plan.stages)} total agent invocations.",
            output_data=plan.model_dump(),
        )
