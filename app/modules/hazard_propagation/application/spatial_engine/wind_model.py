from __future__ import annotations
import math
from app.core.logging import get_logger

log = get_logger(__name__)

class WindModel:
    """Model for wind effects on hazard dispersion."""

    def __init__(self, wind_speed_ms: float = 0.0, wind_direction_deg: float = 0.0) -> None:
        self.wind_speed_ms = wind_speed_ms
        self.wind_direction_deg = wind_direction_deg

    def compute_wind_factor(self, source_coords: dict, target_coords: dict) -> float:
        """Compute wind factor using cosine of angle."""
        sx = source_coords.get("x", 0.0)
        sy = source_coords.get("y", 0.0)
        tx = target_coords.get("x", 0.0)
        ty = target_coords.get("y", 0.0)
        
        dx = tx - sx
        dy = ty - sy
        
        if dx == 0 and dy == 0:
            return 1.0
            
        path_angle = math.degrees(math.atan2(dy, dx))
        angle_diff = path_angle - self.wind_direction_deg
        
        cos_val = math.cos(math.radians(angle_diff))
        
        # Base factor 1.0, influenced by wind speed
        factor = 1.0 + (self.wind_speed_ms / 10.0) * cos_val
        return max(0.5, min(2.0, factor))

    def compute_dispersion_params(self, distance_meters: float, stability_class: str = "D") -> tuple[float, float]:
        """Compute Gaussian plume dispersion parameters."""
        x = max(1.0, distance_meters)
        
        if stability_class == "A":
            sigma_y = 0.22 * (x ** 0.90)
            sigma_z = 0.20 * (x ** 0.86)
        elif stability_class == "F":
            sigma_y = 0.22 * (x ** 0.85)
            sigma_z = 0.12 * (x ** 0.75)
        else: # Default D
            sigma_y = 0.22 * (x ** 0.89)
            sigma_z = 0.16 * (x ** 0.82)
            
        return sigma_y, sigma_z

    def estimate_concentration(self, Q_gs: float, x_m: float, y_m: float, z_m: float = 0.0, H_m: float = 0.0) -> float:
        """Estimate concentration using Gaussian plume model."""
        if x_m <= 0:
            return 0.0
            
        u = max(0.1, self.wind_speed_ms)
        sy, sz = self.compute_dispersion_params(x_m)
        
        if sy <= 0 or sz <= 0:
            return 0.0
            
        term1 = Q_gs / (math.pi * u * sy * sz)
        term2 = math.exp(-(y_m**2) / (2 * sy**2))
        term3 = math.exp(-((z_m - H_m)**2) / (2 * sz**2)) + math.exp(-((z_m + H_m)**2) / (2 * sz**2))
        
        return term1 * term2 * term3

    def adjust_spread_rate(self, base_rate: float, source_coords: dict, target_coords: dict) -> float:
        """Adjust spread rate based on wind."""
        factor = self.compute_wind_factor(source_coords, target_coords)
        return base_rate * factor
