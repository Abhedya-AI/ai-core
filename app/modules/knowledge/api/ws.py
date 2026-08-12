"""
api/ws.py — WebSocket Graph Mutation & Event Streaming.

Provides real-time WebSocket streaming of graph mutations, traversals,
and sync events to connected clients.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger

log = get_logger("knowledge.api.ws")

router = APIRouter(tags=["Knowledge Graph WebSocket"])


@router.websocket("/ws/graph")
async def graph_websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
) -> None:
    """
    WebSocket endpoint for real-time Knowledge Graph mutation events.
    """
    from app.api.v1.websocket import manager as ws_manager
    from app.modules.auth.jwt import decode_access_token
    try:
        payload = decode_access_token(token)
        user_id = payload.sub
    except Exception as exc:
        log.warning(f"WebSocket auth failed: {exc}")
        await websocket.close(code=4001, reason="Unauthorized")
        return

    conn_id = await ws_manager.connect("graph", websocket)
    log.info(f"Graph WS connected: user={user_id}, conn_id={conn_id[:8]}")

    try:
        # Send initial connection acknowledgment
        await websocket.send_json({
            "type": "connection_ack",
            "channel": "graph",
            "user_id": user_id,
            "status": "connected",
        })

        # Keep connection open and handle client messages
        while True:
            raw_msg = await websocket.receive_text()
            try:
                msg = json.loads(raw_msg)
                msg_type = msg.get("type", "ping")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg_type == "subscribe":
                    entity_type = msg.get("entity_type")
                    await websocket.send_json({
                        "type": "subscribed",
                        "entity_type": entity_type,
                    })
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON format"})
    except WebSocketDisconnect:
        ws_manager.disconnect("graph", conn_id)
        log.info(f"Graph WS disconnected: conn_id={conn_id[:8]}")
    except Exception as exc:
        ws_manager.disconnect("graph", conn_id)
        log.error(f"Graph WS error: {exc}")
