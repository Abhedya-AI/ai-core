from __future__ import annotations

import time
import asyncio
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.application.simulation.base import AbstractSimulation, SimulationResult

from app.modules.digital_twin.application.simulation.what_if_simulation import WhatIfSimulation
from app.modules.digital_twin.application.simulation.emergency_simulation import EmergencySimulation
from app.modules.digital_twin.application.simulation.hazard_replay_simulation import HazardReplaySimulation
from app.modules.digital_twin.application.simulation.maintenance_simulation import MaintenanceSimulation
from app.modules.digital_twin.application.simulation.shutdown_simulation import ShutdownSimulation
from app.modules.digital_twin.application.simulation.production_simulation import ProductionSimulation
from app.modules.digital_twin.application.simulation.worker_movement_simulation import WorkerMovementSimulation
from app.modules.digital_twin.application.simulation.equipment_failure_simulation import EquipmentFailureSimulation
from app.modules.digital_twin.application.simulation.power_loss_simulation import PowerLossSimulation

log = get_logger(__name__)

class SimulationRunner:
    def __init__(self, graphrag_service: Any = None):
        self.graphrag_service = graphrag_service
        self._registry = self._build_registry()

    def _build_registry(self) -> dict[str, AbstractSimulation]:
        return {
            "WHAT_IF": WhatIfSimulation(),
            "EMERGENCY": EmergencySimulation(),
            "HAZARD_REPLAY": HazardReplaySimulation(),
            "MAINTENANCE": MaintenanceSimulation(),
            "SHUTDOWN": ShutdownSimulation(),
            "PRODUCTION": ProductionSimulation(),
            "WORKER_MOVEMENT": WorkerMovementSimulation(),
            "EQUIPMENT_FAILURE": EquipmentFailureSimulation(),
            "POWER_LOSS": PowerLossSimulation()
        }

    def get_available_types(self) -> list[str]:
        return list(self._registry.keys())

    async def run_simulation(self, simulation_type: str, twin_id: str, twin_state: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        sim_class = self._registry.get(simulation_type)
        if not sim_class:
            return {
                "simulation_id": "",
                "simulation_type": simulation_type,
                "status": "FAILED",
                "error": f"Unknown simulation type: {simulation_type}",
                "latency_ms": (time.perf_counter() - t0) * 1000
            }
            
        try:
            result = await sim_class.run(twin_state, parameters, self.graphrag_service)
            return {
                "simulation_id": result.simulation_id,
                "simulation_type": result.simulation_type,
                "status": result.status,
                "timeline": result.timeline,
                "summary": result.summary,
                "assumptions": result.assumptions,
                "kg_paths": result.kg_paths,
                "graphrag_citations": result.graphrag_citations,
                "risk_references": result.risk_references,
                "forecast_references": result.forecast_references,
                "hazard_references": result.hazard_references,
                "confidence": result.confidence,
                "alternative_scenarios": result.alternative_scenarios,
                "recommended_actions": result.recommended_actions,
                "latency_ms": result.latency_ms,
                "error": result.error
            }
        except Exception as e:
            log.exception(f"Simulation {simulation_type} failed: {e}")
            return {
                "simulation_id": "",
                "simulation_type": simulation_type,
                "status": "FAILED",
                "error": str(e),
                "latency_ms": (time.perf_counter() - t0) * 1000
            }

    async def run_concurrent_simulations(self, simulations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        tasks = []
        for sim in simulations:
            tasks.append(self.run_simulation(
                sim.get("simulation_type", ""),
                sim.get("twin_id", ""),
                sim.get("twin_state", {}),
                sim.get("parameters", {})
            ))
        return await asyncio.gather(*tasks)
