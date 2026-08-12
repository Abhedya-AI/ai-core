from __future__ import annotations
import uuid
from datetime import datetime, timezone
import numpy as np

from app.core.logging import get_logger
log = get_logger(__name__)

class ScenarioForecastEngine:
    """Engine for generating best/worst/expected case scenarios."""

    def __init__(self) -> None:
        pass

    async def generate_scenarios(self, base_forecast_value: float, base_confidence: float, forecast_type: str, horizon: str, context: dict) -> dict:
        """Generate multiple scenarios around a base forecast."""
        log.info(f"Generating scenarios for {forecast_type} over {horizon}")
        
        uncertainty = 1.0 - base_confidence
        
        # Best case logic
        best_val = base_forecast_value * (1 - 0.2 * uncertainty)
        best_val = self._adjust_for_context(best_val, context, "best")
        best_case = {
            "value": float(np.clip(best_val, 0.0, 1.0) if best_val <= 1.5 else best_val),
            "confidence": float(np.clip(base_confidence * 0.9, 0.0, 1.0)),
            "probability": 0.15,
            "conditions": ["Optimal maintenance", "Favorable environment"],
            "description": "Best case scenario assuming optimal conditions."
        }
        
        # Expected case
        expected_val = self._adjust_for_context(base_forecast_value, context, "expected")
        expected_case = {
            "value": float(np.clip(expected_val, 0.0, 1.0) if expected_val <= 1.5 else expected_val),
            "confidence": float(base_confidence),
            "probability": 0.70,
            "conditions": ["Current trends continue"],
            "description": "Expected outcome based on current trajectory."
        }
        
        # Worst case logic
        worst_val = base_forecast_value * (1 + 0.3 * uncertainty)
        worst_val = self._adjust_for_context(worst_val, context, "worst")
        worst_case = {
            "value": float(np.clip(worst_val, 0.0, 1.0) if worst_val <= 1.5 else worst_val),
            "confidence": float(np.clip(base_confidence * 0.9, 0.0, 1.0)),
            "probability": 0.15,
            "conditions": ["Cascading failures", "Adverse environment"],
            "description": "Worst case scenario factoring in compounding risks."
        }
        
        spread = abs(worst_case["value"] - best_case["value"])
        
        return {
            "best_case": best_case,
            "expected_case": expected_case,
            "worst_case": worst_case,
            "scenario_spread": float(spread)
        }

    def _adjust_for_context(self, value: float, context: dict, scenario_type: str) -> float:
        """Adjust values based on operational context."""
        recent_incidents = context.get("recent_incidents", 0)
        
        if scenario_type == "worst":
            # Context penalty
            if recent_incidents > 0:
                value *= (1.0 + (recent_incidents * 0.05))
        elif scenario_type == "best":
            # Context bonus?
            pass
            
        return value
