"""
intelligence/fire_smoke_verification.py — Multi-Modal Fire & Smoke Verification Engine.

Fuses visual camera detections with:
  - Sensor Intelligence telemetry (gas, smoke, temperature sensors)
  - Knowledge Graph zone proximity context
  - Historical incident patterns

prevents false positive alarms before escalating fire/smoke events.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.modules.vision.domain.entities.vision_assessment import VisionEmergencyCandidate
from app.modules.vision.domain.entities.vision_safety_entities import VisionViolation
from app.modules.vision.domain.enums.vision_safety_enums import VerificationStatus

log = get_logger("vision.intelligence.fire_smoke")


class FireSmokeVerificationEngine:
    """Engine cross-verifying camera fire/smoke detections with IoT sensor telemetry."""

    def verify_fire_smoke(
        self,
        camera_id: str,
        zone_id: str,
        visual_type: str,  # 'FIRE' or 'SMOKE'
        camera_confidence: float,
        sensor_smoke_detected: bool = False,
        sensor_temp_celsius: float | None = None,
        sensor_gas_ppm: float | None = None,
        nearby_sensor_count: int = 1,
        historical_incidents_in_zone: int = 0,
    ) -> tuple[VerificationStatus, float, VisionViolation | None, VisionEmergencyCandidate | None]:
        """
        Fuse multi-modal evidence.

        Returns (VerificationStatus, fused_confidence_pct, violation_or_none, emergency_candidate_or_none).
        """
        fused_score = camera_confidence * 0.5  # Base camera weight 50%

        if sensor_smoke_detected:
            fused_score += 0.30

        if sensor_temp_celsius and sensor_temp_celsius > 55.0:
            fused_score += 0.15

        if sensor_gas_ppm and sensor_gas_ppm > 100.0:
            fused_score += 0.10

        if historical_incidents_in_zone > 0:
            fused_score += 0.05

        fused_score = min(round(fused_score, 2), 1.0)

        # Thresholds
        if fused_score >= 0.70:
            status = VerificationStatus.CONFIRMED
            log.error(f"MULTI-MODAL {visual_type} CONFIRMED in zone {zone_id} (fused_confidence={fused_score})")

            violation = VisionViolation(
                violation_type=f"{visual_type}_CONFIRMED",
                severity="CRITICAL",
                camera_id=camera_id,
                zone_id=zone_id,
                description=f"Multi-modal verified {visual_type} hazard in zone {zone_id} (fused confidence: {fused_score*100:.0f}%)",
                confidence=fused_score,
            )

            emergency = VisionEmergencyCandidate(
                emergency_type=f"CONFIRMED_{visual_type}",
                zone_id=zone_id,
                severity="CRITICAL",
                trigger_reason=f"Multi-modal fusion verified {visual_type} event in zone {zone_id}. Camera={camera_id}, temp={sensor_temp_celsius}°C.",
            )

            return status, fused_score, violation, emergency

        elif fused_score >= 0.40:
            status = VerificationStatus.PENDING_FUSION
            log.warning(f"Fire/smoke detection pending multi-modal verification in zone {zone_id}")
            return status, fused_score, None, None
        else:
            status = VerificationStatus.FALSE_POSITIVE
            log.info(f"Fire/smoke detection rejected as false positive in zone {zone_id}")
            return status, fused_score, None, None
