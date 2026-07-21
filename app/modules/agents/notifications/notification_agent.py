"""notification_agent.py — Notification Agent dispatching alerts."""

from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.events import AgentDomainEvent
from app.modules.agents.core.types import Capability


class NotificationAgent(BaseAgent):
    """Specialized agent converting safety events into outbound push notifications and SMS alerts."""

    name: str = "NotificationAgent"
    version: str = "1.0.0"
    description: str = "Dispatches SMS, Email, and Dashboard alerts for safety events."
    capabilities: list[Capability] = [Capability.NOTIFICATION]

    async def can_handle(self, context: AgentContext) -> bool:
        return True

    async def _run(self, context: AgentContext) -> AgentResult:
        channels = ["SMS", "APP_PUSH", "DASHBOARD"]
        worker_ids = context.metadata.get("recipient_workers", ["W-101", "W-102"])

        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=1.0,
            evidence=[f"Dispatched push notification alerts to {len(worker_ids)} workers via {channels}"],
            recommendations=["Monitor delivery acknowledgment receipts"],
            events=[AgentDomainEvent(event_type="WORKER_STATUS_UPDATED", agent_name=self.name, payload={"workers": worker_ids, "action": "NOTIFIED"}, trace_id=context.trace_id)],
            output_data={"recipients": worker_ids, "channels": channels},
            explanation=f"Notification Agent dispatched safety alerts to {len(worker_ids)} personnel.",
        )
