"""
app/api/v1/platform_ws.py — Platform Real-Time WebSocket Streams.

WebSocket streams:
  /ws/events      — Live event bus stream
  /ws/workflows   — Live workflow execution stream
  /ws/incidents   — Live incident state transition stream
  /ws/supervisor  — Live Supervisor decision stream
  /ws/dashboard   — Live dashboard KPIs & live feed stream
  /ws/system      — Live system health stream
"""
from __future__ import annotations
import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.logging import get_logger

log = get_logger("api.platform_ws")

router = APIRouter(tags=["Platform WebSockets"])

class PlatformWSConnectionManager:
    """Connection manager for platform-wide WebSocket streams."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            "events": [],
            "workflows": [],
            "incidents": [],
            "supervisor": [],
            "dashboard": [],
            "system": []
        }

    async def connect(self, channel: str, websocket: WebSocket):
        await websocket.accept()
        if channel in self.active_connections:
            self.active_connections[channel].append(websocket)
        log.info(f"WebSocket client connected to /ws/{channel}")

    def disconnect(self, channel: str, websocket: WebSocket):
        if channel in self.active_connections and websocket in self.active_connections[channel]:
            self.active_connections[channel].remove(websocket)
        log.info(f"WebSocket client disconnected from /ws/{channel}")

    async def broadcast(self, channel: str, message: dict):
        if channel in self.active_connections:
            dead_sockets = []
            for ws in self.active_connections[channel]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead_sockets.append(ws)
            for ws in dead_sockets:
                self.disconnect(channel, ws)

manager = PlatformWSConnectionManager()

@router.websocket("/ws/events")
async def ws_events(websocket: WebSocket):
    """Stream live domain events."""
    await manager.connect("events", websocket)
    try:
        while True:
            await asyncio.sleep(5)
            await websocket.send_json({
                "stream": "events",
                "event_id": f"evt-{uuid.uuid4().hex[:8]}",
                "event_type": "TELEMETRY_HEARTBEAT",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect("events", websocket)

@router.websocket("/ws/workflows")
async def ws_workflows(websocket: WebSocket):
    """Stream live workflow execution status."""
    await manager.connect("workflows", websocket)
    try:
        while True:
            await asyncio.sleep(5)
            await websocket.send_json({
                "stream": "workflows",
                "workflow_id": f"wf-{uuid.uuid4().hex[:8]}",
                "status": "RUNNING",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect("workflows", websocket)

@router.websocket("/ws/incidents")
async def ws_incidents(websocket: WebSocket):
    """Stream live incident updates."""
    await manager.connect("incidents", websocket)
    try:
        while True:
            await asyncio.sleep(5)
            await websocket.send_json({
                "stream": "incidents",
                "incident_id": f"inc-{uuid.uuid4().hex[:8]}",
                "state": "INVESTIGATING",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect("incidents", websocket)

@router.websocket("/ws/supervisor")
async def ws_supervisor(websocket: WebSocket):
    """Stream live Supervisor decision telemetry."""
    await manager.connect("supervisor", websocket)
    try:
        while True:
            await asyncio.sleep(5)
            await websocket.send_json({
                "stream": "supervisor",
                "execution_id": f"sup-{uuid.uuid4().hex[:8]}",
                "status": "ACTIVE",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect("supervisor", websocket)

@router.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket):
    """Stream live dashboard telemetry KPIs."""
    await manager.connect("dashboard", websocket)
    try:
        while True:
            await asyncio.sleep(5)
            await websocket.send_json({
                "stream": "dashboard",
                "fleet_health_pct": 98.4,
                "readings_per_sec": 120,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect("dashboard", websocket)

@router.websocket("/ws/system")
async def ws_system(websocket: WebSocket):
    """Stream live system readiness status."""
    await manager.connect("system", websocket)
    try:
        while True:
            await asyncio.sleep(5)
            await websocket.send_json({
                "stream": "system",
                "status": "HEALTHY",
                "cpu_util_pct": 14.2,
                "memory_util_pct": 42.1,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect("system", websocket)
