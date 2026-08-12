from __future__ import annotations
from typing import Any
from app.core.logging import get_logger

log = get_logger(__name__)

class HazardSupervisorBridge:
    def __init__(self) -> None:
        self._supervisor = None
        try:
            from app.modules.supervisor.supervisor_decision_engine import SupervisorDecisionEngine
            self._supervisor = SupervisorDecisionEngine()
        except Exception:
            pass
    
    async def notify_hazard_detected(self, propagation_result: dict[str, Any]) -> None:
        if self._supervisor:
            try:
                await self._supervisor.handle_event({"type": "HAZARD_DETECTED", "data": propagation_result})
            except Exception as exc:
                log.warning(f"Supervisor notification failed: {exc}")
        log.info(f"Hazard propagation supervisor notification: {propagation_result.get('hazard_type', 'UNKNOWN')} at {propagation_result.get('source_node_id', 'UNKNOWN')}")
    
    async def notify_critical_exposure(self, exposure_assessment: dict[str, Any]) -> None:
        if self._supervisor:
            try:
                await self._supervisor.handle_event({"type": "CRITICAL_EXPOSURE", "data": exposure_assessment})
            except Exception as exc:
                log.warning(f"Supervisor notification failed: {exc}")
        log.info("Critical exposure supervisor notification.")

    async def notify_cascade_detected(self, domino_effect: dict[str, Any]) -> None:
        if self._supervisor:
            try:
                await self._supervisor.handle_event({"type": "CASCADE_DETECTED", "data": domino_effect})
            except Exception as exc:
                log.warning(f"Supervisor notification failed: {exc}")
        log.info("Cascade detected supervisor notification.")

    async def notify_evacuation_required(self, evacuation_rec: dict[str, Any]) -> None:
        if self._supervisor:
            try:
                await self._supervisor.handle_event({"type": "EVACUATION_REQUIRED", "data": evacuation_rec})
            except Exception as exc:
                log.warning(f"Supervisor notification failed: {exc}")
        log.info("Evacuation required supervisor notification.")

    async def notify_simulation_completed(self, simulation_result: dict[str, Any]) -> None:
        if self._supervisor:
            try:
                await self._supervisor.handle_event({"type": "SIMULATION_COMPLETED", "data": simulation_result})
            except Exception as exc:
                log.warning(f"Supervisor notification failed: {exc}")
        log.info("Simulation completed supervisor notification.")
