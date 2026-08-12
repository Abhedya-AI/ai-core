from __future__ import annotations
from app.core.logging import get_logger

log = get_logger(__name__)

CASCADE_RULES: dict[str, list[dict]] = {
    "GAS_LEAK": [
        {"triggers": "EXPLOSION", "intensity_threshold": 0.3, "probability": 0.6, "time_minutes": 5},
        {"triggers": "FIRE", "intensity_threshold": 0.5, "probability": 0.4, "time_minutes": 10},
    ],
    "EXPLOSION": [
        {"triggers": "FIRE", "intensity_threshold": 0.2, "probability": 0.85, "time_minutes": 1},
        {"triggers": "STRUCTURAL_COLLAPSE", "intensity_threshold": 0.7, "probability": 0.5, "time_minutes": 2},
        {"triggers": "POWER_FAILURE", "intensity_threshold": 0.4, "probability": 0.7, "time_minutes": 3},
    ],
    "FIRE": [
        {"triggers": "SMOKE", "intensity_threshold": 0.1, "probability": 0.95, "time_minutes": 1},
        {"triggers": "POWER_FAILURE", "intensity_threshold": 0.6, "probability": 0.5, "time_minutes": 15},
        {"triggers": "STRUCTURAL_COLLAPSE", "intensity_threshold": 0.8, "probability": 0.3, "time_minutes": 30},
    ],
    "POWER_FAILURE": [
        {"triggers": "ELECTRICAL_FAULT", "intensity_threshold": 0.3, "probability": 0.7, "time_minutes": 2},
    ],
    "STRUCTURAL_COLLAPSE": [
        {"triggers": "FLOOD", "intensity_threshold": 0.5, "probability": 0.3, "time_minutes": 60},
    ],
    "CHEMICAL_SPILL": [
        {"triggers": "TOXIC_GAS", "intensity_threshold": 0.4, "probability": 0.6, "time_minutes": 10},
        {"triggers": "FIRE", "intensity_threshold": 0.6, "probability": 0.4, "time_minutes": 20},
    ],
    "STEAM_LEAK": [
        {"triggers": "STRUCTURAL_COLLAPSE", "intensity_threshold": 0.7, "probability": 0.2, "time_minutes": 30},
    ],
    "HIGH_PRESSURE": [
        {"triggers": "EXPLOSION", "intensity_threshold": 0.5, "probability": 0.55, "time_minutes": 5},
        {"triggers": "STRUCTURAL_COLLAPSE", "intensity_threshold": 0.8, "probability": 0.35, "time_minutes": 10},
    ],
}

class CascadeDetector:
    """Detects hazard cascades."""

    def build_cascade_rules(self) -> dict:
        """Return cascade rules."""
        return CASCADE_RULES

    def detect_cascades(self, hazard_type: str, current_intensity: float, zone_conditions: dict) -> list[dict]:
        """Detect potential cascaded hazards."""
        cascades = []
        rules = CASCADE_RULES.get(hazard_type, [])
        
        for rule in rules:
            if current_intensity >= rule["intensity_threshold"]:
                prob = self.compute_cascade_probability(rule["probability"], current_intensity, rule["intensity_threshold"], zone_conditions)
                cascades.append({
                    "triggers": rule["triggers"],
                    "probability": prob,
                    "time_minutes": rule["time_minutes"],
                    "intensity": current_intensity,
                    "rule_base_prob": rule["probability"]
                })
                
        return cascades

    def compute_cascade_probability(self, base_prob: float, intensity: float, threshold: float, zone_conditions: dict) -> float:
        """Compute adjusted cascade probability."""
        adjusted = base_prob * (intensity / max(threshold, 0.01))
        
        ignition = zone_conditions.get("ignition_sources", 1.0)
        adjusted *= ignition
        
        return max(0.0, min(1.0, adjusted))

    def rank_cascade_risks(self, cascades: list[dict]) -> list[dict]:
        """Rank cascades by probability descending."""
        return sorted(cascades, key=lambda x: x.get("probability", 0.0), reverse=True)

    def is_cascade_likely(self, hazard_type: str, intensity: float) -> bool:
        """Check if any cascade is likely (>0.3 prob)."""
        rules = CASCADE_RULES.get(hazard_type, [])
        for rule in rules:
            if intensity >= rule["intensity_threshold"] and rule["probability"] > 0.3:
                return True
        return False
