from __future__ import annotations
import asyncio
import time
from typing import Any
from app.core.logging import get_logger

log = get_logger(__name__)

class ExposureService:
    def __init__(self) -> None:
        self._worker_calc = None
        self._equipment_calc = None
        self._zone_calc = None
        self._dose_acc = None
        self._init_calculators()
    
    def _init_calculators(self) -> None:
        try:
            from app.modules.hazard_propagation.application.exposure_engine.worker_exposure import WorkerExposureCalculator
            from app.modules.hazard_propagation.application.exposure_engine.equipment_exposure import EquipmentExposureCalculator
            from app.modules.hazard_propagation.application.exposure_engine.zone_exposure import ZoneExposureCalculator
            from app.modules.hazard_propagation.application.exposure_engine.dose_accumulation import DoseAccumulator
            self._worker_calc = WorkerExposureCalculator()
            self._equipment_calc = EquipmentExposureCalculator()
            self._zone_calc = ZoneExposureCalculator()
            self._dose_acc = DoseAccumulator()
        except ImportError as e:
            log.warning(f"Exposure calculators not available: {e}")

    async def assess(self, propagation_id: str, affected_nodes: dict[str, Any], worker_ids: list[str], zone_ids: list[str], equipment_ids: list[str], hazard_type: str, context: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        async def mock_worker():
            return {"worker_exposure": []}
        async def mock_equip():
            return {"equipment_exposure": []}
        async def mock_zone():
            return {"zone_exposure": []}

        tasks = []
        tasks.append(self._worker_calc.calculate(worker_ids, affected_nodes, hazard_type, context) if self._worker_calc else mock_worker())
        tasks.append(self._equipment_calc.calculate(equipment_ids, affected_nodes, hazard_type, context) if self._equipment_calc else mock_equip())
        tasks.append(self._zone_calc.calculate(zone_ids, affected_nodes, hazard_type, context) if self._zone_calc else mock_zone())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        worker_exposure = results[0].get("worker_exposure", []) if isinstance(results[0], dict) else []
        equipment_exposure = results[1].get("equipment_exposure", []) if isinstance(results[1], dict) else []
        zone_exposure = results[2].get("zone_exposure", []) if isinstance(results[2], dict) else []
        
        latency_ms = (time.perf_counter() - t0) * 1000
        return {
            "propagation_id": propagation_id,
            "worker_exposure": worker_exposure,
            "equipment_exposure": equipment_exposure,
            "zone_exposure": zone_exposure,
            "latency_ms": latency_ms
        }

    async def check_thresholds(self, assessment: dict[str, Any], thresholds: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        exceeded = []
        for zone in assessment.get("zone_exposure", []):
            if zone.get("exposure_level", "LOW") in ["HIGH", "CRITICAL"]:
                exceeded.append({
                    "zone_id": zone.get("zone_id"),
                    "exposure_level": zone.get("exposure_level"),
                    "worker_count": len(assessment.get("worker_exposure", [])),
                    "threshold_exceeded": True
                })
        return exceeded
