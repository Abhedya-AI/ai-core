from __future__ import annotations

import bisect
from datetime import datetime, timedelta
from typing import Any

class TimelineController:
    def __init__(self):
        pass

    def compute_frame_timestamps(self, start: str, end: str, total_frames: int) -> list[str]:
        if total_frames <= 1:
            return [start]
        try:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            delta = (end_dt - start_dt) / (total_frames - 1)
            return [(start_dt + delta * i).isoformat() for i in range(total_frames)]
        except Exception:
            return [start] * total_frames

    def find_frame_at_timestamp(self, timestamps: list[str], target: str) -> int:
        if not timestamps:
            return 0
        idx = bisect.bisect_left(timestamps, target)
        if idx == 0:
            return 0
        if idx == len(timestamps):
            return len(timestamps) - 1
        # Closer to idx or idx-1? Simple string compare works for ISO8601
        if target <= timestamps[idx]:
            return idx - 1 if (timestamps[idx] > target and target > timestamps[idx-1]) else idx
        return idx

    def compute_playback_duration_seconds(self, total_frames: int, speed_multiplier: float, frame_interval_seconds: float = 60.0) -> float:
        return (total_frames * frame_interval_seconds) / max(0.1, speed_multiplier)

    def build_frame_events(self, state_a: dict[str, Any], state_b: dict[str, Any]) -> list[str]:
        events = []
        for k, vb in state_b.items():
            if k in state_a:
                va = state_a[k]
                ha = va.get("health_score")
                hb = vb.get("health_score")
                if ha is not None and hb is not None and abs(ha - hb) > 0.05:
                    events.append(f"{k} health changed from {ha:.2f} to {hb:.2f}")
            else:
                events.append(f"{k} appeared")
        return events

    def format_replay_progress(self, current_frame: int, total_frames: int, current_timestamp: str) -> dict[str, Any]:
        pct = 0.0 if total_frames <= 1 else (current_frame / (total_frames - 1)) * 100.0
        return {
            "pct": pct,
            "elapsed_seconds": current_frame,
            "remaining_seconds": max(0, total_frames - 1 - current_frame),
            "current_timestamp": current_timestamp
        }

    def interpolate_states(self, state_a: dict[str, Any], state_b: dict[str, Any], alpha: float) -> dict[str, Any]:
        interp = {}
        for k, va in state_a.items():
            interp[k] = dict(va)
            if k in state_b:
                vb = state_b[k]
                for prop, val_a in va.items():
                    if isinstance(val_a, (int, float)) and prop in vb:
                        val_b = vb[prop]
                        if isinstance(val_b, (int, float)):
                            interp[k][prop] = val_a + (val_b - val_a) * alpha
        return interp
