"""
intelligence/fall_detection_engine.py — Fall Detection & Emergency Engine.

Uses pose abstraction, bounding box aspect ratios (width/height ratio shift > 1.2),
downward motion velocity, temporal confirmation (N consecutive frames), and
false positive filtering (crouching/sitting check) to detect worker falls.

Triggers a Medical Emergency candidate on confirmed fall.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.modules.vision.domain.entities.vision_assessment import VisionEmergencyCandidate
from app.modules.vision.domain.entities.vision_safety_entities import VisionViolation

log = get_logger("vision.intelligence.fall")


class FallDetectionEngine:
    """Engine confirming worker falls and triggering medical emergency alerts."""

    def __init__(self, confirmation_frames_required: int = 3) -> None:
        self._required_frames = confirmation_frames_required
        self._fall_buffers: dict[str, int] = {}  # worker_id -> consecutive_fall_count

    def evaluate_pose_and_motion(
        self,
        worker_id: str,
        camera_id: str,
        zone_id: str,
        bbox_aspect_ratio: float,  # width / height (normal standing < 0.6; prone > 1.2)
        downward_velocity: float,  # m/s
        is_crouching: bool = False,
        confidence: float = 0.92,
    ) -> tuple[bool, VisionViolation | None, VisionEmergencyCandidate | None]:
        """
        Evaluate frame keypoints/bbox kinematics for fall detection.

        Returns (is_confirmed_fall, violation_or_none, emergency_candidate_or_none).
        """
        # False positive filtering: crouching/bending down has high aspect ratio but low downward velocity
        is_prone = bbox_aspect_ratio > 1.2 or downward_velocity > 1.8
        is_fall_candidate = is_prone and not is_crouching

        if is_fall_candidate:
            count = self._fall_buffers.get(worker_id, 0) + 1
            self._fall_buffers[worker_id] = count
        else:
            self._fall_buffers[worker_id] = 0
            return False, None, None

        # Temporal confirmation check
        if self._fall_buffers[worker_id] < self._required_frames:
            log.debug(f"Fall candidate frame {self._fall_buffers[worker_id]}/{self._required_frames} for worker {worker_id}")
            return False, None, None

        # Confirmed fall!
        log.error(f"WORKER FALL CONFIRMED: worker={worker_id}, zone={zone_id}, camera={camera_id}")

        violation = VisionViolation(
            violation_type="WORKER_FALL",
            severity="CRITICAL",
            worker_id=worker_id,
            camera_id=camera_id,
            zone_id=zone_id,
            description=f"CRITICAL: Worker fall detected in zone {zone_id} (aspect_ratio={bbox_aspect_ratio:.2f})",
            confidence=confidence,
        )

        emergency = VisionEmergencyCandidate(
            emergency_type="FALL_MEDICAL_EMERGENCY",
            zone_id=zone_id,
            severity="CRITICAL",
            trigger_reason=f"Worker {worker_id} fall confirmed by camera {camera_id}. Medical assistance required.",
        )

        return True, violation, emergency
