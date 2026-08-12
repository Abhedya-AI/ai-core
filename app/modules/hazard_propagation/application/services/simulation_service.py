from __future__ import annotations
import time
from typing import Any
from app.core.logging import get_logger

log = get_logger(__name__)

class SimulationService:
    def __init__(self) -> None:
        self._simulators = None
        self._init_simulators()

    def _init_simulators(self) -> None:
        try:
            from app.modules.hazard_propagation.application.simulation_engine.what_if import WhatIfSimulator
            from app.modules.hazard_propagation.application.simulation_engine.containment_sim import ContainmentSimulator
            from app.modules.hazard_propagation.application.simulation_engine.evacuation_sim import EvacuationSimulator
            from app.modules.hazard_propagation.application.simulation_engine.multi_hazard_sim import MultiHazardSimulator
            self._simulators = {
                "what_if": WhatIfSimulator(),
                "containment": ContainmentSimulator(),
                "evacuation": EvacuationSimulator(),
                "multi": MultiHazardSimulator()
            }
        except ImportError as e:
            log.warning(f"Simulators not available: {e}")

    async def run_what_if(self, scenario: dict[str, Any], time_horizon_minutes: int = 60) -> dict[str, Any]:
        t0 = time.perf_counter()
        result = {}
        if self._simulators:
            try:
                result = await self._simulators["what_if"].run(scenario, time_horizon_minutes)
            except Exception as e:
                log.warning(f"Error in what_if simulation: {e}")
        latency_ms = (time.perf_counter() - t0) * 1000
        return {"simulation_id": f"sim_wi_{time.time()}", "result": result, "latency_ms": latency_ms}

    async def run_containment_sim(self, propagation_state: dict[str, Any], containment_plan: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        result = {}
        if self._simulators:
            try:
                result = await self._simulators["containment"].run(propagation_state, containment_plan)
            except Exception as e:
                log.warning(f"Error in containment sim: {e}")
        latency_ms = (time.perf_counter() - t0) * 1000
        return {"simulation_id": f"sim_cont_{time.time()}", "result": result, "latency_ms": latency_ms}

    async def run_evacuation_sim(self, workers_by_zone: dict[str, list[str]], routes: dict[str, Any], hazard_timeline: list[dict[str, Any]]) -> dict[str, Any]:
        t0 = time.perf_counter()
        result = {}
        if self._simulators:
            try:
                result = await self._simulators["evacuation"].run(workers_by_zone, routes, hazard_timeline)
            except Exception as e:
                log.warning(f"Error in evacuation sim: {e}")
        latency_ms = (time.perf_counter() - t0) * 1000
        return {"simulation_id": f"sim_evac_{time.time()}", "result": result, "latency_ms": latency_ms}

    async def run_multi_hazard(self, scenarios: list[dict[str, Any]]) -> dict[str, Any]:
        t0 = time.perf_counter()
        result = {}
        if self._simulators:
            try:
                result = await self._simulators["multi"].run(scenarios)
            except Exception as e:
                log.warning(f"Error in multi hazard sim: {e}")
        latency_ms = (time.perf_counter() - t0) * 1000
        return {"simulation_id": f"sim_mh_{time.time()}", "result": result, "latency_ms": latency_ms}
