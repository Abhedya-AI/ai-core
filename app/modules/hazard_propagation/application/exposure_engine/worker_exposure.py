from __future__ import annotations

import math
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

class WorkerExposureCalculator:
    def __init__(self, idlh_thresholds: dict[str, float] | None = None) -> None:
        self._idlh = idlh_thresholds or {
            "GAS_LEAK": 1000.0, "TOXIC_GAS": 50.0, 
            "CHEMICAL_SPILL": 200.0, "SMOKE": 10000.0,
            "STEAM_LEAK": 5000.0, "DEFAULT": 1000.0,
        }
    
    async def compute_worker_exposure(
        self, worker_id: str, zone_id: str, hazard_type: str,
        concentration_ppm: float, ppe_score: float, duration_minutes: float
    ) -> dict:
        ppe_effectiveness = self.compute_ppe_protection(ppe_score, hazard_type)
        effective_concentration = concentration_ppm * (1.0 - ppe_effectiveness)
        dose = self.compute_dose(effective_concentration, duration_minutes)
        idlh = self._idlh.get(hazard_type, self._idlh.get("DEFAULT", 1000.0))
        exposure_score = min(1.0, effective_concentration / max(1e-9, idlh))
        exposure_level = self.classify_exposure_level(exposure_score)
        time_to_unsafe = self.estimate_time_to_unsafe(concentration_ppm, idlh, ppe_effectiveness)
        requires_evacuation = exposure_level.value in (ExposureLevel.HIGH.value, ExposureLevel.CRITICAL.value, ExposureLevel.LETHAL.value)
        lethal_risk = self.assess_lethal_risk(dose, hazard_type)
        
        return {
            "worker_id": worker_id,
            "zone_id": zone_id,
            "hazard_type": hazard_type,
            "ppe_effectiveness": ppe_effectiveness,
            "effective_concentration": effective_concentration,
            "dose": dose,
            "exposure_score": exposure_score,
            "exposure_level": exposure_level.value,
            "time_to_unsafe": time_to_unsafe,
            "requires_evacuation": requires_evacuation,
            "lethal_risk": lethal_risk
        }
    
    def compute_dose(self, concentration_ppm: float, duration_minutes: float) -> float:
        return concentration_ppm * duration_minutes
    
    def compute_ppe_protection(self, ppe_score: float, hazard_type: str) -> float:
        if hazard_type == "TOXIC_GAS":
            base = 0.95 if ppe_score > 0.9 else 0.5
        elif hazard_type == "GAS_LEAK":
            base = 0.8
        elif hazard_type == "SMOKE":
            base = 0.85
        else:
            base = 0.6
        return max(0.0, min(1.0, base * ppe_score))
    
    def estimate_time_to_unsafe(
        self, concentration_ppm: float, idlh: float, ppe_effectiveness: float
    ) -> float | None:
        effective_c = concentration_ppm * (1.0 - ppe_effectiveness)
        if effective_c <= 0:
            return None
        return float(idlh / effective_c)
    
    def assess_lethal_risk(
        self, dose: float, hazard_type: str, probit_params: dict | None = None
    ) -> float:
        a = (probit_params or {}).get("a", -8.3)
        b = (probit_params or {}).get("b", 1.0)
        pr = a + b * math.log(max(1e-9, dose))
        return max(0.0, min(1.0, pr / 10.0))
    
    def classify_exposure_level(self, exposure_score: float) -> ExposureLevel:
        return ExposureLevel.from_score(exposure_score)
