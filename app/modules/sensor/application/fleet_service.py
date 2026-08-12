"""
sensor/application/fleet_service.py — Fleet Intelligence Service.

Provides plant-wide fleet analytics:
  Plant → Zones → Equipment → Sensor Fleet → Statistics
  → Health → Availability → Coverage → Risk
"""
from __future__ import annotations
from typing import Any, List, Dict
from app.core.logging import get_logger
from app.modules.sensor.domain.digital_twin import SensorTwin, ZoneTwin, PlantTwin, EquipmentTwin
from app.modules.sensor.application.digital_twin_service import DigitalTwinService
from app.modules.sensor.application.health_tracker import SensorHealthTracker
from app.modules.sensor.application.analytics_service import SensorAnalyticsService
from app.modules.sensor.application.telemetry_buffer import TelemetryBuffer

log = get_logger(__name__)

class FleetService:
    """Fleet Intelligence Service for plant-wide analytics."""

    def __init__(self) -> None:
        """Initialize the Fleet Service."""
        self._twin_service = DigitalTwinService()
        self._health_tracker = SensorHealthTracker()
        self._analytics = SensorAnalyticsService()
        self._buffer = TelemetryBuffer()

    async def get_fleet_overview(self) -> Dict[str, Any]:
        """Get an overview of the entire sensor fleet."""
        all_twins = await self._twin_service.get_all_sensor_twins()
        all_states = [await self._health_tracker.get_sensor_health(twin.sensor_id) for twin in all_twins]
        
        total_sensors = len(all_twins)
        health_counts = {"HEALTHY": 0, "WARNING": 0, "CRITICAL": 0, "OFFLINE": 0}
        
        for state in all_states:
            if state and state.status in health_counts:
                health_counts[state.status] += 1
                
        at_risk = health_counts.get("CRITICAL", 0) + health_counts.get("WARNING", 0)
        fleet_health_pct = (health_counts.get("HEALTHY", 0) / total_sensors * 100) if total_sensors > 0 else 0.0
        
        return {
            "total_sensors": total_sensors,
            "health_counts": health_counts,
            "fleet_health_pct": round(fleet_health_pct, 2),
            "at_risk_count": at_risk
        }

    async def get_zone_fleet(self, zone_id: str) -> Dict[str, Any]:
        """Get fleet statistics for a specific zone."""
        twins = await self._twin_service.get_sensors_by_zone(zone_id)
        states = [await self._health_tracker.get_sensor_health(twin.sensor_id) for twin in twins]
        
        total = len(twins)
        healthy = sum(1 for s in states if s and s.status == "HEALTHY")
        
        return {
            "zone_id": zone_id,
            "sensor_twins": [t.model_dump() for t in twins],
            "health_summary": {
                "total": total,
                "healthy": healthy,
                "at_risk": total - healthy
            },
            "anomaly_rate": sum(s.anomaly_rate for s in states if s) / total if total > 0 else 0.0,
            "risk_level": "CRITICAL" if any(s.status == "CRITICAL" for s in states if s) else "NORMAL"
        }

    async def get_equipment_fleet(self, equipment_id: str) -> Dict[str, Any]:
        """Get fleet statistics for specific equipment."""
        twins = await self._twin_service.get_sensors_by_equipment(equipment_id)
        states = [await self._health_tracker.get_sensor_health(twin.sensor_id) for twin in twins]
        
        total = len(twins)
        healthy = sum(1 for s in states if s and s.status == "HEALTHY")
        combined_health_pct = (healthy / total * 100) if total > 0 else 0.0
        
        return {
            "equipment_id": equipment_id,
            "sensor_twins": [t.model_dump() for t in twins],
            "individual_health": [s.model_dump() for s in states if s],
            "combined_health_pct": round(combined_health_pct, 2)
        }

    async def get_plant_summary(self, plant_id: str) -> Dict[str, Any]:
        """Get summary statistics for an entire plant."""
        plant_twin = await self._twin_service.get_plant_twin(plant_id)
        fleet_overview = await self.get_fleet_overview()
        
        return {
            "plant_id": plant_id,
            "zones_count": len(plant_twin.zones) if plant_twin else 0,
            "equipment_count": len(plant_twin.equipment) if plant_twin else 0,
            "total_sensor_count": fleet_overview["total_sensors"],
            "fleet_health_pct": fleet_overview["fleet_health_pct"],
            "risk_level": "HIGH" if fleet_overview["at_risk_count"] > fleet_overview["total_sensors"] * 0.1 else "NORMAL"
        }

    async def get_sensor_availability(self) -> List[Dict[str, Any]]:
        """Get availability metrics for all sensors."""
        all_twins = await self._twin_service.get_all_sensor_twins()
        availability_list = []
        
        for twin in all_twins:
            state = await self._health_tracker.get_sensor_health(twin.sensor_id)
            if state:
                availability_list.append({
                    "sensor_id": twin.sensor_id,
                    "uptime_pct": state.uptime_pct,
                    "total_readings": state.total_readings,
                    "anomaly_rate": state.anomaly_rate,
                    "status": state.status
                })
                
        availability_list.sort(key=lambda x: x["uptime_pct"])
        return availability_list

    async def get_fleet_risk_report(self) -> Dict[str, Any]:
        """Generate a risk report for the entire fleet."""
        all_twins = await self._twin_service.get_all_sensor_twins()
        critical_sensors = []
        zone_counts = {}
        equip_counts = {}
        
        total = len(all_twins)
        critical_count = 0
        warning_count = 0
        
        for twin in all_twins:
            state = await self._health_tracker.get_sensor_health(twin.sensor_id)
            if state and state.status in ["CRITICAL", "WARNING"]:
                if state.status == "CRITICAL":
                    critical_count += 1
                else:
                    warning_count += 1
                    
                sensor_info = {
                    "sensor_id": twin.sensor_id,
                    "zone_id": twin.zone_id,
                    "equipment_id": twin.equipment_id,
                    "status": state.status
                }
                critical_sensors.append(sensor_info)
                
                z_id = twin.zone_id or "unknown"
                zone_counts[z_id] = zone_counts.get(z_id, 0) + 1
                
                e_id = twin.equipment_id or "none"
                equip_counts[e_id] = equip_counts.get(e_id, 0) + 1
                
        fleet_risk = "NORMAL"
        if critical_count > 0:
            fleet_risk = "CRITICAL"
        elif total > 0 and (warning_count / total) > 0.1:
            fleet_risk = "HIGH"
            
        return {
            "critical_sensors": critical_sensors,
            "count_by_zone": zone_counts,
            "count_by_equipment": equip_counts,
            "overall_fleet_risk": fleet_risk
        }

    async def get_maintenance_candidates(self) -> List[Dict[str, Any]]:
        """Get a list of sensors recommended for maintenance."""
        all_twins = await self._twin_service.get_all_sensor_twins()
        candidates = []
        
        for twin in all_twins:
            state = await self._health_tracker.get_sensor_health(twin.sensor_id)
            
            failure_prob = state.anomaly_rate / 100.0 if state else 0.0
            
            if state and (failure_prob > 0.6 or state.consecutive_anomalies > 5):
                candidates.append({
                    "sensor_id": twin.sensor_id,
                    "failure_probability": round(failure_prob, 2),
                    "estimated_rul_hours": max(0, 100 - (state.consecutive_anomalies * 10)),
                    "consecutive_anomalies": state.consecutive_anomalies,
                    "recommendation": "Immediate inspection and calibration required" if failure_prob > 0.8 else "Schedule maintenance"
                })
                
        return candidates
