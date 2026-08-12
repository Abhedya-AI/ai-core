"""
domain/entities/detection_class.py — DetectionClass domain value object.

Maps raw model output class labels to domain HazardType enum values.
The DETECTION_CLASS_REGISTRY is the single source of truth for label
resolution across all detector backends. Use resolve_detection_class()
to safely convert any raw string into a typed DetectionClass.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.modules.vision.domain.enums.hazard_type import HazardType


class DetectionClass(BaseModel):
    """Maps a raw model class label to a domain HazardType."""

    model_config = ConfigDict(frozen=True)

    raw_label: str
    hazard_type: HazardType
    display_label: str
    risk_weight: float = Field(ge=0.0, le=1.0)
    is_violation: bool
    color_hex: str


# ── Registry ──────────────────────────────────────────────────────────────────

DETECTION_CLASS_REGISTRY: dict[str, DetectionClass] = {
    "person": DetectionClass(
        raw_label="person", hazard_type=HazardType.PERSON,
        display_label="Person Detected", risk_weight=0.3,
        is_violation=False, color_hex="#4A90D9",
    ),
    "worker": DetectionClass(
        raw_label="worker", hazard_type=HazardType.WORKER,
        display_label="Worker Detected", risk_weight=0.2,
        is_violation=False, color_hex="#4A90D9",
    ),
    "helmet": DetectionClass(
        raw_label="helmet", hazard_type=HazardType.HELMET,
        display_label="Helmet Detected", risk_weight=0.1,
        is_violation=False, color_hex="#27AE60",
    ),
    "hard-hat": DetectionClass(
        raw_label="hard-hat", hazard_type=HazardType.HELMET,
        display_label="Helmet Detected", risk_weight=0.1,
        is_violation=False, color_hex="#27AE60",
    ),
    "no-helmet": DetectionClass(
        raw_label="no-helmet", hazard_type=HazardType.NO_HELMET,
        display_label="No Helmet — PPE Violation", risk_weight=0.9,
        is_violation=True, color_hex="#E74C3C",
    ),
    "no-hard-hat": DetectionClass(
        raw_label="no-hard-hat", hazard_type=HazardType.NO_HELMET,
        display_label="No Helmet — PPE Violation", risk_weight=0.9,
        is_violation=True, color_hex="#E74C3C",
    ),
    "safety-vest": DetectionClass(
        raw_label="safety-vest", hazard_type=HazardType.SAFETY_VEST,
        display_label="Safety Vest Detected", risk_weight=0.1,
        is_violation=False, color_hex="#27AE60",
    ),
    "vest": DetectionClass(
        raw_label="vest", hazard_type=HazardType.SAFETY_VEST,
        display_label="Safety Vest Detected", risk_weight=0.1,
        is_violation=False, color_hex="#27AE60",
    ),
    "no-safety-vest": DetectionClass(
        raw_label="no-safety-vest", hazard_type=HazardType.NO_SAFETY_VEST,
        display_label="No Safety Vest — PPE Violation", risk_weight=0.85,
        is_violation=True, color_hex="#E74C3C",
    ),
    "no-vest": DetectionClass(
        raw_label="no-vest", hazard_type=HazardType.NO_SAFETY_VEST,
        display_label="No Safety Vest — PPE Violation", risk_weight=0.85,
        is_violation=True, color_hex="#E74C3C",
    ),
    "mask": DetectionClass(
        raw_label="mask", hazard_type=HazardType.MASK,
        display_label="Mask Detected", risk_weight=0.1,
        is_violation=False, color_hex="#27AE60",
    ),
    "no-mask": DetectionClass(
        raw_label="no-mask", hazard_type=HazardType.NO_MASK,
        display_label="No Mask — PPE Violation", risk_weight=0.75,
        is_violation=True, color_hex="#E74C3C",
    ),
    "gloves": DetectionClass(
        raw_label="gloves", hazard_type=HazardType.GLOVES,
        display_label="Gloves Detected", risk_weight=0.1,
        is_violation=False, color_hex="#27AE60",
    ),
    "no-gloves": DetectionClass(
        raw_label="no-gloves", hazard_type=HazardType.NO_GLOVES,
        display_label="No Gloves — PPE Violation", risk_weight=0.7,
        is_violation=True, color_hex="#E74C3C",
    ),
    "goggles": DetectionClass(
        raw_label="goggles", hazard_type=HazardType.GOGGLES,
        display_label="Goggles Detected", risk_weight=0.1,
        is_violation=False, color_hex="#27AE60",
    ),
    "safety-glasses": DetectionClass(
        raw_label="safety-glasses", hazard_type=HazardType.GOGGLES,
        display_label="Goggles Detected", risk_weight=0.1,
        is_violation=False, color_hex="#27AE60",
    ),
    "no-goggles": DetectionClass(
        raw_label="no-goggles", hazard_type=HazardType.NO_GOGGLES,
        display_label="No Goggles — PPE Violation", risk_weight=0.7,
        is_violation=True, color_hex="#E74C3C",
    ),
    "forklift": DetectionClass(
        raw_label="forklift", hazard_type=HazardType.FORKLIFT,
        display_label="Forklift Detected", risk_weight=0.5,
        is_violation=False, color_hex="#F39C12",
    ),
    "crane": DetectionClass(
        raw_label="crane", hazard_type=HazardType.CRANE,
        display_label="Crane Detected", risk_weight=0.5,
        is_violation=False, color_hex="#F39C12",
    ),
    "truck": DetectionClass(
        raw_label="truck", hazard_type=HazardType.TRUCK,
        display_label="Truck Detected", risk_weight=0.4,
        is_violation=False, color_hex="#F39C12",
    ),
    "fire": DetectionClass(
        raw_label="fire", hazard_type=HazardType.FIRE,
        display_label="Fire Detected — CRITICAL", risk_weight=1.0,
        is_violation=True, color_hex="#FF0000",
    ),
    "flame": DetectionClass(
        raw_label="flame", hazard_type=HazardType.FIRE,
        display_label="Fire Detected — CRITICAL", risk_weight=1.0,
        is_violation=True, color_hex="#FF0000",
    ),
    "smoke": DetectionClass(
        raw_label="smoke", hazard_type=HazardType.SMOKE,
        display_label="Smoke Detected", risk_weight=0.9,
        is_violation=True, color_hex="#FF6600",
    ),
    "chemical-spill": DetectionClass(
        raw_label="chemical-spill", hazard_type=HazardType.CHEMICAL_SPILL,
        display_label="Chemical Spill Detected", risk_weight=0.95,
        is_violation=True, color_hex="#9B59B6",
    ),
    "spill": DetectionClass(
        raw_label="spill", hazard_type=HazardType.CHEMICAL_SPILL,
        display_label="Chemical Spill Detected", risk_weight=0.95,
        is_violation=True, color_hex="#9B59B6",
    ),
    "fall": DetectionClass(
        raw_label="fall", hazard_type=HazardType.FALL,
        display_label="Person Fall — CRITICAL", risk_weight=1.0,
        is_violation=True, color_hex="#FF0000",
    ),
    "fallen-person": DetectionClass(
        raw_label="fallen-person", hazard_type=HazardType.FALL,
        display_label="Person Fall — CRITICAL", risk_weight=1.0,
        is_violation=True, color_hex="#FF0000",
    ),
}

_UNKNOWN_CLASS = DetectionClass(
    raw_label="unknown",
    hazard_type=HazardType.UNKNOWN,
    display_label="Unknown Object",
    risk_weight=0.3,
    is_violation=False,
    color_hex="#95A5A6",
)


def resolve_detection_class(raw_label: str) -> DetectionClass:
    """Resolve a raw model label to a DetectionClass.

    Performs a case-insensitive, stripped lookup against the registry.
    Returns the UNKNOWN DetectionClass when the label is not found rather
    than raising an exception, allowing the pipeline to continue gracefully.
    """
    return DETECTION_CLASS_REGISTRY.get(raw_label.lower().strip(), _UNKNOWN_CLASS)
