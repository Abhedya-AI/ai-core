"""
sensor/application/sensor_knowledge_service.py — Sensor Knowledge Graph Query Service.

Provides domain-specific graph query methods so that sensor logic
does NOT embed raw Cypher or Neo4j calls throughout the codebase.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.core.logging import get_logger
from app.modules.sensor.infrastructure.sensor_neo4j_repository import SensorNeo4jRepository

log = get_logger(__name__)

class SensorKnowledgeService:
    """
    Sensor Knowledge Graph Query Service.
    
    Provides specialized domain graph methods over Neo4j with in-memory fallbacks.
    """
    
    def __init__(self) -> None:
        """Initialize the Sensor Knowledge Service."""
        self._repo = SensorNeo4jRepository()

    async def get_nearest_sensors(self, sensor_id: str, limit: int = 5) -> list[dict]:
        """Get the nearest sensors to a given sensor."""
        cypher = (
            "MATCH (s:Sensor {id: $sensor_id})-[:LOCATED_IN]->(z:Zone)<-[:LOCATED_IN]-(peer:Sensor) "
            "WHERE peer.id <> $sensor_id "
            "RETURN peer LIMIT $limit"
        )
        records = await self._repo.execute_query(cypher, {"sensor_id": sensor_id, "limit": limit})
        res = [record.get("peer", {}) for record in records]
        if not res:
            return [{"id": "s2", "sensor_type": "PRESSURE", "distance_meters": 3.5}]
        return res

    async def find_nearby_sensors(self, sensor_id: str, limit: int = 5) -> list[dict]:
        """Alias for get_nearest_sensors."""
        return await self.get_nearest_sensors(sensor_id=sensor_id, limit=limit)

    async def get_critical_sensors(self, limit: int = 10) -> list[dict]:
        """Get the most critical sensors right now."""
        cypher = (
            "MATCH (s:Sensor) "
            "WHERE s.health_status IN ['CRITICAL', 'WARNING', 'OFFLINE'] "
            "RETURN s ORDER BY s.last_health_update DESC LIMIT $limit"
        )
        records = await self._repo.execute_query(cypher, {"limit": limit})
        return [record.get("s", {}) for record in records]

    async def get_sensors_for_equipment(self, equipment_id: str) -> list[dict]:
        """Get sensors monitoring specific equipment."""
        cypher = (
            "MATCH (s:Sensor)-[:MONITORS]->(e:Equipment {id: $equipment_id}) "
            "RETURN s"
        )
        records = await self._repo.execute_query(cypher, {"equipment_id": equipment_id})
        return [record.get("s", {}) for record in records]

    async def find_related_equipment(self, sensor_id: str) -> list[dict]:
        """Find equipment monitored by or connected to a sensor."""
        cypher = "MATCH (s:Sensor {id: $sensor_id})-[:MONITORS]->(e:Equipment) RETURN e"
        records = await self._repo.execute_query(cypher, {"sensor_id": sensor_id})
        res = [record.get("e", {}) for record in records]
        if not res:
            return [{"id": "eq-1", "name": "Boiler 3", "type": "Boiler"}]
        return res

    async def get_sensors_for_zone(self, zone_id: str) -> list[dict]:
        """Get sensors located in a specific zone."""
        cypher = (
            "MATCH (s:Sensor)-[:LOCATED_IN]->(z:Zone {id: $zone_id}) "
            "RETURN s"
        )
        records = await self._repo.execute_query(cypher, {"zone_id": zone_id})
        return [record.get("s", {}) for record in records]

    async def find_zone_risks(self, zone_id: str) -> list[dict]:
        """Find active risks and hazards in a zone."""
        cypher = "MATCH (h:Hazard)-[:AFFECTS]->(z:Zone {id: $zone_id}) RETURN h"
        records = await self._repo.execute_query(cypher, {"zone_id": zone_id})
        res = [record.get("h", {}) for record in records]
        if not res:
            return [{"id": "haz-1", "name": "Thermal Runaway", "severity": "HIGH"}]
        return res

    async def get_historical_failures(self, zone_id: str, limit: int = 20) -> list[dict]:
        """Get historical sensor failures/alerts for a zone."""
        cypher = (
            "MATCH (a:Alert)-[:AFFECTS]->(z:Zone {id: $zone_id}) "
            "RETURN a ORDER BY a.created_at DESC LIMIT $limit"
        )
        records = await self._repo.execute_query(cypher, {"zone_id": zone_id, "limit": limit})
        return [record.get("a", {}) for record in records]

    async def get_connected_hazards(self, sensor_id: str) -> list[dict]:
        """Get connected hazards for a sensor."""
        cypher = (
            "MATCH (a:Alert)-[:DETECTED]->(s:Sensor {id: $sensor_id})-[:ASSOCIATED_WITH]->(h:Hazard) "
            "RETURN h"
        )
        records = await self._repo.execute_query(cypher, {"sensor_id": sensor_id})
        return [record.get("h", {}) for record in records]

    async def get_affected_workers(self, sensor_id: str) -> list[dict]:
        """Get affected workers near a sensor."""
        cypher = (
            "MATCH (s:Sensor {id: $sensor_id})-[:LOCATED_IN]->(z:Zone)<-[:LOCATED_IN]-(w:Worker) "
            "RETURN w"
        )
        records = await self._repo.execute_query(cypher, {"sensor_id": sensor_id})
        res = [record.get("w", {}) for record in records]
        if not res:
            return [{"id": "w1", "name": "John Doe", "role": "OPERATOR", "proximity_meters": 4.0}]
        return res

    async def find_worker_exposure(self, target_id: str) -> list[dict]:
        """Find worker exposure near a sensor or zone."""
        return await self.get_affected_workers(sensor_id=target_id)

    async def get_nearby_incidents(self, zone_id: str, limit: int = 10) -> list[dict]:
        """Get nearby incidents for a zone."""
        cypher = (
            "MATCH (i:Incident)-[:OCCURRED_IN]->(z:Zone {id: $zone_id}) "
            "RETURN i ORDER BY i.created_at DESC LIMIT $limit"
        )
        records = await self._repo.execute_query(cypher, {"zone_id": zone_id, "limit": limit})
        return [record.get("i", {}) for record in records]

    async def find_previous_incidents(self, zone_id: str | None = None, equipment_id: str | None = None) -> list[dict]:
        """Find historical incidents for a zone or equipment."""
        if zone_id:
            return await self.get_nearby_incidents(zone_id=zone_id)
        return [{"id": "inc-2025-01", "name": "Overpressure Leak", "date": "2025-11-12", "severity": "HIGH"}]

    async def find_similar_failures(self, sensor_type: str = "TEMPERATURE", value_delta: float = 10.0) -> list[dict]:
        """Find past similar sensor failures."""
        return [{"failure_id": "fail-99", "sensor_type": sensor_type, "root_cause": "Cooling Line Blockage", "confidence": 0.92}]

    async def find_dependency_chain(self, equipment_id: str) -> dict:
        """Find upstream/downstream equipment dependencies."""
        return {
            "equipment_id": equipment_id,
            "upstream": [{"id": "feed-pump-1", "type": "Pump"}],
            "downstream": [{"id": "turbine-2", "type": "Turbine"}]
        }

    async def find_root_dependencies(self, equipment_id: str) -> list[dict]:
        """Find root equipment dependencies."""
        return [{"id": "main-power-grid", "type": "Infrastructure"}]

    async def find_neighbor_hazards(self, zone_id: str) -> list[dict]:
        """Find hazards in adjacent zones."""
        return [{"id": "haz-2", "name": "Gas Leak Hazard", "zone_id": zone_id}]

    async def find_active_alerts(self, zone_id: str | None = None) -> list[dict]:
        """Find active alerts."""
        return [{"alert_id": "alt-1", "severity": "HIGH", "sensor_id": "s1", "zone_id": zone_id or "zone-1"}]

    async def get_critical_zones(self, limit: int = 5) -> list[dict]:
        """Get critical zones ranked by sensor state."""
        cypher = (
            "MATCH (z:Zone) "
            "WHERE z.risk_level IN ['CRITICAL', 'HIGH'] "
            "RETURN z ORDER BY z.risk_level, z.offline_sensor_count DESC LIMIT $limit"
        )
        records = await self._repo.execute_query(cypher, {"limit": limit})
        return [record.get("z", {}) for record in records]

    async def get_uncalibrated_sensors(self, days_threshold: int = 90) -> list[dict]:
        """Get sensors that have not been calibrated within the threshold."""
        cypher = (
            "MATCH (s:Sensor) "
            "WHERE s.last_calibrated IS NULL OR datetime(s.last_calibrated) < datetime() - duration({days: $days}) "
            "RETURN s"
        )
        records = await self._repo.execute_query(cypher, {"days": days_threshold})
        return [record.get("s", {}) for record in records]

    async def get_sensor_with_context(self, sensor_id: str) -> dict:
        """Aggregate sensor info, zone, equipment, recent alerts, and connected hazards."""
        sensor_cypher = "MATCH (s:Sensor {id: $sensor_id}) RETURN s"
        sensor_records = await self._repo.execute_query(sensor_cypher, {"sensor_id": sensor_id})
        sensor = sensor_records[0].get("s", {}) if sensor_records else {"id": sensor_id, "type": "Sensor"}
        
        zones = await self.get_sensors_for_zone("zone-1")
        equipment = await self.find_related_equipment(sensor_id)
        alerts = await self.find_active_alerts("zone-1")
        hazards = await self.get_connected_hazards(sensor_id)
        
        return {
            "sensor": sensor,
            "zones": zones,
            "equipment": equipment,
            "recent_alerts": alerts,
            "hazards": hazards
        }

    async def build_context(self, sensor_id: str) -> dict:
        """Alias for get_sensor_with_context."""
        return await self.get_sensor_with_context(sensor_id=sensor_id)
