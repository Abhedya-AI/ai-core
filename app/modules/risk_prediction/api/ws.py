import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set, Any
from app.core.logging import get_logger

from app.modules.risk_prediction.domain.models import RiskAssessment, RiskForecast

try:
    from app.api.v1.websocket import manager
except ImportError:
    manager = None

log = get_logger(__name__)

ws_router = APIRouter(prefix='/ws/risk', tags=['Risk WebSocket'])

class RiskBroadcaster:
    '''Manages WebSocket connection pools and risk update broadcasting.
    Singleton pattern — shared across all WebSocket connections.
    '''
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RiskBroadcaster, cls).__new__(cls)
            # channel -> set of websockets
            cls._instance.connections: Dict[str, Set[WebSocket]] = {
                'updates': set(),
                'forecasts': set(),
                'alerts': set(),
                'scenarios': set(),
                'analytics': set()
            }
        return cls._instance

    async def broadcast_risk_update(self, assessment: RiskAssessment) -> None:
        '''Send risk update to all connections subscribed to this entity.'''
        for ws in list(self.connections['updates']):
            try:
                await ws.send_json({
                    'type': 'risk_update',
                    'entity_id': assessment.entity_id,
                    'entity_type': assessment.entity_type.value,
                    'level': assessment.overall_risk.level.value,
                    'timestamp': assessment.timestamp.isoformat()
                })
            except Exception as e:
                log.error(f'Failed to broadcast update: {e}')
                self.unsubscribe(ws, 'updates')

    async def broadcast_alert(self, assessment: RiskAssessment, threshold: float) -> None:
        '''Send alert to all /ws/risk/alerts subscribers.'''
        for ws in list(self.connections['alerts']):
            try:
                await ws.send_json({
                    'type': 'risk_alert',
                    'entity_id': assessment.entity_id,
                    'threshold_exceeded': threshold,
                    'level': assessment.overall_risk.level.value,
                    'timestamp': assessment.timestamp.isoformat()
                })
            except Exception as e:
                log.error(f'Failed to broadcast alert: {e}')
                self.unsubscribe(ws, 'alerts')

    async def broadcast_forecast(self, forecast: RiskForecast) -> None:
        '''Send forecast update to /ws/risk/forecast subscribers.'''
        for ws in list(self.connections['forecasts']):
            try:
                await ws.send_json({
                    'type': 'forecast_update',
                    'entity_id': forecast.entity_id,
                    'timestamp': forecast.base_timestamp.isoformat()
                })
            except Exception as e:
                log.error(f'Failed to broadcast forecast: {e}')
                self.unsubscribe(ws, 'forecasts')

    def subscribe(self, websocket: WebSocket, entity_id: str, channel: str) -> None:
        if channel in self.connections:
            self.connections[channel].add(websocket)

    def unsubscribe(self, websocket: WebSocket, channel: str) -> None:
        if channel in self.connections and websocket in self.connections[channel]:
            self.connections[channel].remove(websocket)

broadcaster = RiskBroadcaster()

async def ping_loop(websocket: WebSocket, channel: str):
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({'type': 'ping'})
    except asyncio.CancelledError:
        pass
    except Exception:
        broadcaster.unsubscribe(websocket, channel)

@ws_router.websocket('')
async def websocket_risk_updates(websocket: WebSocket, entity_id: str, entity_type: str):
    await websocket.accept()
    broadcaster.subscribe(websocket, entity_id, 'updates')
    # Send initial state mock
    await websocket.send_json({'type': 'connected', 'channel': 'updates', 'entity_id': entity_id})
    ping_task = asyncio.create_task(ping_loop(websocket, 'updates'))
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.unsubscribe(websocket, 'updates')
        ping_task.cancel()

@ws_router.websocket('/forecast')
async def websocket_risk_forecasts(websocket: WebSocket, entity_id: str):
    await websocket.accept()
    broadcaster.subscribe(websocket, entity_id, 'forecasts')
    await websocket.send_json({'type': 'connected', 'channel': 'forecasts', 'entity_id': entity_id})
    ping_task = asyncio.create_task(ping_loop(websocket, 'forecasts'))
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.unsubscribe(websocket, 'forecasts')
        ping_task.cancel()

@ws_router.websocket('/alerts')
async def websocket_risk_alerts(websocket: WebSocket):
    await websocket.accept()
    broadcaster.subscribe(websocket, '*', 'alerts')
    await websocket.send_json({'type': 'connected', 'channel': 'alerts'})
    ping_task = asyncio.create_task(ping_loop(websocket, 'alerts'))
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.unsubscribe(websocket, 'alerts')
        ping_task.cancel()

@ws_router.websocket('/scenarios')
async def websocket_risk_scenarios(websocket: WebSocket):
    await websocket.accept()
    broadcaster.subscribe(websocket, '*', 'scenarios')
    await websocket.send_json({'type': 'connected', 'channel': 'scenarios'})
    ping_task = asyncio.create_task(ping_loop(websocket, 'scenarios'))
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.unsubscribe(websocket, 'scenarios')
        ping_task.cancel()

@ws_router.websocket('/analytics')
async def websocket_risk_analytics(websocket: WebSocket):
    await websocket.accept()
    broadcaster.subscribe(websocket, '*', 'analytics')
    await websocket.send_json({'type': 'connected', 'channel': 'analytics'})
    ping_task = asyncio.create_task(ping_loop(websocket, 'analytics'))
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.unsubscribe(websocket, 'analytics')
        ping_task.cancel()
