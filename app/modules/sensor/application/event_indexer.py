"""
sensor/application/event_indexer.py — GraphRAG Event Indexer.

Indexes important sensor events into the GraphRAG vector store
so they become retrievable via hybrid semantic search.

Events indexed:
  - Critical and high-severity anomalies
  - Rule triggers (P1/P2 only)
  - Health state transitions
  - Correlation breaks
  - Fleet health degradation events

Pipeline:
  Sensor Event → Entity Extraction → Metadata Assembly
  → Text Chunk Generation → GraphRAG Indexing (via existing GraphRAG module)
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field
from app.core.logging import get_logger
from app.modules.sensor.domain.models import SensorAnomaly, SensorHealthState, AnomalySeverity
from app.modules.sensor.domain.rule_models import RuleTriggerRecord
from app.modules.sensor.domain.correlation_models import CorrelationAlert

log = get_logger(__name__)

class IndexedEvent(BaseModel):
    """Represents a sensor event that is indexed into GraphRAG."""
    event_id: str = Field(..., description="Unique identifier for the event")
    event_type: str = Field(..., description="Type of the event")
    sensor_id: str = Field(..., description="Sensor ID")
    zone_id: Optional[str] = Field(None, description="Zone ID")
    equipment_id: Optional[str] = Field(None, description="Equipment ID")
    text_content: str = Field(..., description="Natural language description")
    entities: List[str] = Field(default_factory=list, description="Extracted entities")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Event metadata")
    severity: str = Field(..., description="Severity level")
    timestamp: datetime = Field(..., description="Event timestamp")
    indexed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Time of indexing")


class SensorEventIndexer:
    """Indexes important sensor events into the GraphRAG vector store."""

    def __init__(self) -> None:
        """Initialize the event indexer."""
        self._graphrag = None
        self._index_queue: List[IndexedEvent] = []

    def _get_graphrag(self) -> Any:
        """Lazy load the GraphRAG indexing service."""
        try:
            from app.modules.graphrag.services.indexing_service import GraphRAGIndexingService
            if not self._graphrag:
                self._graphrag = GraphRAGIndexingService()
        except ImportError:
            log.warning("GraphRAGIndexingService could not be imported.")
        return self._graphrag

    async def index_anomaly(
        self, 
        anomaly: SensorAnomaly, 
        zone_id: Optional[str] = None, 
        equipment_id: Optional[str] = None
    ) -> bool:
        """Index a critical or high severity anomaly."""
        if anomaly.severity not in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]:
            return False

        text_content = (
            f"Sensor {anomaly.sensor_id} detected {anomaly.anomaly_type.value} anomaly "
            f"(severity: {anomaly.severity.value}). Value: {anomaly.value}. "
            f"Expected: {anomaly.expected_value}. {anomaly.description}"
        )
        
        entities = [anomaly.sensor_id, anomaly.anomaly_type.value]
        if zone_id:
            entities.append(zone_id)
        if equipment_id:
            entities.append(equipment_id)
            
        metadata = anomaly.model_dump()
        metadata["zone_id"] = zone_id
        metadata["equipment_id"] = equipment_id

        event = IndexedEvent(
            event_id=f"anomaly_{anomaly.sensor_id}_{int(anomaly.timestamp.timestamp())}",
            event_type="SENSOR_ANOMALY",
            sensor_id=anomaly.sensor_id,
            zone_id=zone_id,
            equipment_id=equipment_id,
            text_content=text_content,
            entities=entities,
            metadata=metadata,
            severity=anomaly.severity.value,
            timestamp=anomaly.timestamp
        )
        self._index_queue.append(event)
        return await self._try_index(event)

    async def index_health_transition(
        self, 
        sensor_id: str, 
        from_status: str, 
        to_status: str, 
        zone_id: Optional[str] = None
    ) -> bool:
        """Index a critical or offline health state transition."""
        if to_status not in ["CRITICAL", "OFFLINE"]:
            return False

        text_content = f"Sensor {sensor_id} health changed from {from_status} to {to_status}"
        entities = [sensor_id, to_status]
        if zone_id:
            entities.append(zone_id)

        event = IndexedEvent(
            event_id=f"health_{sensor_id}_{int(datetime.now(timezone.utc).timestamp())}",
            event_type="HEALTH_TRANSITION",
            sensor_id=sensor_id,
            zone_id=zone_id,
            equipment_id=None,
            text_content=text_content,
            entities=entities,
            metadata={"from_status": from_status, "to_status": to_status},
            severity="HIGH" if to_status == "CRITICAL" else "MEDIUM",
            timestamp=datetime.now(timezone.utc)
        )
        self._index_queue.append(event)
        return await self._try_index(event)

    async def index_rule_trigger(
        self, 
        record: RuleTriggerRecord, 
        rule_name: str, 
        zone_id: Optional[str] = None
    ) -> bool:
        """Index a priority rule trigger."""
        if record.priority not in [1, 2]:
            return False
            
        text_content = (
            f"Rule '{rule_name}' triggered by sensor {record.sensor_id} "
            f"(priority: {record.priority}). Actions: {record.actions_taken}"
        )
        entities = [record.sensor_id, rule_name]
        if zone_id:
            entities.append(zone_id)

        event = IndexedEvent(
            event_id=f"rule_{record.sensor_id}_{int(record.triggered_at.timestamp())}",
            event_type="RULE_TRIGGER",
            sensor_id=record.sensor_id,
            zone_id=zone_id,
            equipment_id=None,
            text_content=text_content,
            entities=entities,
            metadata=record.model_dump(),
            severity="CRITICAL" if record.priority == 1 else "HIGH",
            timestamp=record.triggered_at
        )
        self._index_queue.append(event)
        return await self._try_index(event)

    async def index_correlation_break(self, alert: CorrelationAlert) -> bool:
        """Index a correlation break event."""
        text_content = (
            f"Correlation break detected involving sensor {alert.primary_sensor_id}. "
            f"Reason: {alert.reason}. Target sensor: {alert.target_sensor_id}."
        )
        entities = [alert.primary_sensor_id, alert.target_sensor_id]
        
        event = IndexedEvent(
            event_id=alert.alert_id,
            event_type="CORRELATION_BREAK",
            sensor_id=alert.primary_sensor_id,
            zone_id=None,
            equipment_id=None,
            text_content=text_content,
            entities=entities,
            metadata=alert.model_dump(),
            severity="HIGH",
            timestamp=alert.detected_at
        )
        self._index_queue.append(event)
        return await self._try_index(event)

    async def _try_index(self, event: IndexedEvent) -> bool:
        """Attempt to index the event using the GraphRAG service."""
        try:
            graphrag = self._get_graphrag()
            if graphrag and hasattr(graphrag, "_index_document"):
                await graphrag._index_document(text=event.text_content, metadata=event.metadata)
                return True
            elif graphrag and hasattr(graphrag, "index_document"):
                await graphrag.index_document(text=event.text_content, metadata=event.metadata)
                return True
        except Exception as e:
            log.error(f"Failed to index event {event.event_id}: {str(e)}")
        return False

    def get_queue(self) -> List[IndexedEvent]:
        """Return the unprocessed event queue."""
        return self._index_queue
