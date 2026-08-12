from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.modules.auth.jwt import decode_access_token
from app.core.logging import get_logger

log = get_logger("root_cause.api.intelligence_ws")
router = APIRouter()

async def authenticate_ws(websocket: WebSocket, token: str):
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return False
    try:
        # Mocking decoding for now, decode_access_token would validate it
        decode_access_token(token)
        return True
    except Exception:
        await websocket.close(code=1008, reason="Invalid token")
        return False

@router.websocket("/ws/rca/memory")
async def ws_memory(websocket: WebSocket, token: str = Query(None)):
    await websocket.accept()
    if not await authenticate_ws(websocket, token):
        return
    await websocket.send_json({"message": "Hello from memory stream"})
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"channel": "memory", "echo": data})
    except WebSocketDisconnect:
        log.info("Client disconnected from /ws/rca/memory")

@router.websocket("/ws/rca/context")
async def ws_context(websocket: WebSocket, token: str = Query(None)):
    await websocket.accept()
    if not await authenticate_ws(websocket, token):
        return
    await websocket.send_json({"message": "Hello from context stream"})
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"channel": "context", "echo": data})
    except WebSocketDisconnect:
        log.info("Client disconnected from /ws/rca/context")

@router.websocket("/ws/rca/patterns")
async def ws_patterns(websocket: WebSocket, token: str = Query(None)):
    await websocket.accept()
    if not await authenticate_ws(websocket, token):
        return
    await websocket.send_json({"message": "Hello from patterns stream"})
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"channel": "patterns", "echo": data})
    except WebSocketDisconnect:
        log.info("Client disconnected from /ws/rca/patterns")

@router.websocket("/ws/rca/counterfactual")
async def ws_counterfactual(websocket: WebSocket, token: str = Query(None)):
    await websocket.accept()
    if not await authenticate_ws(websocket, token):
        return
    await websocket.send_json({"message": "Hello from counterfactual stream"})
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"channel": "counterfactual", "echo": data})
    except WebSocketDisconnect:
        log.info("Client disconnected from /ws/rca/counterfactual")

@router.websocket("/ws/rca/feedback")
async def ws_feedback(websocket: WebSocket, token: str = Query(None)):
    await websocket.accept()
    if not await authenticate_ws(websocket, token):
        return
    await websocket.send_json({"message": "Hello from feedback stream"})
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"channel": "feedback", "echo": data})
    except WebSocketDisconnect:
        log.info("Client disconnected from /ws/rca/feedback")
