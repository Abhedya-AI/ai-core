from __future__ import annotations

from app.core.logging import get_logger

log = get_logger(__name__)

try:
    from app.modules.hazard_propagation.domain.enums import ExposureLevel
except ImportError:
    from enum import Enum
    class ExposureLevel(str, Enum):
        NONE = "NONE"
        MINIMAL = "MINIMAL"
        LOW = "LOW"
        MODERATE = "MODERATE"
        HIGH = "HIGH"
        CRITICAL = "CRITICAL"
        LETHAL = "LETHAL"
        
        @classmethod
        def from_score(cls, s: float) -> "ExposureLevel":
            return (cls.NONE if s < 0.05 else 
                    cls.MINIMAL if s < 0.15 else 
                    cls.LOW if s < 0.30 else 
                    cls.MODERATE if s < 0.50 else 
                    cls.HIGH if s < 0.70 else 
                    cls.CRITICAL if s < 0.90 else cls.LETHAL)

class EquipmentExposureCalculator:
    def __init__(self) -> None:
        pass

    async def compute_equipment_exposure(
        self, equipment_id: str, equipment_type: str, hazard_type: str, 
        intensity: float, temperature_celsius: float, duration_minutes: float
    ) -> dict:
        if hazard_type in ("FIRE", "STEAM_LEAK", "SMOKE"):
            damage_prob = self.compute_thermal_damage(temperature_celsius, equipment_type, duration_minutes)
        elif hazard_type in ("EXPLOSION", "HIGH_PRESSURE"):
            damage_prob = self.compute_pressure_damage(intensity * 100, equipment_type)
        elif hazard_type in ("CHEMICAL_SPILL", "TOXIC_GAS", "GAS_LEAK"):
            damage_prob = self.compute_corrosion_risk(hazard_type, equipment_type, intensity * 1000, duration_minutes)
        else:
            damage_prob = intensity * 0.5
            
        exposure_level = ExposureLevel.from_score(damage_prob).value
        op_impact = damage_prob * 100.0
        time_to_fail = self.estimate_time_to_failure(intensity, equipment_type, hazard_type)
        
        return {
            "equipment_id": equipment_id,
            "exposure_level": exposure_level,
            "damage_probability": damage_prob,
            "operational_impact_pct": op_impact,
            "time_to_failure_minutes": time_to_fail
        }

    def compute_thermal_damage(self, temperature_celsius: float, equipment_type: str, duration_minutes: float) -> float:
        if equipment_type == "ELECTRONICS":
            safe, fail = 70.0, 200.0
        elif equipment_type == "MECHANICAL":
            safe, fail = 200.0, 500.0
        else:
            safe, fail = 400.0, 550.0
            
        if temperature_celsius <= safe:
            damage = 0.0
        elif temperature_celsius >= fail:
            damage = 1.0
        else:
            damage = (temperature_celsius - safe) / (fail - safe)
            
        duration_factor = min(1.0, max(0.0, duration_minutes / 60.0))
        return max(0.0, min(1.0, damage * max(0.2, duration_factor)))

    def compute_corrosion_risk(self, chemical_type: str, material: str, concentration_ppm: float, duration_minutes: float) -> float:
        rate = 0.01 * (concentration_ppm / 1000.0)
        damage = rate * duration_minutes / (60.0 * 24.0 * 365.0)
        return max(0.0, min(1.0, damage))

    def compute_pressure_damage(self, overpressure_bar: float, equipment_type: str) -> float:
        if equipment_type == "VESSEL":
            thresh = 5.0
        elif equipment_type == "PIPE":
            thresh = 10.0
        else:
            thresh = 20.0
            
        if overpressure_bar <= 0:
            return 0.0
        if overpressure_bar >= 2 * thresh:
            return 1.0
        if overpressure_bar == thresh:
            return 0.7
            
        if overpressure_bar < thresh:
            return (overpressure_bar / thresh) * 0.7
        else:
            return 0.7 + ((overpressure_bar - thresh) / thresh) * 0.3

    def estimate_time_to_failure(self, intensity: float, equipment_type: str, hazard_type: str) -> float | None:
        if intensity < 0.2:
            return None
        base_time = {"ELECTRONICS": 30.0, "MECHANICAL": 120.0}.get(equipment_type, 60.0)
        return float(base_time * (1.0 - intensity))

    def assess_operational_impact(self, equipment_ids: list[str], exposure_results: list[dict]) -> dict:
        total = len(equipment_ids)
        if total == 0:
            return {"affected_count": 0, "critical_count": 0, "production_impact_pct": 0.0, "estimated_recovery_hours": 0.0}
            
        affected = [r for r in exposure_results if r.get("damage_probability", 0) > 0.1]
        critical = [r for r in exposure_results if r.get("damage_probability", 0) > 0.7]
        
        mean_damage = sum(r.get("damage_probability", 0) for r in exposure_results) / total if total > 0 else 0.0
        
        return {
            "affected_count": len(affected),
            "critical_count": len(critical),
            "production_impact_pct": float(len(critical) / max(1, total) * 100.0),
            "estimated_recovery_hours": float(mean_damage * 24.0)
        }
