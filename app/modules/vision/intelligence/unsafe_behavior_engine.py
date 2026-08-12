"""
intelligence/unsafe_behavior_engine.py — Unsafe Behavior Engine.

Detects 8 industrial unsafe behaviors:
  1. Running in hazardous zones
  2. Entering restricted areas
  3. Standing under suspended loads
  4. Unsafe ladder usage
  5. Improper lifting posture
  6. Workers too close to moving machinery
  7. Ignoring safety barriers
  8. Smoking in prohibited areas

Generates confidence scores, severity ratings, and VisionViolation records.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.modules.vision.domain.entities.vision_safety_entities import VisionViolation
from app.modules.vision.domain.enums.vision_safety_enums import UnsafeBehaviorType

log = get_logger("vision.intelligence.behavior")


class UnsafeBehaviorEngine:
    """Engine analyzing pose, kinematics, and spatial context for unsafe behaviors."""

    def evaluate_behavior(
        self,
        camera_id: str,
        zone_id: str,
        behavior_type: str | UnsafeBehaviorType,
        velocity: float = 0.0,
        distance_to_machine: float = 10.0,
        worker_id: str | None = None,
        is_smoking_detected: bool = False,
        is_suspended_load_above: bool = False,
        is_improper_posture: bool = False,
        confidence: float = 0.9,
    ) -> VisionViolation | None:
        """
        Evaluate frame features and return VisionViolation if an unsafe behavior is confirmed.
        """
        b_type_str = behavior_type.value if hasattr(behavior_type, "value") else str(behavior_type)
        severity = "MEDIUM"
        is_violation = False
        desc = ""

        if b_type_str == UnsafeBehaviorType.RUNNING_IN_HAZARDOUS_ZONE.value or velocity > 2.5:
            is_violation = True
            severity = "HIGH"
            desc = f"Worker running in hazardous zone (velocity={velocity:.1f}m/s)"

        elif b_type_str == UnsafeBehaviorType.STANDING_UNDER_SUSPENDED_LOAD.value or is_suspended_load_above:
            is_violation = True
            severity = "CRITICAL"
            desc = "Worker standing under suspended load threat"

        elif b_type_str == UnsafeBehaviorType.WORKER_TOO_CLOSE_TO_MACHINERY.value or distance_to_machine < 1.2:
            is_violation = True
            severity = "CRITICAL" if distance_to_machine < 0.5 else "HIGH"
            desc = f"Worker dangerously close to machinery (distance={distance_to_machine:.2f}m)"

        elif b_type_str == UnsafeBehaviorType.SMOKING_IN_PROHIBITED_AREA.value or is_smoking_detected:
            is_violation = True
            severity = "CRITICAL"
            desc = "Smoking in prohibited hazardous chemical area"

        elif b_type_str == UnsafeBehaviorType.IMPROPER_LIFTING_POSTURE.value or is_improper_posture:
            is_violation = True
            severity = "MEDIUM"
            desc = "Improper heavy lifting posture detected (back strain risk)"

        elif b_type_str in (
            UnsafeBehaviorType.UNSAFE_LADDER_USAGE.value,
            UnsafeBehaviorType.IGNORING_SAFETY_BARRIER.value,
            UnsafeBehaviorType.ENTERING_RESTRICTED_AREA.value,
        ):
            is_violation = True
            severity = "HIGH"
            desc = f"Unsafe behavior detected: {b_type_str}"

        if not is_violation:
            return None

        violation = VisionViolation(
            violation_type="UNSAFE_BEHAVIOR",
            severity=severity,
            worker_id=worker_id,
            camera_id=camera_id,
            zone_id=zone_id,
            description=desc,
            confidence=confidence,
        )
        log.info(f"Unsafe behavior detected [{severity}]: {desc}")
        return violation
