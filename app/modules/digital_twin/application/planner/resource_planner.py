from __future__ import annotations
import uuid
from typing import Any
from app.core.logging import get_logger

log = get_logger(__name__)

class ResourcePlanner:
    def __init__(self, graphrag_service: Any = None):
        self.graphrag_service = graphrag_service

    async def generate_plan(self, twin_id: str, twin_state: dict[str, Any], planning_horizon_days: int = 7, context: dict[str, Any] = None) -> dict[str, Any]:
        context = context or {}
        resource_states = twin_state.get("resource_states", {})
        
        replenishment_schedule = {}
        total_cost = 0.0
        critical_resources = []
        
        for r_id, r_data in resource_states.items():
            avail = r_data.get("availability_pct", 1.0)
            if avail < 0.2:
                critical_resources.append(r_id)
                qty = 100
                unit_cost = context.get(f"{r_id}_cost", 10.0)
                replenishment_schedule[r_id] = {
                    "quantity": qty,
                    "replenishment_date": "Immediate",
                    "priority": "HIGH"
                }
                total_cost += qty * unit_cost
            elif avail < 0.4:
                qty = 50
                unit_cost = context.get(f"{r_id}_cost", 10.0)
                replenishment_schedule[r_id] = {
                    "quantity": qty,
                    "replenishment_date": "Within 3 days",
                    "priority": "MEDIUM"
                }
                total_cost += qty * unit_cost
                
        citations = []
        if self.graphrag_service:
            try:
                ans = await self.graphrag_service.answer("What are best practices for industrial resource planning and inventory management?")
                citations = getattr(ans, "citations", [])
            except Exception:
                pass
                
        return {
            "plan_id": str(uuid.uuid4()),
            "plan_type": "RESOURCE",
            "title": f"Resource Planning ({planning_horizon_days} Days)",
            "resource_inventory": resource_states,
            "replenishment_schedule": replenishment_schedule,
            "critical_resources": critical_resources,
            "estimated_cost": total_cost,
            "confidence": 0.88,
            "graphrag_citations": citations
        }
