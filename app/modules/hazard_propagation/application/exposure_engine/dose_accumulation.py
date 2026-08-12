from __future__ import annotations

import numpy as np
from app.core.logging import get_logger

log = get_logger(__name__)

class DoseAccumulator:
    def __init__(self, time_step_minutes: float = 1.0) -> None:
        self.time_step_minutes = max(0.1, time_step_minutes)

    def accumulate_dose(self, concentration_series: list[float], time_step_minutes: float | None = None) -> float:
        if not concentration_series:
            return 0.0
        dt = time_step_minutes if time_step_minutes is not None else self.time_step_minutes
        if len(concentration_series) == 1:
            return float(concentration_series[0] * dt)
        return float(np.trapz(concentration_series, dx=dt))

    def compute_permissible_exposure_limit(self, hazard_type: str, duration_hours: float) -> float:
        pel_8h = {
            "GAS_LEAK": 50.0,
            "TOXIC_GAS": 2.0,
            "CHEMICAL_SPILL": 100.0,
            "SMOKE": 50.0,
            "DEFAULT": 50.0
        }
        base_pel = pel_8h.get(hazard_type, pel_8h["DEFAULT"])
        dur = max(0.1, duration_hours)
        return float(base_pel * ((8.0 / dur) ** 0.5))

    def check_pel_exceeded(self, accumulated_dose: float, hazard_type: str, duration_hours: float) -> bool:
        pel = self.compute_permissible_exposure_limit(hazard_type, duration_hours)
        return accumulated_dose > (pel * duration_hours * 60.0)

    def compute_worker_dose_profile(self, concentration_series: list[float], ppe_effectiveness: float) -> dict:
        eff_series = [max(0.0, c * (1.0 - ppe_effectiveness)) for c in concentration_series]
        cum_dose = self.accumulate_dose(eff_series)
        peak_c = max(eff_series) if eff_series else 0.0
        
        pel = self.compute_permissible_exposure_limit("DEFAULT", max(1, len(eff_series) * self.time_step_minutes / 60.0))
        time_above_pel = sum(1 for c in eff_series if c > pel) * self.time_step_minutes
        
        exceeded = self.check_pel_exceeded(cum_dose, "DEFAULT", max(1, len(eff_series) * self.time_step_minutes / 60.0))
        
        ld50_dose = 10000.0 
        lethal_frac = min(1.0, cum_dose / ld50_dose)
        
        return {
            "cumulative_dose": cum_dose,
            "peak_concentration": peak_c,
            "time_above_pel_minutes": time_above_pel,
            "pel_exceeded": exceeded,
            "lethal_dose_fraction": lethal_frac
        }

    def estimate_recovery_time(self, accumulated_dose: float, hazard_type: str) -> float | None:
        pel = self.compute_permissible_exposure_limit(hazard_type, 8.0)
        limit = pel * 60.0
        if accumulated_dose < limit:
            return None
        return float((accumulated_dose / limit) * 24.0)
