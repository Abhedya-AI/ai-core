"""
intelligence/ppe_engine.py — PPE Compliance Engine.

Evaluates detected items against zone, role, and equipment-specific PPE policies.
Supported PPE items: Helmet, Vest, Safety Shoes, Gloves, Mask, Face Shield, Goggles, Harness, Ear Protection.

Generates:
  - Compliance percentage (0-100%)
  - Missing PPE items & violation records
  - Repeated offender risk score
  - Mitigation recommendations
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.modules.vision.domain.entities.vision_safety_entities import PPEViolation

log = get_logger("vision.intelligence.ppe")

# Default baseline policy requirement
DEFAULT_REQUIRED_PPE = ["HELMET", "SAFETY_VEST"]

# Policy matrix mapping zone/equipment/role to required PPE
POLICY_MATRIX: dict[str, list[str]] = {
    "ZONE_HIGH_RISK": ["HELMET", "SAFETY_VEST", "SAFETY_SHOES", "GLOVES"],
    "ZONE_CHEMICAL": ["HELMET", "SAFETY_VEST", "MASK", "FACE_SHIELD", "GLOVES"],
    "ZONE_NOISE": ["HELMET", "SAFETY_VEST", "EAR_PROTECTION"],
    "ZONE_HEIGHTS": ["HELMET", "SAFETY_VEST", "HARNESS"],
    "EQUIPMENT_CRANE": ["HELMET", "SAFETY_VEST", "SAFETY_SHOES"],
    "EQUIPMENT_GRINDER": ["HELMET", "GOGGLES", "GLOVES", "EAR_PROTECTION"],
    "ROLE_ELECTRICIAN": ["HELMET", "GLOVES", "SAFETY_SHOES", "GOGGLES"],
}


class PPEComplianceEngine:
    """Engine computing PPE compliance scores and detecting violations."""

    def __init__(self) -> None:
        self._offender_history: dict[str, int] = {}  # worker_id -> violation_count

    def resolve_policy(
        self,
        zone_type: str | None = None,
        equipment_type: str | None = None,
        worker_role: str | None = None,
    ) -> list[str]:
        """Determine required PPE items based on zone, equipment, and role context."""
        required = set(DEFAULT_REQUIRED_PPE)

        if zone_type and zone_type in POLICY_MATRIX:
            required.update(POLICY_MATRIX[zone_type])
        if equipment_type and equipment_type in POLICY_MATRIX:
            required.update(POLICY_MATRIX[equipment_type])
        if worker_role and worker_role in POLICY_MATRIX:
            required.update(POLICY_MATRIX[worker_role])

        return sorted(list(required))

    def evaluate(
        self,
        detected_ppe: list[str],
        camera_id: str,
        zone_id: str,
        worker_id: str | None = None,
        zone_type: str | None = None,
        equipment_type: str | None = None,
        worker_role: str | None = None,
    ) -> tuple[float, list[str], PPEViolation | None]:
        """
        Evaluate compliance.

        Returns (compliance_score_pct, missing_ppe_list, ppe_violation_or_none).
        """
        required = self.resolve_policy(zone_type, equipment_type, worker_role)
        detected_set = {p.upper() for p in detected_ppe}
        required_set = {p.upper() for p in required}

        missing = sorted(list(required_set - detected_set))
        present = sorted(list(required_set.intersection(detected_set)))

        if not required_set:
            score = 100.0
        else:
            score = round((len(present) / len(required_set)) * 100.0, 1)

        violation: PPEViolation | None = None
        if missing:
            # Track repeat offender count
            offender_count = 1
            if worker_id:
                self._offender_history[worker_id] = self._offender_history.get(worker_id, 0) + 1
                offender_count = self._offender_history[worker_id]

            risk_level = "CRITICAL" if (score < 50.0 or offender_count > 3) else ("HIGH" if score < 75.0 else "MEDIUM")

            violation = PPEViolation(
                worker_id=worker_id,
                camera_id=camera_id,
                zone_id=zone_id,
                missing_ppe=missing,
                detected_ppe=present,
                compliance_score=score,
                risk_level=risk_level,
                policy_id=f"POL-PPE-{zone_id}",
            )
            log.info(f"PPE Violation detected: worker={worker_id}, missing={missing}, score={score}%")

        return score, missing, violation

    def get_repeat_offenders(self, threshold: int = 3) -> dict[str, int]:
        """Return dict of worker_ids exceeding violation threshold."""
        return {w: cnt for w, cnt in self._offender_history.items() if cnt >= threshold}
