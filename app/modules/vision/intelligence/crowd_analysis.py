"""
intelligence/crowd_analysis.py — Crowd Congestion & Dynamics Engine.

Detects crowd formation, bottlenecking, congestion thresholds, and movement flow disruptions.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger

log = get_logger("vision.intelligence.crowd")


class CrowdAnalysisEngine:
    """Engine assessing crowd density, bottlenecking, and flow velocity."""

    def analyze_crowd(
        self,
        zone_id: str,
        worker_count: int,
        average_velocity: float,
        congestion_threshold_count: int = 15,
        velocity_bottleneck_threshold: float = 0.5,
    ) -> dict[str, Any]:
        """
        Analyze crowd dynamics.

        Returns {is_congested, is_bottlenecked, congestion_severity, recommendation}.
        """
        is_congested = worker_count >= congestion_threshold_count
        is_bottlenecked = is_congested and average_velocity < velocity_bottleneck_threshold

        severity = "LOW"
        if is_bottlenecked:
            severity = "HIGH"
            log.warning(f"Crowd bottleneck detected in zone {zone_id}: count={worker_count}, avg_velocity={average_velocity:.2f}m/s")
        elif is_congested:
            severity = "MEDIUM"

        return {
            "zone_id": zone_id,
            "worker_count": worker_count,
            "average_velocity": average_velocity,
            "is_congested": is_congested,
            "is_bottlenecked": is_bottlenecked,
            "congestion_severity": severity,
            "recommendation": "Open secondary exit corridor" if is_bottlenecked else "Monitor zone flow",
        }
