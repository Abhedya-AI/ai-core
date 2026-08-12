from __future__ import annotations
import asyncio
import time
from typing import Any
from app.core.logging import get_logger

log = get_logger(__name__)

class ContainmentService:
    def __init__(self, graphrag_service: Any = None, knowledge_service: Any = None) -> None:
        self.graphrag_service = graphrag_service
        self.knowledge_service = knowledge_service
        self._engines = None
        self._init_engines()

    def _init_engines(self) -> None:
        try:
            from app.modules.hazard_propagation.application.containment_engine.isolation_strategy import IsolationStrategyEngine
            from app.modules.hazard_propagation.application.containment_engine.valve_shutdown import ValveShutdownEngine
            from app.modules.hazard_propagation.application.containment_engine.barrier_deployment import BarrierDeploymentEngine
            from app.modules.hazard_propagation.application.containment_engine.safe_zones import SafeZoneEngine
            self._engines = {
                "isolation": IsolationStrategyEngine(),
                "valve": ValveShutdownEngine(),
                "barrier": BarrierDeploymentEngine(),
                "safe_zone": SafeZoneEngine()
            }
        except ImportError as e:
            log.warning(f"Containment engines not available: {e}")

    async def generate(self, propagation_id: str, hazard_type: str, source_node_id: str, affected_nodes: dict[str, Any], severity: str, context: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        async def run_mock(name):
            return {name: []}

        tasks = []
        if self._engines:
            tasks.append(self._engines["isolation"].generate(propagation_id, hazard_type, affected_nodes))
            tasks.append(self._engines["valve"].generate(propagation_id, source_node_id, affected_nodes))
            tasks.append(self._engines["barrier"].generate(propagation_id, hazard_type, affected_nodes))
            tasks.append(self._engines["safe_zone"].generate(propagation_id, hazard_type, affected_nodes))
        else:
            tasks = [run_mock("isolation"), run_mock("valve"), run_mock("barrier"), run_mock("safe_zone")]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        isolation = results[0] if not isinstance(results[0], Exception) else {}
        valve = results[1] if not isinstance(results[1], Exception) else {}
        barrier = results[2] if not isinstance(results[2], Exception) else {}
        safe_zones = results[3] if not isinstance(results[3], Exception) else {}

        latency_ms = (time.perf_counter() - t0) * 1000
        return {
            "propagation_id": propagation_id,
            "plan_id": f"cont_{propagation_id}",
            "isolation_strategies": isolation,
            "valve_shutdowns": valve,
            "barriers": barrier,
            "safe_zones": safe_zones,
            "latency_ms": latency_ms
        }
