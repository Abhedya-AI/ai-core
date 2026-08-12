from __future__ import annotations

import uuid
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.application.replay.timeline_controller import TimelineController

log = get_logger(__name__)

class TwinReplayEngine:
    def __init__(self, snapshot_manager: Any = None):
        self.snapshot_manager = snapshot_manager
        self._sessions: dict[str, dict[str, Any]] = {}
        self._frames: dict[str, list[dict[str, Any]]] = {}
        self.timeline_controller = TimelineController()
        
    async def start_replay(self, twin_id: str, replay_by: str, start_timestamp: str, end_timestamp: str, speed_multiplier: float = 1.0) -> dict[str, Any]:
        replay_id = str(uuid.uuid4())
        
        # Load relevant snapshots
        snapshots = []
        if self.snapshot_manager:
            try:
                # Assuming snapshot_manager has get_snapshots_in_range
                pass
            except Exception as e:
                log.warning(f"Snapshot manager error: {e}")
                
        # Mocking frames for now since we don't have real snapshots
        frames = [
            {"frame": 0, "timestamp": start_timestamp, "entities": {}, "events": ["Replay started"], "progress_pct": 0.0},
            {"frame": 1, "timestamp": end_timestamp, "entities": {}, "events": ["Replay ended"], "progress_pct": 100.0}
        ]
        
        self._frames[replay_id] = frames
        
        session = {
            "replay_id": replay_id,
            "twin_id": twin_id,
            "replay_by": replay_by,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "speed_multiplier": speed_multiplier,
            "status": "PLAYING",
            "current_frame": 0,
            "total_frames": len(frames)
        }
        self._sessions[replay_id] = session
        return session
        
    async def get_frame(self, replay_id: str, frame_index: int) -> dict[str, Any]:
        if replay_id not in self._frames:
            return {}
        frames = self._frames[replay_id]
        if frame_index < 0 or frame_index >= len(frames):
            return {}
        return frames[frame_index]
        
    async def advance_frame(self, replay_id: str) -> dict[str, Any]:
        if replay_id not in self._sessions:
            return {}
        session = self._sessions[replay_id]
        if session["status"] == "PLAYING" and session["current_frame"] < session["total_frames"] - 1:
            session["current_frame"] += 1
            if session["current_frame"] == session["total_frames"] - 1:
                session["status"] = "COMPLETED"
        return await self.get_frame(replay_id, session["current_frame"])
        
    async def seek(self, replay_id: str, target_timestamp: str) -> dict[str, Any]:
        if replay_id not in self._sessions:
            return {}
        frames = self._frames.get(replay_id, [])
        timestamps = [f["timestamp"] for f in frames]
        idx = self.timeline_controller.find_frame_at_timestamp(timestamps, target_timestamp)
        self._sessions[replay_id]["current_frame"] = idx
        return await self.get_frame(replay_id, idx)
        
    async def pause(self, replay_id: str) -> dict[str, Any]:
        if replay_id in self._sessions:
            self._sessions[replay_id]["status"] = "PAUSED"
        return self._sessions.get(replay_id, {})
        
    async def resume(self, replay_id: str) -> dict[str, Any]:
        if replay_id in self._sessions:
            if self._sessions[replay_id]["status"] != "COMPLETED":
                self._sessions[replay_id]["status"] = "PLAYING"
        return self._sessions.get(replay_id, {})
        
    async def set_speed(self, replay_id: str, speed_multiplier: float) -> dict[str, Any]:
        if replay_id in self._sessions:
            self._sessions[replay_id]["speed_multiplier"] = max(0.25, min(10.0, speed_multiplier))
        return self._sessions.get(replay_id, {})
        
    async def complete_replay(self, replay_id: str) -> dict[str, Any]:
        if replay_id in self._sessions:
            self._sessions[replay_id]["status"] = "COMPLETED"
            self._sessions[replay_id]["current_frame"] = self._sessions[replay_id]["total_frames"] - 1
        return self._sessions.get(replay_id, {})
