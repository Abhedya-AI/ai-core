from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.modules.auth.jwt import decode_access_token
from app.core.logging import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["Root Cause Analysis — WebSockets"])

async def handle_ws_connection(websocket: WebSocket, token: Optional[str] = None):
    await websocket.accept()
    if not token:
        await websocket.close(code=1008, reason="Token required")
        return None
    try:
        user_info = decode_access_token(token)
        return user_info
    except Exception as e:
        log.warning(f"WebSocket auth failed: {e}")
        await websocket.close(code=1008, reason="Invalid token")
        return None

@router.websocket("/investigations")
async def ws_investigations(websocket: WebSocket, token: str = Query(...)):
    user = await handle_ws_connection(websocket, token)
    if not user:
        return
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo investigations: {data}")
    except WebSocketDisconnect:
        log.info("WebSocket investigations disconnected")

@router.websocket("/evidence")
async def ws_evidence(websocket: WebSocket, token: str = Query(...)):
    user = await handle_ws_connection(websocket, token)
    if not user:
        return
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo evidence: {data}")
    except WebSocketDisconnect:
        log.info("WebSocket evidence disconnected")

@router.websocket("/timeline")
async def ws_timeline(websocket: WebSocket, token: str = Query(...)):
    user = await handle_ws_connection(websocket, token)
    if not user:
        return
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo timeline: {data}")
    except WebSocketDisconnect:
        log.info("WebSocket timeline disconnected")

@router.websocket("/root-cause")
async def ws_root_cause(websocket: WebSocket, token: str = Query(...)):
    user = await handle_ws_connection(websocket, token)
    if not user:
        return
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo root-cause: {data}")
    except WebSocketDisconnect:
        log.info("WebSocket root-cause disconnected")

@router.websocket("/recommendations")
async def ws_recommendations(websocket: WebSocket, token: str = Query(...)):
    user = await handle_ws_connection(websocket, token)
    if not user:
        return
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo recommendations: {data}")
    except WebSocketDisconnect:
        log.info("WebSocket recommendations disconnected")
