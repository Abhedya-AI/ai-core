"""
app/api/v1/sensor_ws.py — Enhanced Sensor Intelligence WebSocket Streams.

Channels with hierarchical subscriptions:
  /ws/sensors           — All sensor readings
  /ws/plant/{plant_id}  — Plant-scoped stream
  /ws/zone/{zone_id}    — Zone-scoped stream
  /ws/equipment/{equipment_id} — Equipment-scoped stream
  /ws/alerts            — Critical alerts stream
  /ws/analytics         — Analytics snapshots
  /ws/health            — Health state changes

Filtering: ?sensor_type=GAS&severity=CRITICAL
"""
from __future__ import annotations
import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Path

from app.core.logging import get_logger

log = get_logger(__name__)


class SensorWSConnectionManager:
    """Manages WebSocket connections for Sensor Intelligence channels."""

    def __init__(self) -> None:
        """Initialize the connection manager."""
        # channel -> connection_id -> dict with 'ws' and 'filters'
        self._connections: dict[str, dict[str, dict[str, Any]]] = {
            "sensors": {},
            "plant": {},
            "zone": {},
            "equipment": {},
            "alerts": {},
            "analytics": {},
            "health": {},
        }

    async def connect(self, channel: str, ws: WebSocket, filters: dict[str, str]) -> str:
        """Accept WS, store with filters, return conn_id."""
        await ws.accept()
        conn_id = str(uuid.uuid4())
        if channel not in self._connections:
            self._connections[channel] = {}
        self._connections[channel][conn_id] = {"ws": ws, "filters": filters}
        log.info(f"Client {conn_id} connected to {channel} with filters: {filters}")
        return conn_id

    def disconnect(self, channel: str, conn_id: str) -> None:
        """Disconnect and remove connection."""
        if channel in self._connections and conn_id in self._connections[channel]:
            del self._connections[channel][conn_id]
            log.info(f"Client {conn_id} disconnected from {channel}")

    async def broadcast_to_channel(self, channel: str, data: dict[str, Any], context_filter: dict[str, str] | None = None) -> None:
        """Only send to connections whose filters match data."""
        if channel not in self._connections:
            return

        dead_connections = []
        for conn_id, conn_data in self._connections[channel].items():
            ws: WebSocket = conn_data["ws"]
            conn_filters: dict[str, str] = conn_data["filters"]
            
            if self._matches_filters(conn_filters, data, context_filter):
                try:
                    await ws.send_json(data)
                except Exception as e:
                    log.error(f"Error sending data to client {conn_id} on {channel}: {str(e)}")
                    dead_connections.append(conn_id)
        
        for conn_id in dead_connections:
            self.disconnect(channel, conn_id)

    def connection_stats(self) -> dict[str, int]:
        """Return {channel: count} for all channels."""
        return {ch: len(conns) for ch, conns in self._connections.items()}

    def _matches_filters(self, conn_filters: dict[str, str], data: dict[str, Any], context_filter: dict[str, str] | None) -> bool:
        """Check if data matches subscriber filters."""
        for key, value in conn_filters.items():
            if value is None:
                continue
            
            # Check context_filter first
            if context_filter and key in context_filter:
                if str(context_filter[key]) != str(value):
                    return False
            
            # Check data directly
            elif key in data:
                if str(data[key]) != str(value):
                    return False
        
        return True


_ws_manager = SensorWSConnectionManager()
router = APIRouter(tags=["Sensor WebSocket"])

async def _keep_alive(ws: WebSocket):
    """Send periodic keep-alive pings."""
    try:
        while True:
            await asyncio.sleep(30)
            await ws.send_json({"type": "PING", "timestamp": datetime.now(timezone.utc).isoformat()})
    except asyncio.CancelledError:
        pass
    except Exception as e:
        log.warning(f"Keepalive error: {e}")


async def _handle_ws_lifecycle(channel: str, ws: WebSocket, filters: dict[str, str]):
    conn_id = await _ws_manager.connect(channel, ws, filters)
    
    await ws.send_json({
        "type": "CONNECTED",
        "channel": channel,
        "filters": filters,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    keepalive_task = asyncio.create_task(_keep_alive(ws))
    
    try:
        while True:
            text = await ws.receive_text()
            if text == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        log.error(f"WebSocket error on /{channel}: {str(e)}")
    finally:
        keepalive_task.cancel()
        _ws_manager.disconnect(channel, conn_id)


@router.websocket("/ws/sensors")
async def websocket_sensors(
    ws: WebSocket, 
    zone_id: str | None = Query(None), 
    sensor_type: str | None = Query(None),
    plant_id: str | None = Query(None)
):
    """All readings stream."""
    filters = {k: v for k, v in {"zone_id": zone_id, "sensor_type": sensor_type, "plant_id": plant_id}.items() if v is not None}
    await _handle_ws_lifecycle("sensors", ws, filters)


@router.websocket("/ws/plant/{plant_id}")
async def websocket_plant(
    ws: WebSocket,
    plant_id: str = Path(...),
    sensor_type: str | None = Query(None)
):
    """Plant-scoped stream."""
    filters = {"plant_id": plant_id}
    if sensor_type:
        filters["sensor_type"] = sensor_type
    await _handle_ws_lifecycle("plant", ws, filters)


@router.websocket("/ws/zone/{zone_id}")
async def websocket_zone(
    ws: WebSocket,
    zone_id: str = Path(...),
    sensor_type: str | None = Query(None)
):
    """Zone-scoped stream."""
    filters = {"zone_id": zone_id}
    if sensor_type:
        filters["sensor_type"] = sensor_type
    await _handle_ws_lifecycle("zone", ws, filters)


@router.websocket("/ws/equipment/{equipment_id}")
async def websocket_equipment(
    ws: WebSocket,
    equipment_id: str = Path(...),
    sensor_type: str | None = Query(None)
):
    """Equipment-scoped stream."""
    filters = {"equipment_id": equipment_id}
    if sensor_type:
        filters["sensor_type"] = sensor_type
    await _handle_ws_lifecycle("equipment", ws, filters)


@router.websocket("/ws/alerts")
async def websocket_alerts(ws: WebSocket, severity: str | None = Query(None)):
    """Alerts stream."""
    filters = {k: v for k, v in {"severity": severity}.items() if v is not None}
    await _handle_ws_lifecycle("alerts", ws, filters)


@router.websocket("/ws/analytics")
async def websocket_analytics(ws: WebSocket, sensor_id: str | None = Query(None)):
    """Analytics stream."""
    filters = {k: v for k, v in {"sensor_id": sensor_id}.items() if v is not None}
    await _handle_ws_lifecycle("analytics", ws, filters)


@router.websocket("/ws/health")
async def websocket_health(ws: WebSocket, zone_id: str | None = Query(None)):
    """Health changes stream."""
    filters = {k: v for k, v in {"zone_id": zone_id}.items() if v is not None}
    await _handle_ws_lifecycle("health", ws, filters)


@router.get("/ws/connections")
async def get_connections():
    """Active connection count per channel."""
    return _ws_manager.connection_stats()
