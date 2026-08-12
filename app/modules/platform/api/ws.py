from __future__ import annotations
import asyncio
import json
import time
from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.logging import get_logger
log = get_logger(__name__)

class PlatformBroadcaster:
    """Singleton broadcaster for platform WebSocket channels."""
    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = {
            "general": set(),
            "monitoring": set(),
            "models": set(),
            "alerts": set(),
            "analytics": set(),
        }
    
    async def connect(self, channel: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(channel, set()).add(ws)
        log.info(f"Platform WS connected: channel={channel}")
    
    async def disconnect(self, channel: str, ws: WebSocket) -> None:
        self._connections.get(channel, set()).discard(ws)
    
    async def broadcast(self, channel: str, data: dict[str, Any]) -> int:
        payload = json.dumps({"channel": channel, "data": data, "timestamp": time.time()})
        connections = list(self._connections.get(channel, set()))
        sent = 0
        dead = []
        for ws in connections:
            try:
                await ws.send_text(payload)
                sent += 1
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.get(channel, set()).discard(ws)
        return sent
    
    async def broadcast_all(self, data: dict[str, Any]) -> None:
        for channel in self._connections:
            await self.broadcast(channel, data)
    
    def connection_count(self, channel: str) -> int:
        return len(self._connections.get(channel, set()))

_broadcaster = PlatformBroadcaster()

def get_broadcaster() -> PlatformBroadcaster:
    return _broadcaster

ws_router = APIRouter(tags=["Platform WebSocket"])

@ws_router.websocket("/ws/platform")
async def ws_platform(websocket: WebSocket):
    broadcaster = get_broadcaster()
    await broadcaster.connect("general", websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await broadcaster.broadcast("general", {"echo": data, "type": "message"})
    except WebSocketDisconnect:
        await broadcaster.disconnect("general", websocket)

@ws_router.websocket("/ws/platform/monitoring")
async def ws_platform_monitoring(websocket: WebSocket):
    broadcaster = get_broadcaster()
    await broadcaster.connect("monitoring", websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await broadcaster.broadcast("monitoring", {"echo": data, "type": "message"})
    except WebSocketDisconnect:
        await broadcaster.disconnect("monitoring", websocket)

@ws_router.websocket("/ws/platform/models")
async def ws_platform_models(websocket: WebSocket):
    broadcaster = get_broadcaster()
    await broadcaster.connect("models", websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await broadcaster.broadcast("models", {"echo": data, "type": "message"})
    except WebSocketDisconnect:
        await broadcaster.disconnect("models", websocket)

@ws_router.websocket("/ws/platform/alerts")
async def ws_platform_alerts(websocket: WebSocket):
    broadcaster = get_broadcaster()
    await broadcaster.connect("alerts", websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await broadcaster.broadcast("alerts", {"echo": data, "type": "message"})
    except WebSocketDisconnect:
        await broadcaster.disconnect("alerts", websocket)

@ws_router.websocket("/ws/platform/analytics")
async def ws_platform_analytics(websocket: WebSocket):
    broadcaster = get_broadcaster()
    await broadcaster.connect("analytics", websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await broadcaster.broadcast("analytics", {"echo": data, "type": "message"})
    except WebSocketDisconnect:
        await broadcaster.disconnect("analytics", websocket)
