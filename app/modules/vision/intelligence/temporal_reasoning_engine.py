"""
intelligence/temporal_reasoning_engine.py — Multi-Frame Temporal Reasoning Engine.

Reasons across temporal frame sequences (Frame 1 -> Frame 2 -> Frame N -> Pattern -> Violation)
to eliminate single-frame false positives, detect persistent violations, and track repeated offences over sliding event windows.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.core.logging import get_logger

log = get_logger("vision.intelligence.temporal")


class TemporalViolationSequence(BaseModel):
    worker_id: str
    violation_type: str
    first_seen_timestamp: str
    last_seen_timestamp: str
    occurrence_count: int
    confirmed_persistent: bool = False


class TemporalReasoningEngine:
    """Engine maintaining sliding event windows for multi-frame pattern detection."""

    def __init__(self, min_persistence_frames: int = 3, window_seconds: float = 60.0) -> None:
        self._min_frames = min_persistence_frames
        self._window_sec = window_seconds
        self._sliding_windows: dict[str, list[dict[str, Any]]] = {}  # key -> list of event dicts

    def evaluate_temporal_pattern(
        self,
        key: str,  # worker_id or camera_id:violation_type
        current_event_type: str,
        confidence: float,
        timestamp: float,
    ) -> tuple[bool, int, float]:
        """
        Evaluate if event persists over minimum required consecutive frames.

        Returns (is_persistent_violation, occurrence_count, average_confidence).
        """
        history = self._sliding_windows.setdefault(key, [])

        # Prune old events outside window
        cutoff = timestamp - self._window_sec
        history = [e for e in history if e["ts"] >= cutoff]
        history.append({"type": current_event_type, "conf": confidence, "ts": timestamp})
        self._sliding_windows[key] = history

        # Count matching occurrences in window
        matching = [e for e in history if e["type"] == current_event_type]
        count = len(matching)
        avg_conf = sum(e["conf"] for e in matching) / max(count, 1)

        is_persistent = count >= self._min_frames

        if is_persistent and count == self._min_frames:
            log.info(
                f"Temporal reasoning CONFIRMED persistent violation: key={key}, type={current_event_type}, count={count}"
            )

        return is_persistent, count, round(avg_conf, 2)
