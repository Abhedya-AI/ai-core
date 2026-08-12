from __future__ import annotations
import math
from app.core.logging import get_logger

log = get_logger(__name__)

class HazardGrowthDecayModel:
    """Model for hazard growth and decay dynamics."""

    def __init__(self, growth_rate: float = 0.1, decay_rate: float = 0.05) -> None:
        self.growth_rate = growth_rate
        self.decay_rate = decay_rate

    def compute_growth(self, intensity: float, dt: float, fuel_available: bool = True) -> float:
        """Compute generic hazard growth."""
        if fuel_available:
            # Logistic growth
            new_i = intensity + self.growth_rate * intensity * (1.0 - intensity) * dt
        else:
            new_i = self.compute_decay(intensity, dt)
        return max(0.0, min(1.0, new_i))

    def compute_decay(self, intensity: float, dt: float, containment_factor: float = 0.0) -> float:
        """Compute hazard decay."""
        new_i = intensity * math.exp(-self.decay_rate * (1.0 + containment_factor) * dt)
        return max(0.0, min(1.0, new_i))

    def compute_fire_growth(self, intensity: float, fuel_load: float, ventilation: float, dt: float) -> float:
        """Compute fire specific growth."""
        alpha = 0.012 * fuel_load * max(0.1, 1.0 - ventilation)
        new_i = intensity + alpha * (intensity ** 0.5) * dt
        return max(0.0, min(1.0, new_i))

    def compute_gas_decay(self, concentration: float, ventilation_rate: float, dt: float) -> float:
        """Compute gas specific decay."""
        new_c = concentration * math.exp(-ventilation_rate * dt / 60.0)
        return max(0.0, new_c)

    def compute_heat_evolution(self, temperature: float, ambient_temp: float, heat_source: float, thermal_mass: float, dt: float) -> float:
        """Compute temperature evolution."""
        dT = (heat_source - 0.5 * (temperature - ambient_temp)) / max(1.0, thermal_mass) * dt
        return temperature + dT

    def estimate_hazard_lifetime(self, initial_intensity: float, decay_rate: float) -> float:
        """Estimate time until intensity decays to 0.05."""
        if initial_intensity <= 0.05:
            return 0.0
            
        i0 = max(1e-9, initial_intensity)
        dr = max(1e-9, decay_rate)
        
        t = math.log(i0 / 0.05) / dr
        return max(0.0, t)
