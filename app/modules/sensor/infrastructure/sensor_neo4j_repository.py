"""
sensor/infrastructure/sensor_neo4j_repository.py — Sensor Neo4j Repository.

Manages INCREMENTAL graph updates for sensor data.
NEVER recreates the graph — only merges/updates.

Graph structure maintained:
  (Sensor) -[:MONITORS]-> (Equipment)
  (Sensor) -[:LOCATED_IN]-> (Zone)
  (Sensor) -[:GENERATED]-> (SensorReadingNode)
  (Alert)  -[:DETECTED]-> (Sensor)
  (Alert)  -[:AFFECTS]-> (Zone)
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.modules.sensor.domain.models import SensorReading, SensorAnomaly, SensorHealthState

log = get_logger("app.modules.sensor.infrastructure.sensor_neo4j_repository")

class SensorNeo4jRepository:
    """Repository for syncing sensor data into the Neo4j Knowledge Graph."""

    def __init__(self) -> None:
        """Initialize the repository, deferring driver loading."""
        self._driver = None

    def _get_driver(self) -> Any:
        """
        Get the Neo4j driver from the global registry.
        
        Returns:
            Neo4j driver instance.
        """
        from app.core.registry import registry
        if self._driver is None:
            self._driver = registry.neo4j
        return self._driver

    async def _execute(self, query: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Execute a Cypher query against Neo4j.
        
        Args:
            query: Cypher query string.
            params: Query parameters.
            
        Returns:
            List of dictionaries representing the records.
        """
        try:
            driver = self._get_driver()
            async with driver.session() as session:
                result = await session.run(query, params)
                return [dict(record) async for record in result]
        except Exception as exc:
            log.warning(f"Neo4j query failed (non-fatal): {exc}")
            return []

    async def execute_query(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Public interface to execute a Cypher query."""
        return await self._execute(query, params or {})

    async def sync_sensor_reading(self, reading: SensorReading) -> bool:
        """
        Sync a sensor reading into the graph by merging a SensorReading node.
        
        Args:
            reading: The sensor reading domain model.
            
        Returns:
            bool: True if synced successfully, False otherwise.
        """
        query = """
        MERGE (sr:SensorReading {reading_id: $reading_id})
        SET sr += $props
        WITH sr
        MATCH (s:Sensor {id: $sensor_id})
        MERGE (s)-[:GENERATED]->(sr)
        RETURN sr
        """
        
        timestamp_iso = reading.timestamp.isoformat() if isinstance(reading.timestamp, datetime) else str(reading.timestamp)
        
        params = {
            "reading_id": getattr(reading, "id", f"reading_{reading.sensor_id}_{timestamp_iso}"),
            "sensor_id": reading.sensor_id,
            "props": {
                "value": reading.value,
                "unit": reading.unit,
                "timestamp": timestamp_iso,
                "quality_score": reading.quality_score,
            }
        }
        
        result = await self._execute(query, params)
        return len(result) > 0

    async def sync_sensor_health(self, state: SensorHealthState) -> bool:
        """
        Update an existing sensor node with the latest health status.
        
        Args:
            state: The sensor health state domain model.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        query = """
        MATCH (s:Sensor {id: $sensor_id})
        SET s.health_status = $status,
            s.last_health_update = $ts,
            s.uptime_pct = $uptime
        RETURN s
        """
        
        timestamp_iso = state.last_updated.isoformat() if isinstance(state.last_updated, datetime) else str(state.last_updated)
        
        params = {
            "sensor_id": state.sensor_id,
            "status": state.status.value if hasattr(state.status, "value") else str(state.status),
            "ts": timestamp_iso,
            "uptime": state.uptime_pct,
        }
        
        result = await self._execute(query, params)
        return len(result) > 0

    async def create_alert_node(self, anomaly: SensorAnomaly, zone_id: str | None = None) -> bool:
        """
        Create or merge an Alert node and relate it to the sensor and zone.
        
        Args:
            anomaly: The anomaly detected.
            zone_id: Optional zone ID where the sensor is located.
            
        Returns:
            bool: True if the alert was created, False otherwise.
        """
        query = """
        MERGE (a:Alert {anomaly_id: $anomaly_id})
        SET a.type = $type,
            a.severity = $severity,
            a.created_at = $timestamp,
            a.description = $description
        WITH a
        MATCH (s:Sensor {id: $sensor_id})
        MERGE (a)-[:DETECTED]->(s)
        """
        
        timestamp_iso = anomaly.timestamp.isoformat() if isinstance(anomaly.timestamp, datetime) else str(anomaly.timestamp)
        
        params = {
            "anomaly_id": anomaly.id,
            "type": anomaly.anomaly_type.value if hasattr(anomaly.anomaly_type, "value") else str(anomaly.anomaly_type),
            "severity": anomaly.severity.value if hasattr(anomaly.severity, "value") else str(anomaly.severity),
            "timestamp": timestamp_iso,
            "description": anomaly.description,
            "sensor_id": anomaly.sensor_id,
        }
        
        if zone_id:
            query += """
            WITH a
            MATCH (z:Zone {id: $zone_id})
            MERGE (a)-[:AFFECTS]->(z)
            """
            params["zone_id"] = zone_id
            
        query += " RETURN a"
        
        result = await self._execute(query, params)
        return len(result) > 0

    async def get_sensor_reading_count(self, sensor_id: str) -> int:
        """
        Count the number of readings generated by a given sensor.
        
        Args:
            sensor_id: The ID of the sensor.
            
        Returns:
            int: The number of readings.
        """
        query = """
        MATCH (s:Sensor {id: $sensor_id})-[:GENERATED]->(sr:SensorReading)
        RETURN count(sr) as cnt
        """
        params = {"sensor_id": sensor_id}
        result = await self._execute(query, params)
        
        if result and "cnt" in result[0]:
            return int(result[0]["cnt"])
        return 0

    async def get_recent_alerts(self, sensor_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Retrieve recent alerts detected by a given sensor.
        
        Args:
            sensor_id: The ID of the sensor.
            limit: Maximum number of alerts to return.
            
        Returns:
            List of dictionaries containing alert data.
        """
        query = """
        MATCH (a:Alert)-[:DETECTED]->(s:Sensor {id: $sensor_id})
        RETURN a
        ORDER BY a.created_at DESC
        LIMIT $limit
        """
        params = {
            "sensor_id": sensor_id,
            "limit": limit
        }
        
        return await self._execute(query, params)
