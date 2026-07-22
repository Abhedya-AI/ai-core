"""
infrastructure/mapper.py — Maps raw detector outputs to domain objects.

Responsibility: translate model-specific dicts/tensors into domain
Detection objects so the domain never sees raw class IDs or pixel coords.

Design
──────
• This file is the only place raw class labels are translated.
• Adding a new detector (RT-DETR, Grounding DINO) requires only a new
  mapping dict below — no domain changes.
• Normalisation of bounding boxes happens here, not in the detector.

Expected raw detection format (adapter dict)
────────────────────────────────────────────
Each detector implementation must produce a list of dicts:
{
    "class_name": str,       # raw model class label
    "confidence": float,     # model confidence ∈ [0, 1]
    "x1": int,               # pixel coordinates (absolute)
    "y1": int,
    "x2": int,
    "y2": int,
    "image_width": int,
    "image_height": int,
}
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.modules.vision.domain.entities import Detection
from app.modules.vision.domain.enums import HazardType
from app.modules.vision.domain.value_objects import BoundingBox

log = get_logger("vision.mapper")

# ── Class-name → HazardType mapping ─────────────────────────────────────────
# Add new detector class labels here without touching any other file.

_CLASS_TO_HAZARD: dict[str, HazardType] = {
    # YOLO safety dataset (common labels)
    "person":           HazardType.PERSON,
    "helmet":           HazardType.HELMET,
    "no-helmet":        HazardType.NO_HELMET,
    "no_helmet":        HazardType.NO_HELMET,
    "hardhat":          HazardType.HELMET,
    "no-hardhat":       HazardType.NO_HELMET,
    "vest":             HazardType.VEST,
    "safety-vest":      HazardType.VEST,
    "no-vest":          HazardType.NO_VEST,
    "no_vest":          HazardType.NO_VEST,
    "fire":             HazardType.FIRE,
    "smoke":            HazardType.SMOKE,
    "chemical-spill":   HazardType.CHEMICAL_SPILL,
    "chemical_spill":   HazardType.CHEMICAL_SPILL,
    "fall":             HazardType.FALL,
    "falling":          HazardType.FALL,
    "machinery":        HazardType.MACHINERY,
    "machine":          HazardType.MACHINERY,
    "forklift":         HazardType.MACHINERY,
    "crane":            HazardType.MACHINERY,
}


def map_raw_detection(
    raw: dict,
    frame_id: str,
    camera_id: str,
    image_path: str | None = None,
) -> Detection | None:
    """
    Convert a single raw detector output to a domain Detection.

    Returns None if the class label is not in the mapping (unknown class).

    Parameters
    ──────────
    raw         Adapter dict produced by the detector.
    frame_id    Caller-supplied frame identifier.
    camera_id   Source camera identifier.
    image_path  Optional persisted image path.

    Returns
    ───────
    Detection | None
    """
    class_name = raw.get("class_name", "").lower().strip()
    hazard_type = _CLASS_TO_HAZARD.get(class_name)

    if hazard_type is None:
        log.warning(
            f"Unknown class label '{class_name}' — detection skipped. "
            f"Add it to infrastructure/mapper.py to handle it."
        )
        return None

    try:
        bounding_box = BoundingBox.from_xyxy_pixels(
            x1=int(raw["x1"]),
            y1=int(raw["y1"]),
            x2=int(raw["x2"]),
            y2=int(raw["y2"]),
            image_width=int(raw["image_width"]),
            image_height=int(raw["image_height"]),
        )
    except (KeyError, ValueError, ZeroDivisionError) as exc:
        log.warning(f"Bounding box construction failed for '{class_name}': {exc}")
        return None

    return Detection(
        hazard_type=hazard_type,
        confidence=float(raw["confidence"]),
        bounding_box=bounding_box,
        frame_id=frame_id,
        camera_id=camera_id,
        image_path=image_path,
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

    Parameters
    ──────────
    raws            List of adapter dicts.
    frame_id        Frame identifier.
    camera_id       Camera identifier.
    image_path      Optional persisted path.
    min_confidence  Detections below this threshold are dropped.

    Returns
    ───────
    List of domain Detection objects (unknowns and low-confidence dropped).
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
