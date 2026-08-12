from __future__ import annotations
import uuid
from typing import Any
from app.core.logging import get_logger

log = get_logger(__name__)

class EmergencyPlanner:
    def __init__(self, graphrag_service: Any = None, hazard_service: Any = None):
        self.graphrag_service = graphrag_service
        self.hazard_service = hazard_service

    async def generate_plan(self, twin_id: str, twin_state: dict[str, Any], emergency_type: str, severity: float, context: dict[str, Any] = None) -> dict[str, Any]:
        context = context or {}
        
        citations = []
        if self.graphrag_service:
            try:
                ans = await self.graphrag_service.answer(f"What are the standard emergency response procedures for {emergency_type}?")
                citations = getattr(ans, "citations", [])
            except Exception:
                pass
                
        plan = {
            "plan_id": str(uuid.uuid4()),
            "plan_type": "EMERGENCY",
            "title": f"Emergency Response: {emergency_type}",
            "immediate_actions": [
                {"action": "Sound alarm", "priority": "CRITICAL", "responsible_party": "Safety Officer", "deadline_minutes": 1}
            ],
            "evacuation_routes": {},
            "resource_deployment": {"fire_extinguishers": "Zone_A"},
            "communication_plan": ["Notify external emergency services", "Broadcast to all plant workers"],
            "escalation_triggers": ["Fire spreads beyond initial zone", "Worker injury reported"],
            "confidence": 0.9,
            "graphrag_citations": citations
        }
        return plan
