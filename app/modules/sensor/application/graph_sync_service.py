"""
sensor/application/graph_sync_service.py — Knowledge Graph Synchronization Service.

Orchestrates incremental Neo4j updates whenever sensor state changes.
Never recreates nodes — always MERGE.
Supports graph history and versioning via timestamp-stamped relationships.
"""
from __future__ import annotations

import asyncio
from typing import Any

from app.core.logging import get_logger
from app.modules.sensor.domain.models import SensorReading, SensorAnomaly, SensorHealthState
from app.modules.sensor.infrastructure.sensor_neo4j_repository import SensorNeo4jRepository

log = get_logger("app.modules.sensor.application.graph_sync_service")


class GraphSyncService:
    """
    Synchronizes sensor domain events with the Neo4j Knowledge Graph.
    Ensures that real-time sensor data is appropriately reflected in the graph.
    """

    def __init__(self) -> None:
        """Initialize the Graph Sync Service with the Neo4j repository."""
        self._repo = SensorNeo4jRepository()

    async def on_reading_ingested(self, reading: SensorReading) -> None:
        """
        Handle a new sensor reading by syncing it to the graph.
        This is a fire-and-forget operation; exceptions are caught and logged.
        
        Args:
            reading: The newly ingested sensor reading.
        """
        try:
            success = await self._repo.sync_sensor_reading(reading)
            if not success:
                log.debug(f"Could not sync reading to graph. Sensor node {reading.sensor_id} might not exist.")
        except Exception as exc:
            log.error(f"Failed to sync reading to graph for sensor {reading.sensor_id}: {exc}")

    async def on_anomaly_detected(self, anomaly: SensorAnomaly, zone_id: str | None = None) -> None:
        """
        Handle a newly detected anomaly by creating an alert node in the graph.
        
        Args:
            anomaly: The detected sensor anomaly.
            zone_id: The optional zone ID associated with the sensor.
        """
        try:
            success = await self._repo.create_alert_node(anomaly, zone_id)
            if not success:
                log.debug(f"Could not create alert node for anomaly {anomaly.id}.")
        except Exception as exc:
            log.error(f"Failed to create alert node in graph for anomaly {anomaly.id}: {exc}")

    async def on_health_changed(self, state: SensorHealthState) -> None:
        """
        Handle a sensor health state change by updating the sensor node properties.
        
        Args:
            state: The new sensor health state.
        """
        try:
            success = await self._repo.sync_sensor_health(state)
            if not success:
                log.debug(f"Could not sync health state for sensor {state.sensor_id} to graph.")
        except Exception as exc:
            log.error(f"Failed to sync health state to graph for sensor {state.sensor_id}: {exc}")

    async def on_bulk_readings(self, readings: list[SensorReading]) -> None:
        """
        Process a bulk list of sensor readings concurrently.
        
        Args:
            readings: A list of sensor readings to sync.
        """
        try:
            tasks = [self.on_reading_ingested(reading) for reading in readings]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log any exceptions that were returned by gather
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    reading_sensor = readings[i].sensor_id
                    log.error(f"Error processing bulk reading for sensor {reading_sensor}: {result}")
                    
        except Exception as exc:
            log.error(f"Failed during bulk readings sync: {exc}")
