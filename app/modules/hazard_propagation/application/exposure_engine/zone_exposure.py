from __future__ import annotations

import math
from app.core.logging import get_logger

log = get_logger(__name__)

class ZoneExposureCalculator:
    def __init__(self) -> None:
        pass

    async def compute_zone_exposure(
        self, zone_id: str, zone_area_m2: float, worker_count: int, 
        equipment_ids: list[str], hazard_intensity: float, 
        concentration_ppm: float, hazard_type: str
    ) -> dict:
        exposure_score = min(1.0, hazard_intensity * 0.7 + (concentration_ppm / 10000.0) * 0.3)
        return {
            "zone_id": zone_id,
            "zone_area_m2": zone_area_m2,
            "worker_count": worker_count,
            "equipment_count": len(equipment_ids),
            "hazard_intensity": hazard_intensity,
            "concentration_ppm": concentration_ppm,
            "hazard_type": hazard_type,
            "exposure_score": exposure_score
        }

    def compute_aggregate_zone_risk(self, zones: list[dict]) -> dict:
        if not zones:
            return {
                "max_exposure_level": 0.0,
                "critical_zones": [],
                "total_workers_at_risk": 0,
                "total_equipment_at_risk": 0
            }
        max_exp = max(z.get("exposure_score", 0.0) for z in zones)
        critical = [z for z in zones if z.get("exposure_score", 0.0) > 0.7]
        return {
            "max_exposure_level": max_exp,
            "critical_zones": critical,
            "total_workers_at_risk": sum(z.get("worker_count", 0) for z in zones),
            "total_equipment_at_risk": sum(z.get("equipment_count", 0) for z in zones)
        }

    def rank_zones_by_exposure(self, zone_exposures: list[dict]) -> list[dict]:
        return sorted(zone_exposures, key=lambda x: x.get("exposure_score", 0.0), reverse=True)

    def find_zones_requiring_evacuation(self, zone_exposures: list[dict], evacuation_threshold_score: float = 0.5) -> list[str]:
        return [z.get("zone_id", "") for z in zone_exposures if z.get("exposure_score", 0.0) >= evacuation_threshold_score and z.get("zone_id")]

    def estimate_zone_clearance_time(
        self, zone_id: str, zone_area_m2: float, ventilation_rate: float, 
        current_concentration: float, safe_threshold: float
    ) -> float:
        if current_concentration <= safe_threshold or current_concentration <= 0:
            return 0.0
        if ventilation_rate <= 0:
            return 9999.0
        
        try:
            return float((-60.0 / ventilation_rate) * math.log(max(1e-9, safe_threshold / current_concentration)))
        except (ValueError, ZeroDivisionError):
            return 9999.0
