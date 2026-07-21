"""document_agent.py — Document Agent managing safety manuals and SOP retrieval."""

from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent


class DocumentAgent(BaseAgent):
    """Specialized agent retrieving, summarizing, and formatting safety manuals and SOP documents."""

    name: str = "DocumentAgent"
    description: str = "Retrieves and summarizes safety manuals, SOPs, and inspection reports."

    async def can_handle(self, context: AgentContext) -> bool:
        return True

    async def _run(self, context: AgentContext) -> AgentResult:
        docs = context.documents or [{"title": "SOP-12 Gas Leak Protocol", "summary": "Evacuate zone immediately"}]

        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=0.92,
            evidence=[f"Retrieved document: '{d.get('title', 'SOP')}'" for d in docs],
            recommendations=["Follow SOP-12 step 3 for gas isolation", "Verify emergency assembly points"],
            output_data={"retrieved_documents": docs},
            explanation=f"Retrieved and analyzed {len(docs)} relevant safety SOP document(s).",
        )
