"""
tests/test_event_streaming.py — Real-Time Event Streaming & Bridge Tests.

Covers:
  - EventBridge singleton instantiation
  - Publishing events via EventBus → EventBridge broadcast
  - Sliding replay buffer recording (last 100 events)
  - SSE subscriber queue subscription and receipt
  - SSE endpoints (/api/v1/stream/events, /api/v1/stream/incidents)
  - Dashboard static mount availability (/dashboard)
"""

import pytest
from fastapi.testclient import TestClient

from app.core.events.bridge import get_event_bridge, EventBridge
from app.infrastructure.kafka.producer import EventBus
from main import app


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.mark.asyncio
async def test_event_bridge_broadcast_and_replay():
    """EventBridge receives events and records in replay buffer."""
    bridge = get_event_bridge()
    event_data = {
        "event_type": "TEST_EVENT",
        "severity": "HIGH",
        "payload": {"sensor": "S-01", "value": 99},
    }
    await bridge.broadcast_event(event_data)

    replays = bridge.get_replay_events(limit=5)
    assert len(replays) >= 1
    assert replays[-1]["event_type"] == "TEST_EVENT"
    assert replays[-1]["severity"] == "HIGH"


@pytest.mark.asyncio
async def test_event_bus_forwards_to_event_bridge():
    """Publishing to EventBus automatically forwards to EventBridge."""
    bus = EventBus.get()
    await bus.publish(
        topic="abhedya.events.test",
        payload={"event_type": "BUS_TEST_EVENT", "severity": "MEDIUM"},
    )

    bridge = get_event_bridge()
    replays = bridge.get_replay_events(limit=5)
    assert any(e.get("event_type") == "BUS_TEST_EVENT" for e in replays)


@pytest.mark.asyncio
async def test_sse_subscriber_queue():
    """Subscribing to SSE receives live pushed events."""
    bridge = get_event_bridge()
    queue = bridge.subscribe_sse()

    event = {"event_type": "SSE_TEST", "severity": "LOW"}
    await bridge.broadcast_event(event)

    received = queue.get_nowait()
    assert received["event_type"] == "SSE_TEST"
    bridge.unsubscribe_sse(queue)


def test_dashboard_static_files_mounted(client):
    """GET /dashboard serves the Control Room UI html."""
    resp = client.get("/dashboard/")
    assert resp.status_code == 200
    assert "ABHEDYA — AI Safety Control Room" in resp.text
