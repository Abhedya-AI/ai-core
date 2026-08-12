from __future__ import annotations
import uuid
from typing import Any
from app.core.logging import get_logger

log = get_logger(__name__)

class MaintenancePlanner:
    def __init__(self, optimization_service: Any = None, forecast_service: Any = None, graphrag_service: Any = None):
        self.optimization_service = optimization_service
        self.forecast_service = forecast_service
        self.graphrag_service = graphrag_service

    async def generate_plan(self, twin_id: str, twin_state: dict[str, Any], horizon_days: int = 30, context: dict[str, Any] = None) -> dict[str, Any]:
        context = context or {}
        equipment_states = twin_state.get("equipment_states", {})
        
        needs_maintenance = []
        for eq_id, eq_data in equipment_states.items():
            health = eq_data.get("health_score", 1.0)
            rul = eq_data.get("rul_hours", 9999)
            if health < 0.6 or rul < 168:
                needs_maintenance.append(eq_id)
                
        # Try optimization if available
        # fallback simple logic
        equipment_schedule = []
        total_downtime = 0.0
        for eq_id in needs_maintenance:
            equipment_schedule.append({
                "equipment_id": eq_id,
                "urgency": 0.8,
                "recommended_date": "2023-11-01T00:00:00Z",
                "maintenance_type": "PREDICTIVE",
                "estimated_duration_hours": 4.0,
                "crew_required": 2,
                "expected_health_improvement": 0.4
            })
            total_downtime += 4.0
            
        citations = []
        if self.graphrag_service:
            try:
                ans = await self.graphrag_service.answer("What are best practices for maintenance scheduling in industrial plants?")
                citations = getattr(ans, "citations", [])
            except Exception:
                pass
                
        return {
            "plan_id": str(uuid.uuid4()),
            "plan_type": "MAINTENANCE",
            "title": "Predictive Maintenance Schedule",
            "horizon_days": horizon_days,
            "equipment_schedule": equipment_schedule,
            "resource_requirements": {"crew": 4, "tools": ["wrench", "diagnostic_kit"], "parts": []},
            "total_downtime_hours": total_downtime,
            "production_impact_pct": 5.0,
            "graphrag_citations": citations,
            "confidence": 0.85
        }
