"""
app/api/v1/vision_ws.py — Vision Intelligence WebSocket channels.

Channels:
  /ws/cameras    — Live camera status updates
  /ws/detections — Real-time detection feed
  /ws/tracking   — Active tracking updates
  /ws/video      — Frame snapshot stream
"""
from __future__ import annotations
import json
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.logging import get_logger

log = get_logger("vision.api.ws")

router = APIRouter(tags=["Vision — WebSockets"])


@router.websocket("/ws/cameras")
async def ws_cameras(websocket: WebSocket) -> None:
    """Live camera status stream."""
    await websocket.accept()
    try:
        await websocket.send_text(json.dumps({"type": "connected", "channel": "cameras", "timestamp": datetime.now(tz=timezone.utc).isoformat()}))
        while True:
            data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            await websocket.send_text(json.dumps({"type": "pong", "channel": "cameras", "timestamp": datetime.now(tz=timezone.utc).isoformat()}))
    except (WebSocketDisconnect, asyncio.TimeoutError):
        log.debug("Camera WS client disconnected")


@router.websocket("/ws/detections")
async def ws_detections(websocket: WebSocket) -> None:
    """Real-time detection event stream."""
    await websocket.accept()
    try:
        await websocket.send_text(json.dumps({"type": "connected", "channel": "detections", "timestamp": datetime.now(tz=timezone.utc).isoformat()}))
        while True:
            data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            await websocket.send_text(json.dumps({"type": "pong", "channel": "detections", "timestamp": datetime.now(tz=timezone.utc).isoformat()}))
    except (WebSocketDisconnect, asyncio.TimeoutError):
        log.debug("Detections WS client disconnected")


@router.websocket("/ws/tracking")
async def ws_tracking(websocket: WebSocket) -> None:
    """Active object tracking stream."""
    await websocket.accept()
    try:
        await websocket.send_text(json.dumps({"type": "connected", "channel": "tracking", "timestamp": datetime.now(tz=timezone.utc).isoformat()}))
        while True:
            data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            await websocket.send_text(json.dumps({"type": "pong", "channel": "tracking", "timestamp": datetime.now(tz=timezone.utc).isoformat()}))
    except (WebSocketDisconnect, asyncio.TimeoutError):
        log.debug("Tracking WS client disconnected")


@router.websocket("/ws/video")
async def ws_video(websocket: WebSocket) -> None:
    """Frame snapshot stream (base64 JPEG)."""
    await websocket.accept()
    try:
        await websocket.send_text(json.dumps({"type": "connected", "channel": "video", "timestamp": datetime.now(tz=timezone.utc).isoformat()}))
        ONE_PIXEL_JPEG = "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFgABAQEAAAAAAAAAAAAAAAAABgUEA/8QAIhAAAQMEAgMAAAAAAAAAAAAAAQIDBAURITFBUWH/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8Aon3LUqxLVHiTJ8mQ6hCW1OPKKlEAAAZJ9qm6WtFPt6eIFNiJj承認AAAAB/9k="
        for i in range(5):
            frame_msg = {
                "type": "frame",
                "channel": "video",
                "frame_index": i,
                "camera_id": "demo",
                "format": "jpeg",
                "data": ONE_PIXEL_JPEG,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            }
            await websocket.send_text(json.dumps(frame_msg))
            await asyncio.sleep(0.2)
        while True:
            data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            await websocket.send_text(json.dumps({"type": "pong", "channel": "video", "timestamp": datetime.now(tz=timezone.utc).isoformat()}))
    except (WebSocketDisconnect, asyncio.TimeoutError):
        log.debug("Video WS client disconnected")
