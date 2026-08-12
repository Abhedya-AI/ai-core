"""
app/api/v1/sse.py — Server-Sent Events (SSE) Streaming Router.

Provides HTTP text/event-stream endpoints as a lightweight alternative
to WebSockets for browser and dashboard streaming clients.

Endpoints:
  GET /api/v1/stream/events     — Real-time stream of all domain events
  GET /api/v1/stream/incidents  — Real-time stream of incident alerts
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from app.core.events.bridge import get_event_bridge
from app.core.logging import get_logger

log = get_logger("api.sse")

router = APIRouter(prefix="/stream", tags=["Server-Sent Events"])


@router.get("/events", summary="Stream domain events via SSE", operation_id="sse_stream_events")
async def stream_events(request: Request):
    """
    Server-Sent Events stream for real-time domain event monitoring.
    Replays recent buffered events first, then streams live events.
    """
    bridge = get_event_bridge()

    async def event_generator():
        # 1. Send initial replay buffer
        replays = bridge.get_replay_events(limit=20)
        for evt in replays:
            yield {
                "event": "replay",
                "data": json.dumps(evt),
            }

        # 2. Subscribe to live events queue
        queue = bridge.subscribe_sse()
        try:
            while True:
                # Check client disconnect
                if await request.is_disconnected():
                    break

                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {
                        "event": "domain_event",
                        "data": json.dumps(event),
                    }
                except asyncio.TimeoutError:
                    # Send periodic keep-alive comment
                    yield {
                        "event": "ping",
                        "data": json.dumps({"timestamp": datetime.now(timezone.utc).isoformat()}),
                    }
        finally:
            bridge.unsubscribe_sse(queue)

    return EventSourceResponse(event_generator())


@router.get("/incidents", summary="Stream incident alerts via SSE", operation_id="sse_stream_incidents")
async def stream_incidents(request: Request):
    """
    SSE stream filtered specifically for high-severity incident events.
    """
    bridge = get_event_bridge()

    async def incident_generator():
        queue = bridge.subscribe_sse()
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    severity = str(event.get("severity", "LOW")).upper()
                    event_type = str(event.get("event_type", ""))
                    if "INCIDENT" in event_type or severity in ("HIGH", "CRITICAL", "EMERGENCY"):
                        yield {
                            "event": "incident_alert",
                            "data": json.dumps(event),
                        }
                except asyncio.TimeoutError:
                    yield {
                        "event": "ping",
                        "data": json.dumps({"timestamp": datetime.now(timezone.utc).isoformat()}),
                    }
        finally:
            bridge.unsubscribe_sse(queue)

    return EventSourceResponse(incident_generator())
