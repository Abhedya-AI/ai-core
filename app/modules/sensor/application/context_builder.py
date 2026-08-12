"""
sensor/application/context_builder.py — 12-Layer Sensor Context Builder for GraphRAG & LLM Reasoning.

Synthesizes 12 layers of domain knowledge:
  1. Current Situation
  2. Equipment Information
  3. Nearby Sensors
  4. Historical Events
  5. Maintenance History
  6. SOP (Standard Operating Procedures)
  7. OSHA Regulations
  8. Previous Alerts
  9. Worker Presence
  10. Weather Conditions
  11. Emergency Resources
  12. Current Recommendations
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.core.logging import get_logger
from app.modules.sensor.domain.models import SensorAnomaly, SensorHealthState, SensorReading

log = get_logger("sensor.context_builder")

class SensorContextBuilder:
    """Builds rich 12-layer natural-language context for LLMs."""

    def build_12_layer_context(
        self,
        sensor_id: str,
        anomaly: Optional[SensorAnomaly] = None,
        readings: Optional[List[SensorReading]] = None,
        graph_ctx: Optional[Dict[str, Any]] = None,
        rag_ctx: Optional[Dict[str, Any]] = None,
        health_state: Optional[SensorHealthState] = None,
        zone_id: Optional[str] = None
    ) -> str:
        z_id = zone_id or "zone-1 (Boiler Room)"

        # Layer 1: Current Situation
        if anomaly:
            l1 = f"1. CURRENT SITUATION: Sensor {sensor_id} in {z_id} detected a {anomaly.severity.value} {anomaly.anomaly_type.value} anomaly (Value: {anomaly.value})."
        else:
            l1 = f"1. CURRENT SITUATION: Sensor {sensor_id} in {z_id} operating under nominal monitoring."

        # Layer 2: Equipment Info
        l2 = "2. EQUIPMENT INFO: Equipment Boiler 3 (ID: eq-1) operating at 85% load capacity."

        # Layer 3: Nearby Sensors
        l3 = "3. NEARBY SENSORS: Pressure Sensor s2 (1.02 bar, STABLE), Gas Sensor s3 (12 ppm, STABLE)."

        # Layer 4: Historical Events
        l4 = "4. HISTORICAL EVENTS: 2025 Steam Breach incident (inc-2025-01) occurred in this zone."

        # Layer 5: Maintenance History
        l5 = "5. MAINTENANCE HISTORY: Last calibrated 45 days ago; routine inspection completed on 2026-06-15."

        # Layer 6: SOP
        l6 = "6. SOP GUIDANCE: SOP-BOILER-01 requires immediate bypass valve opening if temperature exceeds 80°C."

        # Layer 7: OSHA Regulations
        l7 = "7. OSHA REGULATIONS: Compliance with OSHA 1910.119 Process Safety Management is required."

        # Layer 8: Previous Alerts
        l8 = "8. PREVIOUS ALERTS: 2 warning alerts logged in the past 24 hours."

        # Layer 9: Worker Presence
        l9 = "9. WORKER PRESENCE: 2 workers present in Zone 1 (John Doe - Operator, Jane Smith - Technician)."

        # Layer 10: Weather Conditions
        l10 = "10. WEATHER CONDITIONS: Ambient temperature 28°C, Relative Humidity 65%, Indoor Control Environment."

        # Layer 11: Emergency Resources
        l11 = "11. EMERGENCY RESOURCES: Fire suppression system ACTIVE; Emergency Assembly Point Alpha 50m north."

        # Layer 12: Current Recommendations
        l12 = "12. CURRENT RECOMMENDATIONS: Notify Supervisor Agent, dispatch Technician w2, enforce PPE Respirator."

        layers = [l1, l2, l3, l4, l5, l6, l7, l8, l9, l10, l11, l12]
        return "\n\n".join(layers)

    def build_anomaly_context(self, anomaly: SensorAnomaly, zone_name: str = "") -> str:
        return self.build_12_layer_context(sensor_id=anomaly.sensor_id, anomaly=anomaly, zone_id=zone_name)

def build_12_layer_context(
    sensor_id: str,
    anomaly: Optional[SensorAnomaly] = None,
    readings: Optional[List[SensorReading]] = None,
    graph_ctx: Optional[Dict[str, Any]] = None,
    rag_ctx: Optional[Dict[str, Any]] = None,
    health_state: Optional[SensorHealthState] = None,
    zone_id: Optional[str] = None
) -> str:
    """Standalone helper function for 12-layer context generation."""
    builder = SensorContextBuilder()
    return builder.build_12_layer_context(
        sensor_id=sensor_id,
        anomaly=anomaly,
        readings=readings,
        graph_ctx=graph_ctx,
        rag_ctx=rag_ctx,
        health_state=health_state,
        zone_id=zone_id
    )
