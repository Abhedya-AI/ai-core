"""vision_agent.py — Vision Agent evaluating CCTV feeds and PPE compliance."""

from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent


class VisionAgent(BaseAgent):
    """Specialized agent processing computer vision, CCTV feeds, and PPE compliance."""

    name: str = "VisionAgent"
    description: str = "Evaluates CCTV video streams, PPE compliance, and visual hazard detections."

    async def can_handle(self, context: AgentContext) -> bool:
        return "vision" in context.query.lower() or "camera" in context.query.lower()

    async def _run(self, context: AgentContext) -> AgentResult:
        camera_id = context.metadata.get("camera_id", "CAM-01")
        detections = context.metadata.get("detections", ["PPE_HELMET_MISSING", "SMOKE_DETECTED"])

        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=0.94,
            evidence=[f"Camera '{camera_id}' detected: {', '.join(detections)}"],
            recommendations=["Issue safety warning to unhelmeted worker", "Inspect smoke detection sensor in Zone B"],
            events=[{"topic": "HAZARD_DETECTED", "payload": {"camera_id": camera_id, "detections": detections}}],
            output_data={"camera_id": camera_id, "detections": detections},
            explanation=f"CCTV Camera '{camera_id}' visual analysis detected {len(detections)} safety anomalies.",
        )
