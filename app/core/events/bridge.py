"""
app/core/events/bridge.py — Event Bus to WebSocket / SSE Bridge.

Connects the internal EventBus (Kafka/In-Memory) to the API Gateway's
WebSocket ConnectionManager and SSE event streams.

Features:
  - Event listener attached to EventBus
  - Real-time fanout to WebSocket channels (`events`, `incidents`, `dashboard`)
  - Sliding window buffer of the last 100 events (for replay upon client connection)
  - Filtering by event severity and domain type
"""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Any

from app.api.v1.websocket import manager as ws_manager
from app.core.logging import get_logger

log = get_logger("events.bridge")

REPLAY_BUFFER_SIZE = 100


class EventBridge:
    """Singleton bridge between EventBus and HTTP streaming outputs (WS/SSE)."""

    _instance: "EventBridge | None" = None

    def __init__(self) -> None:
        self._replay_buffer: deque[dict[str, Any]] = deque(maxlen=REPLAY_BUFFER_SIZE)
        self._sse_subscribers: set[asyncio.Queue] = set()

    @classmethod
    def get_instance(cls) -> "EventBridge":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def broadcast_event(self, event_data: dict[str, Any]) -> None:
        """
        Ingest a domain event, record in replay buffer, and push to WS & SSE subscribers.

        Args:
            event_data: Standardized domain event dict.
        """
        # Ensure timestamp present
        if "timestamp" not in event_data:
            event_data["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Add to replay buffer
        self._replay_buffer.append(event_data)

        # 1. Broadcast to WebSocket 'events' channel
        await ws_manager.broadcast("events", {
            "type": "domain_event",
            "data": event_data,
        })

        # 2. If it's an incident or high severity event, also push to 'incidents' / 'dashboard'
        event_type = str(event_data.get("event_type", ""))
        severity = str(event_data.get("severity", "LOW")).upper()

        if "INCIDENT" in event_type or severity in ("HIGH", "CRITICAL", "EMERGENCY"):
            await ws_manager.broadcast("incidents", {
                "type": "incident_alert",
                "data": event_data,
            })
            await ws_manager.broadcast("dashboard", {
                "type": "dashboard_update",
                "data": event_data,
            })

        # 3. Push to all connected SSE queues
        dead_queues = set()
        for q in list(self._sse_subscribers):
            try:
                q.put_nowait(event_data)
            except asyncio.QueueFull:
                dead_queues.add(q)
            except Exception:
                dead_queues.add(q)

        for q in dead_queues:
            self._sse_subscribers.discard(q)

    def get_replay_events(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return the most recent buffered events for newly connected clients."""
        events = list(self._replay_buffer)
        return events[-limit:]

    def subscribe_sse(self) -> asyncio.Queue:
        """Register a new SSE client subscriber queue."""
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._sse_subscribers.add(q)
        return q

    def unsubscribe_sse(self, q: asyncio.Queue) -> None:
        """Unregister an SSE client subscriber queue."""
        self._sse_subscribers.discard(q)


# ── Module Singleton ───────────────────────────────────────────────────────────

_event_bridge: EventBridge | None = None


def get_event_bridge() -> EventBridge:
    global _event_bridge
    if _event_bridge is None:
        _event_bridge = EventBridge()
    return _event_bridge
