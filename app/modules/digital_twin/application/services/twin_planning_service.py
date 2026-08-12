from __future__ import annotations

import time
import uuid
from typing import Any, List
from app.core.logging import get_logger

log = get_logger(__name__)


class MaintenancePlanner:
    async def generate(self, twin_id: str, twin_state: dict, entity_id: str, horizon_days: int, context: dict) -> dict:
        return {"plan_id": str(uuid.uuid4()), "type": "maintenance", "actions": [{"task": "Inspect valve", "due_in_days": horizon_days // 2}]}


class EmergencyPlanner:
    async def generate(self, twin_id: str, twin_state: dict, entity_id: str, horizon_days: int, context: dict) -> dict:
        return {"plan_id": str(uuid.uuid4()), "type": "emergency", "actions": [{"task": "Evacuate sector", "priority": "CRITICAL"}]}


class ResourcePlanner:
    async def generate(self, twin_id: str, twin_state: dict, entity_id: str, horizon_days: int, context: dict) -> dict:
        return {"plan_id": str(uuid.uuid4()), "type": "resource", "allocations": [{"resource": "Power", "amount": 500}]}


class BusinessContinuityPlanner:
    async def generate(self, twin_id: str, twin_state: dict, entity_id: str, horizon_days: int, context: dict) -> dict:
        return {"plan_id": str(uuid.uuid4()), "type": "continuity", "strategies": ["Reroute traffic", "Activate backup generator"]}


class TwinPlanningService:
    def __init__(self, graphrag_service: Any = None) -> None:
        self.graphrag_service = graphrag_service
        self._planners = {
            "maintenance": MaintenancePlanner(),
            "emergency": EmergencyPlanner(),
            "resource": ResourcePlanner(),
            "continuity": BusinessContinuityPlanner(),
        }

    async def generate(
        self,
        twin_id: str,
        plan_type: str,
        twin_state: dict[str, Any],
        entity_id: str,
        horizon_days: int = 30,
        context: dict[str, Any] = None,
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        context = context or {}
        
        try:
            planner = self._planners.get(plan_type)
            if not planner:
                raise ValueError(f"Unknown plan type: {plan_type}")

            plan = await planner.generate(twin_id, twin_state, entity_id, horizon_days, context)
            
            # Enrich with GraphRAG if available
            if self.graphrag_service:
                try:
                    q = f"Generate {plan_type} planning context for twin {twin_id}, entity {entity_id}"
                    gr_res = await self.graphrag_service.answer(q)
                    plan["graphrag_context"] = gr_res.answer
                    plan["citations"] = getattr(gr_res, "citations", [])
                except Exception as e:
                    log.warning(f"GraphRAG enrichment failed during planning: {e}")

            plan["twin_id"] = twin_id
            plan["entity_id"] = entity_id
            plan["horizon_days"] = horizon_days
            plan["created_at"] = time.time()
            return plan
        except Exception as e:
            log.error(f"Planning generation failed: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"TwinPlanningService.generate completed in {latency_ms:.2f}ms")

    async def get_available_plan_types(self) -> List[str]:
        t0 = time.perf_counter()
        types = list(self._planners.keys())
        latency_ms = (time.perf_counter() - t0) * 1000
        log.info(f"get_available_plan_types completed in {latency_ms:.2f}ms")
        return types
