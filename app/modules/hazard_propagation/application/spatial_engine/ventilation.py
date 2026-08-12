from __future__ import annotations
import math
from app.core.logging import get_logger

log = get_logger(__name__)

class VentilationModel:
    """Model for ventilation and air changes."""

    def __init__(self, ventilation_rate: float = 0.1) -> None:
        self._ventilation_rate = ventilation_rate

    def compute_dilution_factor(self, ventilation_rate: float, volume_m3: float, time_minutes: float) -> float:
        """Compute dilution factor (C/C0)."""
        return math.exp(-ventilation_rate * time_minutes / 60.0)

    def compute_safe_time(self, initial_concentration: float, safe_threshold: float, ventilation_rate: float, volume_m3: float) -> float:
        """Compute time to reach safe threshold."""
        if initial_concentration <= 0 or safe_threshold >= initial_concentration:
            return 0.0
        if ventilation_rate <= 0:
            return float('inf')
            
        t = (-60.0 / ventilation_rate) * math.log(safe_threshold / initial_concentration)
        return max(0.0, t)

    def get_zone_ventilation(self, zone_id: str, zone_metadata: dict) -> float:
        """Get ventilation rate for zone."""
        return zone_metadata.get("ventilation_rate", self._ventilation_rate)

    def adjust_gas_concentration(self, concentration: float, ventilation_rate: float, dt_minutes: float) -> float:
        """Adjust concentration for ventilation."""
        return concentration * math.exp(-ventilation_rate * dt_minutes / 60.0)

    def recommend_ventilation_increase(self, current_concentration: float, safe_threshold: float, volume_m3: float) -> dict:
        """Recommend ventilation increase for 30 min clearance."""
        if current_concentration <= safe_threshold:
            return {"required_rate": 0.0, "time_to_safe_minutes": 0.0, "action_description": "Safe"}
            
        # Target time = 30 mins
        # safe = current * exp(-rate * 30 / 60) -> ln(safe/current) = -rate/2 -> rate = -2 * ln(safe/current)
        required_rate = -2.0 * math.log(safe_threshold / current_concentration)
        
        return {
            "required_rate": required_rate,
            "time_to_safe_minutes": 30.0,
            "action_description": f"Increase ventilation to {required_rate:.2f} ACH to clear in 30 mins."
        }
