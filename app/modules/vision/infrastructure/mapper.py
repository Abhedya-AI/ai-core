"""
infrastructure/mapper.py — Maps raw detector outputs to domain objects.

Responsibility: translate model-specific dicts/tensors into domain
Detection objects so the domain never sees raw class IDs or pixel coords.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.vision.domain.entities import Detection
from app.modules.vision.domain.enums import DetectionStatus, HazardType
from app.modules.vision.domain.value_objects import BoundingBox
from app.modules.vision.application.calculate_risk import RiskEngine

log = get_logger("vision.mapper")

# ── Class-name → HazardType mapping ─────────────────────────────────────────
# Add new detector class labels here without touching any other file.

_CLASS_TO_HAZARD: dict[str, HazardType] = {
    # YOLO safety dataset (common labels)
    "person":              HazardType.PERSON,
    "helmet":              HazardType.HELMET,
    "hardhat":             HazardType.HELMET,
    "no-helmet":           HazardType.NO_HELMET,
    "no_helmet":           HazardType.NO_HELMET,
    "no-hardhat":          HazardType.NO_HELMET,
    "vest":                HazardType.SAFETY_VEST,
    "safety-vest":         HazardType.SAFETY_VEST,
    "safety_vest":         HazardType.SAFETY_VEST,
    "no-vest":             HazardType.NO_SAFETY_VEST,
    "no_vest":             HazardType.NO_SAFETY_VEST,
    "no-safety-vest":      HazardType.NO_SAFETY_VEST,
    "no_safety_vest":      HazardType.NO_SAFETY_VEST,
    "fire":                HazardType.FIRE,
    "smoke":               HazardType.SMOKE,
    "chemical-spill":      HazardType.CHEMICAL_SPILL,
    "chemical_spill":      HazardType.CHEMICAL_SPILL,
    "fall":                HazardType.FALL,
    "falling":             HazardType.FALL,
    "machinery":           HazardType.MACHINERY,
    "machine":             HazardType.MACHINERY,
    "forklift":            HazardType.MACHINERY,
    "crane":               HazardType.MACHINERY,
    # Unknown / unclassified
    "unknown":             HazardType.UNKNOWN,
}


def parse_camera_id(camera_id: str) -> uuid.UUID:
    """Helper to convert string camera ID to a UUID deterministically if not already a UUID."""
    try:
        return uuid.UUID(camera_id)
    except ValueError:
        return uuid.uuid5(uuid.NAMESPACE_DNS, camera_id)


def map_raw_detection(
    raw: dict,
    frame_id: str,
    camera_id: str,
    image_path: str | None = None,
) -> Detection | None:
    """
    Convert a single raw detector output to a domain Detection.
    """
    class_name = raw.get("class_name", "").lower().strip()
    hazard_type = _CLASS_TO_HAZARD.get(class_name)

    if hazard_type is None:
        log.warning(
            f"Unknown class label '{class_name}' — mapped to UNKNOWN. "
            f"Add it to infrastructure/mapper.py for a precise category."
        )
        hazard_type = HazardType.UNKNOWN

    try:
        bounding_box = BoundingBox.from_xyxy_pixels(
            x_min=int(raw["x1"]),
            y_min=int(raw["y1"]),
            x_max=int(raw["x2"]),
            y_max=int(raw["y2"]),
            image_width=int(raw["image_width"]),
            image_height=int(raw["image_height"]),
        )
    except (KeyError, ValueError, ZeroDivisionError) as exc:
        log.warning(f"Bounding box construction failed for '{class_name}': {exc}")
        return None

    confidence = float(raw["confidence"])
    risk_engine = RiskEngine()
    risk = risk_engine.calculate(hazard_type, confidence)

    camera_uuid = parse_camera_id(camera_id)
    detection_id = uuid.uuid4()

    return Detection(
        id=detection_id,
        camera_id=camera_uuid,
        hazard_type=hazard_type,
        confidence=confidence,
        bounding_box=bounding_box,
        risk=risk,
        status=DetectionStatus.PENDING,
        detected_at=datetime.now(tz=timezone.utc),
    )


def map_raw_detections(
    raws: list[dict],
    frame_id: str,
    camera_id: str,
    image_path: str | None = None,
    min_confidence: float = 0.0,
) -> list[Detection]:
    """
    Convert a list of raw detector outputs to domain Detections.
    """
    results: list[Detection] = []

    for raw in raws:
        if float(raw.get("confidence", 0.0)) < min_confidence:
            continue

        det = map_raw_detection(raw, frame_id, camera_id, image_path)
        if det is not None:
            results.append(det)

    log.debug(
        f"Mapped {len(results)}/{len(raws)} raw detections "
        f"(threshold={min_confidence})"
    )
    return results
