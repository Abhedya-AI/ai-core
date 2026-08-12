from __future__ import annotations
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

ws_router = APIRouter()

class TwinBroadcaster:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connections = {
                "general": set(),
                "state": set(),
                "simulation": set(),
                "scenarios": set(),
                "optimization": set(),
                "replay": set(),
                "analytics": set(),
            }
        return cls._instance
    
    async def connect(self, channel: str, websocket: WebSocket) -> None:
        if channel in self._connections:
            self._connections[channel].add(websocket)
            
    async def disconnect(self, channel: str, websocket: WebSocket) -> None:
        if channel in self._connections and websocket in self._connections[channel]:
            self._connections[channel].remove(websocket)
            
    async def broadcast(self, channel: str, message: dict) -> None:
        if channel not in self._connections:
            return
        dead_connections = set()
        data = json.dumps(message)
        for connection in self._connections[channel]:
            try:
                await connection.send_text(data)
            except Exception:
                dead_connections.add(connection)
        for dead in dead_connections:
            self._connections[channel].remove(dead)

    async def broadcast_state_change(self, entity_id: str, entity_type: str, old_status: str, new_status: str, health_score: float) -> None:
        await self.broadcast("state", {
            "type": "state_change",
            "entity_id": entity_id,
            "entity_type": entity_type,
            "old_status": old_status,
            "new_status": new_status,
            "health_score": health_score
        })
        
    async def broadcast_simulation_update(self, simulation_id: str, status: str, progress: float) -> None:
        await self.broadcast("simulation", {
            "type": "simulation_update",
            "simulation_id": simulation_id,
            "status": status,
            "progress": progress
        })
        
    async def broadcast_optimization_result(self, optimization_id: str, target: str, improvement_score: float) -> None:
        await self.broadcast("optimization", {
            "type": "optimization_result",
            "optimization_id": optimization_id,
            "target": target,
            "improvement_score": improvement_score
        })
        
    async def broadcast_replay_frame(self, replay_id: str, frame: dict) -> None:
        await self.broadcast("replay", {
            "type": "replay_frame",
            "replay_id": replay_id,
            "frame": frame
        })
        
    async def broadcast_analytics_update(self, analytics: dict) -> None:
        await self.broadcast("analytics", {
            "type": "analytics_update",
            "analytics": analytics
        })

@ws_router.websocket("/ws/twin")
async def twin_general_ws(websocket: WebSocket):
    broadcaster = TwinBroadcaster()
    await websocket.accept()
    await broadcaster.connect("general", websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(json.dumps({"status": "received", "data": data}))
    except WebSocketDisconnect:
        await broadcaster.disconnect("general", websocket)

@ws_router.websocket("/ws/twin/state")
async def twin_state_ws(websocket: WebSocket):
    broadcaster = TwinBroadcaster()
    await websocket.accept()
    await broadcaster.connect("state", websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await broadcaster.disconnect("state", websocket)

@ws_router.websocket("/ws/twin/simulation")
async def twin_simulation_ws(websocket: WebSocket):
    broadcaster = TwinBroadcaster()
    await websocket.accept()
    await broadcaster.connect("simulation", websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await broadcaster.disconnect("simulation", websocket)

@ws_router.websocket("/ws/twin/scenarios")
async def twin_scenarios_ws(websocket: WebSocket):
    broadcaster = TwinBroadcaster()
    await websocket.accept()
    await broadcaster.connect("scenarios", websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await broadcaster.disconnect("scenarios", websocket)

@ws_router.websocket("/ws/twin/optimization")
async def twin_optimization_ws(websocket: WebSocket):
    broadcaster = TwinBroadcaster()
    await websocket.accept()
    await broadcaster.connect("optimization", websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await broadcaster.disconnect("optimization", websocket)

@ws_router.websocket("/ws/twin/replay")
async def twin_replay_ws(websocket: WebSocket):
    broadcaster = TwinBroadcaster()
    await websocket.accept()
    await broadcaster.connect("replay", websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await broadcaster.disconnect("replay", websocket)

@ws_router.websocket("/ws/twin/analytics")
async def twin_analytics_ws(websocket: WebSocket):
    broadcaster = TwinBroadcaster()
    await websocket.accept()
    await broadcaster.connect("analytics", websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await broadcaster.disconnect("analytics", websocket)
