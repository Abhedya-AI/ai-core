from __future__ import annotations

import asyncio
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.logging import get_logger

log = get_logger(__name__)

ws_router = APIRouter(prefix='/ws/forecast', tags=['Forecast WebSocket'])


class ForecastBroadcaster:
    """Singleton WebSocket broadcaster for all forecast channels."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.connections: Dict[str, Set[WebSocket]] = {
                'general': set(),
                'plant': set(),
                'equipment': set(),
                'resources': set(),
                'scenarios': set(),
                'analytics': set(),
            }
        return cls._instance
    
    async def broadcast(self, channel: str, message: dict) -> None:
        """Broadcast message to all connections in a channel."""
        for ws in list(self.connections.get(channel, set())):
            try:
                await ws.send_json(message)
            except Exception:
                self.connections[channel].discard(ws)
    
    def subscribe(self, ws: WebSocket, channel: str) -> None:
        self.connections.setdefault(channel, set()).add(ws)
    
    def unsubscribe(self, ws: WebSocket, channel: str) -> None:
        self.connections.get(channel, set()).discard(ws)


broadcaster = ForecastBroadcaster()


async def _ping_loop(ws: WebSocket, channel: str):
    """Keeps connection alive with periodic pings."""
    try:
        while True:
            await asyncio.sleep(30)
            await ws.send_json({'type': 'ping', 'channel': channel})
    except (asyncio.CancelledError, Exception):
        broadcaster.unsubscribe(ws, channel)


@ws_router.websocket("")
async def general_forecast_ws(websocket: WebSocket):
    channel = 'general'
    await websocket.accept()
    broadcaster.subscribe(websocket, channel)
    await websocket.send_json({'type': 'connected', 'channel': channel, 'message': 'Forecast stream ready'})
    
    ping_task = asyncio.create_task(_ping_loop(websocket, channel))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.unsubscribe(websocket, channel)
        ping_task.cancel()


@ws_router.websocket("/plant")
async def plant_forecast_ws(websocket: WebSocket):
    channel = 'plant'
    await websocket.accept()
    broadcaster.subscribe(websocket, channel)
    await websocket.send_json({'type': 'connected', 'channel': channel, 'message': 'Forecast stream ready'})
    
    ping_task = asyncio.create_task(_ping_loop(websocket, channel))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.unsubscribe(websocket, channel)
        ping_task.cancel()


@ws_router.websocket("/equipment")
async def equipment_forecast_ws(websocket: WebSocket):
    channel = 'equipment'
    await websocket.accept()
    broadcaster.subscribe(websocket, channel)
    await websocket.send_json({'type': 'connected', 'channel': channel, 'message': 'Forecast stream ready'})
    
    ping_task = asyncio.create_task(_ping_loop(websocket, channel))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.unsubscribe(websocket, channel)
        ping_task.cancel()


@ws_router.websocket("/resources")
async def resources_forecast_ws(websocket: WebSocket):
    channel = 'resources'
    await websocket.accept()
    broadcaster.subscribe(websocket, channel)
    await websocket.send_json({'type': 'connected', 'channel': channel, 'message': 'Forecast stream ready'})
    
    ping_task = asyncio.create_task(_ping_loop(websocket, channel))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.unsubscribe(websocket, channel)
        ping_task.cancel()


@ws_router.websocket("/scenarios")
async def scenarios_forecast_ws(websocket: WebSocket):
    channel = 'scenarios'
    await websocket.accept()
    broadcaster.subscribe(websocket, channel)
    await websocket.send_json({'type': 'connected', 'channel': channel, 'message': 'Forecast stream ready'})
    
    ping_task = asyncio.create_task(_ping_loop(websocket, channel))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.unsubscribe(websocket, channel)
        ping_task.cancel()


@ws_router.websocket("/analytics")
async def analytics_forecast_ws(websocket: WebSocket):
    channel = 'analytics'
    await websocket.accept()
    broadcaster.subscribe(websocket, channel)
    await websocket.send_json({'type': 'connected', 'channel': channel, 'message': 'Forecast stream ready'})
    
    ping_task = asyncio.create_task(_ping_loop(websocket, channel))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.unsubscribe(websocket, channel)
        ping_task.cancel()
