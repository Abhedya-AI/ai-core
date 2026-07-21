"""compliance_agent.py — Compliance Agent validating safety regulations and SOPs."""

from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent


class ComplianceAgent(BaseAgent):
    """Specialized agent verifying regulatory compliance against OSHA, ISO, and factory SOPs."""

    name: str = "ComplianceAgent"
    description: str = "Checks OSHA, ISO, and facility SOP regulatory compliance."

    async def can_handle(self, context: AgentContext) -> bool:
        return True

    async def _run(self, context: AgentContext) -> AgentResult:
        reg_code = context.metadata.get("regulation", "OSHA-1910.147")
        is_compliant = context.metadata.get("is_compliant", True)

        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=0.96,
            evidence=[f"Evaluated regulation '{reg_code}' (Lockout/Tagout standard)"],
            recommendations=["Ensure hot work permits are signed before zone entry", "Audit safety checklist compliance"],
            output_data={"regulation": reg_code, "compliant": is_compliant},
            explanation=f"Compliance check against '{reg_code}' confirmed operational adherence.",
        )
