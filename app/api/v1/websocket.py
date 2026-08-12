"""
app/api/v1/websocket.py — WebSocket Real-time Event Streaming.

Provides live streaming of ABHEDYA domain events to connected clients.

Channels:
  /ws/events        — All domain events (raw agent output)
  /ws/incidents     — Incident status changes only
  /ws/dashboard     — Dashboard summary updates

Authentication: Bearer token in query parameter ?token=<jwt>
(WebSocket protocol does not support Authorization headers from browsers)
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.modules.auth.jwt import decode_access_token
from app.api.exceptions import TokenInvalidError, TokenExpiredError

log = get_logger("api.websocket")

router = APIRouter(tags=["WebSocket Streaming"])


# ── Connection Manager ─────────────────────────────────────────────────────────

class WSConnectionManager:
    """Manages WebSocket connections organized by channel."""

    _instance: "WSConnectionManager | None" = None

    def __init__(self) -> None:
        self._connections: dict[str, dict[str, WebSocket]] = defaultdict(dict)
        # connection_id → channel for reverse lookup
        self._conn_channels: dict[str, str] = {}

    @classmethod
    def get_instance(cls) -> "WSConnectionManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def connect(self, channel: str, websocket: WebSocket) -> str:
        """Accept a new WebSocket connection on a channel. Returns connection_id."""
        await websocket.accept()
        conn_id = str(uuid.uuid4())
        self._connections[channel][conn_id] = websocket
        self._conn_channels[conn_id] = channel
        log.info(f"WS connected: channel={channel}, conn_id={conn_id[:8]}")
        return conn_id

    def disconnect(self, conn_id: str) -> None:
        """Remove a connection from its channel."""
        channel = self._conn_channels.pop(conn_id, None)
        if channel:
            self._connections[channel].pop(conn_id, None)
            log.info(f"WS disconnected: channel={channel}, conn_id={conn_id[:8]}")

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        """Broadcast a JSON message to all connections on a channel."""
        dead: list[str] = []
        for conn_id, ws in list(self._connections.get(channel, {}).items()):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(conn_id)

        for conn_id in dead:
            self.disconnect(conn_id)

    async def broadcast_all(self, message: dict[str, Any]) -> None:
        """Broadcast to ALL channels."""
        for channel in list(self._connections.keys()):
            await self.broadcast(channel, message)

    def connection_count(self, channel: str | None = None) -> int:
        if channel:
            return len(self._connections.get(channel, {}))
        return sum(len(conns) for conns in self._connections.values())


manager = WSConnectionManager.get_instance()


# ── Auth helper ────────────────────────────────────────────────────────────────

async def _authenticate_ws(token: str | None) -> dict | None:
    """Validate JWT from query param. Returns claims or None if invalid."""
    if not token:
        return None
    try:
        return decode_access_token(token)
    except (TokenExpiredError, TokenInvalidError):
        return None


# ── Heartbeat task ─────────────────────────────────────────────────────────────

async def _heartbeat(websocket: WebSocket, interval: int = 30) -> None:
    """Send periodic ping to keep connection alive."""
    while True:
        await asyncio.sleep(interval)
        try:
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            break


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.websocket("/ws/events")
async def ws_events(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    """
    WebSocket endpoint: streams all ABHEDYA domain events.
    Authentication: ?token=<access_jwt>
    """
    claims = await _authenticate_ws(token)
    if not claims:
        await websocket.close(code=4001, reason="Authentication required")
        return

    conn_id = await manager.connect("events", websocket)
    # Send welcome message
    await websocket.send_json({
        "type": "connected",
        "channel": "events",
        "conn_id": conn_id,
        "user_id": claims.get("sub"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    heartbeat_task = asyncio.create_task(_heartbeat(websocket))
    try:
        while True:
            # Keep connection open — events are pushed via manager.broadcast()
            data = await websocket.receive_text()
            # Handle ping/pong from client
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        manager.disconnect(conn_id)


@router.websocket("/ws/incidents")
async def ws_incidents(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    """
    WebSocket endpoint: streams incident status changes only.
    """
    claims = await _authenticate_ws(token)
    if not claims:
        await websocket.close(code=4001, reason="Authentication required")
        return

    conn_id = await manager.connect("incidents", websocket)
    await websocket.send_json({
        "type": "connected",
        "channel": "incidents",
        "conn_id": conn_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    heartbeat_task = asyncio.create_task(_heartbeat(websocket))
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        manager.disconnect(conn_id)


@router.websocket("/ws/dashboard")
async def ws_dashboard(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    """
    WebSocket endpoint: real-time dashboard metrics and summaries.
    No authentication required for read-only dashboard view.
    """
    conn_id = await manager.connect("dashboard", websocket)
    await websocket.send_json({
        "type": "connected",
        "channel": "dashboard",
        "conn_id": conn_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "active_connections": manager.connection_count(),
    })

    heartbeat_task = asyncio.create_task(_heartbeat(websocket))
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        manager.disconnect(conn_id)


@router.get(
    "/ws/status",
    tags=["WebSocket Streaming"],
    summary="WebSocket connection status",
    operation_id="ws_status",
)
async def ws_status() -> dict:
    """Return current WebSocket connection counts by channel."""
    return {
        "active_connections": manager.connection_count(),
        "by_channel": {
            "events": manager.connection_count("events"),
            "incidents": manager.connection_count("incidents"),
            "dashboard": manager.connection_count("dashboard"),
        },
    }
