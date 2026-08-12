from __future__ import annotations

import time
import uuid
import asyncio
from typing import Any, List
from app.core.logging import get_logger

log = get_logger(__name__)


class SimulationRunner:
    async def run(self, twin_id: str, sim_type: str, state: dict, params: dict) -> dict:
        await asyncio.sleep(0.1) # Simulate work
        return {
            "simulation_id": str(uuid.uuid4()),
            "twin_id": twin_id,
            "simulation_type": sim_type,
            "status": "COMPLETED",
            "results": {"metric": 42.0},
            "created_at": time.time(),
        }


class TwinSimulationService:
    def __init__(self, graphrag_service: Any = None) -> None:
        self.graphrag_service = graphrag_service
        self._runner = SimulationRunner()

    async def run(self, twin_id: str, simulation_type: str, twin_state: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        try:
            sim_res = await self._runner.run(twin_id, simulation_type, twin_state, parameters)
            
            if self.graphrag_service:
                try:
                    q = f"Provide contextual background for simulation type {simulation_type} on twin {twin_id}"
                    gr_res = await self.graphrag_service.answer(q)
                    sim_res["graphrag_context"] = gr_res.answer
                    sim_res["citations"] = getattr(gr_res, "citations", [])
                except Exception as e:
                    log.warning(f"GraphRAG enrichment failed during simulation: {e}")
                    
            return sim_res
        except Exception as e:
            log.error(f"Simulation run failed: {e}")
            return {"status": "FAILED", "error": str(e)}
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"TwinSimulationService.run completed in {latency_ms:.2f}ms")

    async def run_concurrent(self, twin_id: str, simulations: List[dict[str, Any]], twin_state: dict[str, Any]) -> List[dict[str, Any]]:
        t0 = time.perf_counter()
        try:
            tasks = []
            for sim in simulations:
                tasks.append(self.run(twin_id, sim.get("simulation_type", "default"), twin_state, sim.get("parameters", {})))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [res if isinstance(res, dict) else {"status": "FAILED", "error": str(res)} for res in results]
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"TwinSimulationService.run_concurrent completed in {latency_ms:.2f}ms")

    async def explain_simulation(self, simulation_id: str, simulation_data: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        try:
            explanation = {
                "simulation_id": simulation_id,
                "assumptions": ["Standard operating conditions", "No external anomalies"],
                "timeline": "Mocked timeline events",
                "recommended_actions": ["Review output metrics"]
            }
            if self.graphrag_service:
                try:
                    q = f"Explain the simulation results for {simulation_id} given data: {simulation_data}"
                    gr_res = await self.graphrag_service.answer(q)
                    explanation["graphrag_citations"] = getattr(gr_res, "citations", [])
                    explanation["summary"] = gr_res.answer
                except Exception as e:
                    log.warning(f"GraphRAG explanation failed: {e}")
            return explanation
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"TwinSimulationService.explain_simulation completed in {latency_ms:.2f}ms")
