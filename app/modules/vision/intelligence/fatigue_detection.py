"""
intelligence/fatigue_detection.py — Worker Dwell & Fatigue Assessment Engine.

Evaluates micro-movements, posture slowing, shift duration, and continuous standing/sitting
dwell times to detect worker fatigue risks before incidents happen.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger

log = get_logger("vision.intelligence.fatigue")


class FatigueDetectionEngine:
    """Engine monitoring movement slowing, long dwell times, and posture fatigue indicators."""

    def evaluate_fatigue(
        self,
        worker_id: str,
        camera_id: str,
        zone_id: str,
        continuous_dwell_seconds: float,
        recent_average_velocity: float,
        posture_instability_score: float = 0.0,
        shift_hours_elapsed: float = 4.0,
    ) -> dict[str, Any]:
        """
        Evaluate worker fatigue score (0.0 - 100.0%).

        High dwell + low velocity + long shift = high fatigue score.
        """
        fatigue_score = 0.0

        # Dwell factor (> 2 hours continuous in active zone)
        if continuous_dwell_seconds > 7200:
            fatigue_score += 40.0
        elif continuous_dwell_seconds > 3600:
            fatigue_score += 20.0

        # Velocity slowing factor (< 0.2 m/s while standing)
        if recent_average_velocity < 0.15:
            fatigue_score += 25.0

        # Shift elapsed factor (> 8 hours)
        if shift_hours_elapsed >= 8.0:
            fatigue_score += 25.0
        elif shift_hours_elapsed >= 6.0:
            fatigue_score += 15.0

        # Posture instability
        fatigue_score += posture_instability_score * 10.0

        fatigue_score = min(round(fatigue_score, 1), 100.0)
        is_fatigued = fatigue_score >= 60.0

        if is_fatigued:
            log.warning(
                f"Worker fatigue warning: worker={worker_id}, score={fatigue_score}%, dwell={continuous_dwell_seconds:.0f}s"
            )

        return {
            "worker_id": worker_id,
            "camera_id": camera_id,
            "zone_id": zone_id,
            "fatigue_score": fatigue_score,
            "is_fatigued": is_fatigued,
            "continuous_dwell_seconds": continuous_dwell_seconds,
            "shift_hours_elapsed": shift_hours_elapsed,
            "recommendation": "Mandatory 15-minute rest break advised" if is_fatigued else "Normal status",
        }
