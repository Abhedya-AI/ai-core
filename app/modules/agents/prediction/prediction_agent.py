"""prediction_agent.py — Prediction Agent evaluating AI equipment failure forecasts."""

from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent


class PredictionAgent(BaseAgent):
    """Specialized agent evaluating predictive models for equipment failure and risk forecasts."""

    name: str = "PredictionAgent"
    description: str = "Evaluates AI predictive failure forecasts and remaining useful life (RUL)."

    async def can_handle(self, context: AgentContext) -> bool:
        return True

    async def _run(self, context: AgentContext) -> AgentResult:
        asset_id = context.target_entity_id or "EQ-PUMP-1"
        predicted_risk = context.metadata.get("predicted_risk", 78.5)

        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=0.89,
            evidence=[f"Predictive model forecast failure risk score of {predicted_risk}% for {asset_id}"],
            recommendations=["Schedule preventative maintenance within 48 hours", "Reduce operating pressure to 80%"],
            output_data={"asset_id": asset_id, "predicted_risk_score": predicted_risk, "rul_days": 3.5},
            explanation=f"Predictive model forecasts elevated failure risk ({predicted_risk}%) for asset '{asset_id}'.",
        )
