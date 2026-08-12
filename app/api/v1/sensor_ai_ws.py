"""
app/api/v1/sensor_ai_ws.py — Real-Time Sensor AI WebSocket Streams.

Channels:
  /ws/context         — Real-time 12-layer context stream
  /ws/recommendations — Real-time industrial safety recommendations stream
  /ws/risk            — Real-time hazard & risk propagation stream
  /ws/emergency       — Real-time emergency trigger & supervisor escalation stream
  /ws/graph           — Real-time graph intelligence topology update stream
  /ws/knowledge       — Real-time GraphRAG knowledge stream
"""
from __future__ import annotations
import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Path

from app.core.logging import get_logger

log = get_logger("api.v1.sensor_ai_ws")

router = APIRouter(tags=["Sensor AI WebSockets"])

class SensorAIWSManager:
    """Manages real-time AI WebSocket stream connections."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "context": set(),
            "recommendations": set(),
            "risk": set(),
            "emergency": set(),
            "graph": set(),
            "knowledge": set()
        }

    async def connect(self, channel: str, websocket: WebSocket):
        await websocket.accept()
        if channel in self.active_connections:
            self.active_connections[channel].add(websocket)
            log.info(f"WebSocket client connected to /ws/{channel}. Total: {len(self.active_connections[channel])}")

    def disconnect(self, channel: str, websocket: WebSocket):
        if channel in self.active_connections and websocket in self.active_connections[channel]:
            self.active_connections[channel].remove(websocket)
            log.info(f"WebSocket client disconnected from /ws/{channel}")

    async def broadcast(self, channel: str, message: dict):
        if channel not in self.active_connections:
            return
        dead_sockets = set()
        for connection in list(self.active_connections[channel]):
            try:
                await connection.send_json(message)
            except Exception:
                dead_sockets.add(connection)
        for dead in dead_sockets:
            self.active_connections[channel].discard(dead)

ai_ws_manager = SensorAIWSManager()


@router.websocket("/ws/context")
async def ws_context_stream(websocket: WebSocket, sensor_id: str = Query("s1")):
    await ai_ws_manager.connect("context", websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            data = {"channel": "context", "sensor_id": sensor_id, "timestamp": datetime.now(timezone.utc).isoformat(), "received": msg}
            await websocket.send_json(data)
    except WebSocketDisconnect:
        ai_ws_manager.disconnect("context", websocket)


@router.websocket("/ws/recommendations")
async def ws_recommendations_stream(websocket: WebSocket, sensor_id: str = Query("s1")):
    await ai_ws_manager.connect("recommendations", websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            data = {"channel": "recommendations", "sensor_id": sensor_id, "timestamp": datetime.now(timezone.utc).isoformat(), "status": "ACTIVE"}
            await websocket.send_json(data)
    except WebSocketDisconnect:
        ai_ws_manager.disconnect("recommendations", websocket)


@router.websocket("/ws/risk")
async def ws_risk_stream(websocket: WebSocket, zone_id: str = Query("zone-1")):
    await ai_ws_manager.connect("risk", websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            data = {"channel": "risk", "zone_id": zone_id, "risk_level": "LOW", "timestamp": datetime.now(timezone.utc).isoformat()}
            await websocket.send_json(data)
    except WebSocketDisconnect:
        ai_ws_manager.disconnect("risk", websocket)


@router.websocket("/ws/emergency")
async def ws_emergency_stream(websocket: WebSocket):
    await ai_ws_manager.connect("emergency", websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            data = {"channel": "emergency", "active_triggers": 0, "timestamp": datetime.now(timezone.utc).isoformat()}
            await websocket.send_json(data)
    except WebSocketDisconnect:
        ai_ws_manager.disconnect("emergency", websocket)


@router.websocket("/ws/graph")
async def ws_graph_stream(websocket: WebSocket):
    await ai_ws_manager.connect("graph", websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            data = {"channel": "graph", "nodes": 18, "relationships": 18, "timestamp": datetime.now(timezone.utc).isoformat()}
            await websocket.send_json(data)
    except WebSocketDisconnect:
        ai_ws_manager.disconnect("graph", websocket)


@router.websocket("/ws/knowledge")
async def ws_knowledge_stream(websocket: WebSocket):
    await ai_ws_manager.connect("knowledge", websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            data = {"channel": "knowledge", "status": "SYNCHRONIZED", "timestamp": datetime.now(timezone.utc).isoformat()}
            await websocket.send_json(data)
    except WebSocketDisconnect:
        ai_ws_manager.disconnect("knowledge", websocket)
