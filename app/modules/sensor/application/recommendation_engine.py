"""
sensor/application/recommendation_engine.py — Industrial Safety Recommendation Engine.

Generates 10 structured categories of safety recommendations:
  1. Immediate Actions
  2. Preventive Actions
  3. Maintenance
  4. Inspection
  5. Shutdown Recommendation
  6. Evacuation Recommendation
  7. PPE Recommendation
  8. Supervisor Escalation
  9. Government Compliance
  10. Safety Checklist
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.core.logging import get_logger

log = get_logger("sensor.recommendation_engine")

class SensorRecommendationEngine:
    """Industrial Safety Recommendation Engine."""

    def generate_recommendations(
        self,
        sensor_id: str,
        risk_score: float = 0.5,
        anomaly_type: Optional[str] = None,
        context_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate structured industrial safety recommendations across 10 categories."""
        is_critical = risk_score >= 0.8
        is_high = risk_score >= 0.6

        immediate = []
        if is_critical:
            immediate.append("Isolate fuel intake valve immediately.")
            immediate.append("Activate zone warning siren.")
        elif is_high:
            immediate.append("Reduce equipment operational load by 50%.")
            immediate.append("Vent secondary bypass line.")
        else:
            immediate.append("Continue continuous telemetry monitoring.")

        preventive = [
            "Inspect thermal insulation coating for micro-fractures.",
            "Recalibrate sensor transducer baseline."
        ]

        maintenance = [
            "Schedule preventive maintenance within 24 hours.",
            "Flush coolant recirculation loop."
        ]

        inspection = [
            "Visual inspection of pressure relief valves.",
            "Infrared thermal scan of sensor mounting flange."
        ]

        shutdown = {
            "recommended": is_critical,
            "rationale": "Overpressure and thermal runaway risk exceed P1 safety margin." if is_critical else "Operational conditions stable."
        }

        evacuation = {
            "recommended": is_critical and anomaly_type == "GAS_LEAK",
            "rationale": "Hazardous gas exposure risk in Zone 1." if (is_critical and anomaly_type == "GAS_LEAK") else "No evacuation necessary."
        }

        ppe = ["HELMET", "SAFETY_BOOTS", "HEAT_SUIT"] if is_high else ["HELMET", "SAFETY_BOOTS"]

        supervisor = {
            "escalate": is_high or is_critical,
            "target_agent": "SupervisorAgent",
            "priority": "P1" if is_critical else "P2"
        }

        compliance = [
            "OSHA 1910.119 PSM Section 4 Incident Reporting",
            "NFPA 85 Boiler and Combustion Systems Code"
        ]

        checklist = [
            "Verify pressure gauge local reading",
            "Confirm ventilation fan operational",
            "Log entry in plant safety ledger",
            "Notify shift supervisor"
        ]

        return {
            "sensor_id": sensor_id,
            "risk_score": risk_score,
            "anomaly_type": anomaly_type,
            "categories": {
                "immediate_actions": immediate,
                "preventive_actions": preventive,
                "maintenance": maintenance,
                "inspection": inspection,
                "shutdown_recommendation": shutdown,
                "evacuation_recommendation": evacuation,
                "ppe_recommendation": ppe,
                "supervisor_escalation": supervisor,
                "government_compliance": compliance,
                "safety_checklist": checklist
            }
        }

def generate_recommendations(
    sensor_id: str,
    risk_score: float = 0.5,
    anomaly_type: Optional[str] = None,
    context_str: Optional[str] = None
) -> Dict[str, Any]:
    """Standalone function helper for recommendation generation."""
    engine = SensorRecommendationEngine()
    return engine.generate_recommendations(
        sensor_id=sensor_id,
        risk_score=risk_score,
        anomaly_type=anomaly_type,
        context_str=context_str
    )
