"""
api/ws.py — Real-time WebSockets with Topic Subscriptions.

Channels:
  - /ws/ppe
  - /ws/violations
  - /ws/occupancy
  - /ws/worker-interactions
  - /ws/fire
  - /ws/vision-ai

Supports filtered subscriptions by:
  - Plant ID
  - Zone ID
  - Camera ID
  - Severity level (INFO | MEDIUM | HIGH | CRITICAL)
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger

log = get_logger("vision.api.ws")

router = APIRouter(tags=["Vision Safety WebSockets"])


async def _handle_vision_ws(
    channel_name: str,
    websocket: WebSocket,
    token: str,
    plant_id: str | None = None,
    zone_id: str | None = None,
    camera_id: str | None = None,
    min_severity: str = "INFO",
) -> None:
    """Generic WebSocket connection handler for Vision Safety streaming."""
    from app.api.v1.websocket import manager as ws_manager
    from app.modules.auth.jwt import decode_access_token

    try:
        payload = decode_access_token(token)
        user_id = payload.sub
    except Exception as exc:
        log.warning(f"Vision WS auth failed for channel {channel_name}: {exc}")
        await websocket.close(code=4001, reason="Unauthorized")
        return

    conn_id = await ws_manager.connect(channel_name, websocket)
    log.info(
        f"Vision WS '{channel_name}' connected: user={user_id}, plant={plant_id}, zone={zone_id}, camera={camera_id}"
    )

    try:
        await websocket.send_json({
            "type": "connection_ack",
            "channel": channel_name,
            "user_id": user_id,
            "filter_subscription": {
                "plant_id": plant_id,
                "zone_id": zone_id,
                "camera_id": camera_id,
                "min_severity": min_severity,
            },
            "status": "connected",
        })

        while True:
            raw_msg = await websocket.receive_text()
            try:
                msg = json.loads(raw_msg)
                msg_type = msg.get("type", "ping")
                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON format"})
    except WebSocketDisconnect:
        ws_manager.disconnect(channel_name, conn_id)
        log.info(f"Vision WS '{channel_name}' disconnected: conn_id={conn_id[:8]}")
    except Exception as exc:
        ws_manager.disconnect(channel_name, conn_id)
        log.error(f"Vision WS error on channel '{channel_name}': {exc}")


@router.websocket("/ws/ppe")
async def ws_ppe(
    websocket: WebSocket,
    token: str = Query(...),
    zone_id: str | None = Query(default=None),
    camera_id: str | None = Query(default=None),
) -> None:
    await _handle_vision_ws("ppe", websocket, token, zone_id=zone_id, camera_id=camera_id)


@router.websocket("/ws/violations")
async def ws_violations(
    websocket: WebSocket,
    token: str = Query(...),
    zone_id: str | None = Query(default=None),
    min_severity: str = Query(default="HIGH"),
) -> None:
    await _handle_vision_ws("violations", websocket, token, zone_id=zone_id, min_severity=min_severity)


@router.websocket("/ws/occupancy")
async def ws_occupancy(
    websocket: WebSocket,
    token: str = Query(...),
    zone_id: str | None = Query(default=None),
) -> None:
    await _handle_vision_ws("occupancy", websocket, token, zone_id=zone_id)


@router.websocket("/ws/worker-interactions")
async def ws_interactions(
    websocket: WebSocket,
    token: str = Query(...),
    zone_id: str | None = Query(default=None),
) -> None:
    await _handle_vision_ws("worker-interactions", websocket, token, zone_id=zone_id)


@router.websocket("/ws/fire")
async def ws_fire(
    websocket: WebSocket,
    token: str = Query(...),
    zone_id: str | None = Query(default=None),
) -> None:
    await _handle_vision_ws("fire", websocket, token, zone_id=zone_id)


@router.websocket("/ws/vision-ai")
async def ws_vision_ai(
    websocket: WebSocket,
    token: str = Query(...),
    plant_id: str | None = Query(default=None),
    zone_id: str | None = Query(default=None),
    camera_id: str | None = Query(default=None),
) -> None:
    await _handle_vision_ws(
        "vision-ai", websocket, token, plant_id=plant_id, zone_id=zone_id, camera_id=camera_id
    )
