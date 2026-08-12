from __future__ import annotations

import time
import uuid
import asyncio
from typing import Any, List
from app.core.logging import get_logger

log = get_logger(__name__)


class BaseOptimizer:
    async def optimize(self, twin_id: str, twin_state: dict, constraints: dict) -> dict:
        return {"score": 0.9, "recommendations": []}


class EnergyOptimizer(BaseOptimizer): pass
class ThroughputOptimizer(BaseOptimizer): pass
class SafetyOptimizer(BaseOptimizer): pass
class CostOptimizer(BaseOptimizer): pass
class EmissionsOptimizer(BaseOptimizer): pass
class ReliabilityOptimizer(BaseOptimizer): pass
class QualityOptimizer(BaseOptimizer): pass


class TwinOptimizationService:
    def __init__(self, graphrag_service: Any = None) -> None:
        self.graphrag_service = graphrag_service
        self._registry = {
            "energy": EnergyOptimizer(),
            "throughput": ThroughputOptimizer(),
            "safety": SafetyOptimizer(),
            "cost": CostOptimizer(),
            "emissions": EmissionsOptimizer(),
            "reliability": ReliabilityOptimizer(),
            "quality": QualityOptimizer(),
        }

    async def optimize(
        self, twin_id: str, target: str, twin_state: dict[str, Any], constraints: dict[str, Any]
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        try:
            optimizer = self._registry.get(target)
            if not optimizer:
                raise ValueError(f"No optimizer found for target: {target}")

            result = await optimizer.optimize(twin_id, twin_state, constraints)
            opt_dict = {
                "optimization_id": str(uuid.uuid4()),
                "twin_id": twin_id,
                "target": target,
                "status": "COMPLETED",
                "result": result,
                "created_at": time.time(),
            }

            if self.graphrag_service:
                try:
                    q = f"Provide context for optimizing {target} for twin {twin_id}"
                    gr_res = await self.graphrag_service.answer(q)
                    opt_dict["graphrag_context"] = gr_res.answer
                    opt_dict["citations"] = getattr(gr_res, "citations", [])
                except Exception as e:
                    log.warning(f"GraphRAG enrichment failed during optimization: {e}")

            return opt_dict
        except Exception as e:
            log.error(f"Optimization failed: {e}")
            return {"status": "FAILED", "error": str(e), "target": target}
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"TwinOptimizationService.optimize completed in {latency_ms:.2f}ms")

    async def optimize_multiple(
        self, twin_id: str, targets: List[str], twin_state: dict[str, Any], constraints: dict[str, Any]
    ) -> List[dict[str, Any]]:
        t0 = time.perf_counter()
        try:
            tasks = [
                self.optimize(twin_id, target, twin_state, constraints)
                for target in targets
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [res if isinstance(res, dict) else {"status": "FAILED", "error": str(res)} for res in results]
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"TwinOptimizationService.optimize_multiple completed in {latency_ms:.2f}ms")

    def get_available_targets(self) -> List[str]:
        return list(self._registry.keys())
