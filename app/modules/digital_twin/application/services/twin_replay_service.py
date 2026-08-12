from __future__ import annotations

import time
import uuid
import asyncio
from typing import Any, List
from app.core.logging import get_logger

log = get_logger(__name__)


class TwinReplayEngine:
    def __init__(self):
        self.sessions = {}

    async def start(self, twin_id: str, replay_by: str, start_ts: float, end_ts: float, speed: float) -> dict:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "id": session_id,
            "twin_id": twin_id,
            "replay_by": replay_by,
            "start_timestamp": start_ts,
            "end_timestamp": end_ts,
            "speed_multiplier": speed,
            "status": "PLAYING",
            "current_time": start_ts,
        }
        return self.sessions[session_id]

    async def get_frame(self, replay_id: str, frame_index: int) -> dict:
        return {"replay_id": replay_id, "frame_index": frame_index, "data": {"state": "mock_frame_data"}}

    async def control(self, replay_id: str, action: str, speed_multiplier: float = None) -> dict:
        session = self.sessions.get(replay_id)
        if not session:
            raise ValueError("Replay session not found")
        
        if action in ["PAUSE", "RESUME", "SEEK"]:
            session["status"] = action
        if speed_multiplier:
            session["speed_multiplier"] = speed_multiplier
        return session

    async def get_status(self, replay_id: str) -> dict:
        return self.sessions.get(replay_id, {"status": "NOT_FOUND"})


class TwinReplayService:
    def __init__(self, snapshot_manager: Any = None) -> None:
        self.snapshot_manager = snapshot_manager
        self._engine = TwinReplayEngine()

    async def start(
        self, twin_id: str, replay_by: str, start_timestamp: float, end_timestamp: float, speed_multiplier: float = 1.0
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        try:
            result = await self._engine.start(twin_id, replay_by, start_timestamp, end_timestamp, speed_multiplier)
            return result
        except Exception as e:
            log.error(f"Failed to start replay: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"start replay completed in {latency_ms:.2f}ms")

    async def get_frame(self, replay_id: str, frame_index: int) -> dict[str, Any]:
        t0 = time.perf_counter()
        try:
            return await self._engine.get_frame(replay_id, frame_index)
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"get_frame completed in {latency_ms:.2f}ms")

    async def control(self, replay_id: str, action: str, speed_multiplier: float = None) -> dict[str, Any]:
        t0 = time.perf_counter()
        try:
            return await self._engine.control(replay_id, action, speed_multiplier)
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"control replay completed in {latency_ms:.2f}ms")

    async def get_status(self, replay_id: str) -> dict[str, Any]:
        t0 = time.perf_counter()
        try:
            return await self._engine.get_status(replay_id)
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"get_status completed in {latency_ms:.2f}ms")
