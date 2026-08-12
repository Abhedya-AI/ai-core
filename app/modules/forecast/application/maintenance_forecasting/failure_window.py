from __future__ import annotations
import uuid
from datetime import datetime, timezone

from app.core.logging import get_logger
log = get_logger(__name__)

class FailureWindowPredictor:
    """Predictor for probable failure windows based on RUL and uncertainty."""

    def __init__(self) -> None:
        pass

    async def predict_failure_window(self, equipment_id: str, rul_hours: float, rul_confidence: float, degradation_variance: float) -> dict:
        """Predict the most probable failure window."""
        log.info(f"Predicting failure window for {equipment_id}")
        
        # Uncertainty widens the window
        uncertainty_factor = (1.0 - rul_confidence) + degradation_variance
        window_width = max(1.0, rul_hours * uncertainty_factor)
        
        start_hours = max(0.0, rul_hours - (window_width / 2.0))
        end_hours = rul_hours + (window_width / 2.0)
        
        prob = rul_confidence
        
        inspection = max(0.0, start_hours * 0.5)
        
        failure_prob_soon = 1.0 if start_hours <= 24.0 else 0.1
        urgency = self._classify_urgency(start_hours, failure_prob_soon)
        
        risk_catastrophic = min(1.0, (1.0 - rul_confidence) * (1.0 if rul_hours < 48 else 0.2))
        
        actions = []
        if urgency in ('IMMEDIATE', 'URGENT'):
            actions.append("Schedule immediate inspection")
            actions.append("Prepare replacement parts")
        else:
            actions.append("Monitor sensor trends")
            
        return {
            "probable_failure_window": {
                "start_hours": float(start_hours),
                "end_hours": float(end_hours),
                "probability": float(prob)
            },
            "inspection_recommended_at_hours": float(inspection),
            "maintenance_urgency": urgency,
            "risk_of_catastrophic_failure": float(risk_catastrophic),
            "recommended_actions": actions
        }

    def _classify_urgency(self, start_hours: float, failure_prob: float) -> str:
        """Classify maintenance urgency."""
        if start_hours <= 24.0 or failure_prob > 0.8:
            return 'IMMEDIATE'
        elif start_hours <= 72.0:
            return 'URGENT'
        elif start_hours <= 336.0: # 2 weeks
            return 'SCHEDULED'
        return 'ROUTINE'
