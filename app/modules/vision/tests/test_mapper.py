"""
tests/test_mapper.py — Unit tests for the infrastructure mapper.
"""

import pytest

from app.modules.vision.domain.enums import HazardType
from app.modules.vision.infrastructure.mapper import map_raw_detection, map_raw_detections


def _make_raw(
    class_name: str = "fire",
    confidence: float = 0.85,
    x1: int = 100,
    y1: int = 100,
    x2: int = 400,
    y2: int = 400,
    w: int = 640,
    h: int = 480,
) -> dict:
    return {
        "class_name":   class_name,
        "confidence":   confidence,
        "x1": x1, "y1": y1, "x2": x2, "y2": y2,
        "image_width":  w,
        "image_height": h,
    }


class TestMapper:

    def test_known_class_maps_correctly(self):
        det = map_raw_detection(_make_raw("fire"), "f1", "CAM-01")
        assert det is not None
        assert det.hazard_type == HazardType.FIRE

    def test_no_helmet_aliases(self):
        for label in ["no-helmet", "no_helmet", "no-hardhat"]:
            det = map_raw_detection(_make_raw(label), "f1", "c1")
            assert det is not None
            assert det.hazard_type == HazardType.NO_HELMET, label

    def test_safety_vest_aliases(self):
        for label in ["vest", "safety-vest", "safety_vest"]:
            det = map_raw_detection(_make_raw(label), "f1", "c1")
            assert det is not None
            assert det.hazard_type == HazardType.SAFETY_VEST, label

    def test_no_safety_vest_aliases(self):
        for label in ["no-vest", "no_vest", "no-safety-vest", "no_safety_vest"]:
            det = map_raw_detection(_make_raw(label), "f1", "c1")
            assert det is not None
            assert det.hazard_type == HazardType.NO_SAFETY_VEST, label

    def test_unknown_class_maps_to_unknown(self):
        """Unknown labels must now map to UNKNOWN, not return None."""
        det = map_raw_detection(_make_raw("dragon"), "f1", "c1")
        assert det is not None
        assert det.hazard_type == HazardType.UNKNOWN

    def test_bounding_box_uses_x_min_y_min_fields(self):
        det = map_raw_detection(
            _make_raw(x1=64, y1=48, x2=640, y2=480, w=640, h=480),
            "f1", "c1",
        )
        assert det is not None
        # Verify field names are x_min / y_min / x_max / y_max
        assert hasattr(det.bounding_box, "x_min")
        assert hasattr(det.bounding_box, "y_min")
        assert hasattr(det.bounding_box, "x_max")
        assert hasattr(det.bounding_box, "y_max")
        assert not hasattr(det.bounding_box, "x1")
        assert det.bounding_box.x_min == pytest.approx(0.1)
        assert det.bounding_box.y_min == pytest.approx(0.1)
        assert det.bounding_box.x_max == pytest.approx(1.0)
        assert det.bounding_box.y_max == pytest.approx(1.0)

    def test_confidence_threshold_filtering(self):
        raws = [
            _make_raw("fire",   confidence=0.9),
            _make_raw("smoke",  confidence=0.3),
            _make_raw("person", confidence=0.6),
        ]
        detections = map_raw_detections(raws, "f1", "c1", min_confidence=0.5)
        assert len(detections) == 2
        types = {d.hazard_type for d in detections}
        assert HazardType.FIRE in types
        assert HazardType.PERSON in types

    def test_all_detections_pass_zero_threshold(self):
        raws = [_make_raw("fire"), _make_raw("smoke"), _make_raw("vest")]
        detections = map_raw_detections(raws, "f1", "c1", min_confidence=0.0)
        assert len(detections) == 3

    def test_detection_default_status_pending(self):
        from app.modules.vision.domain.enums import DetectionStatus
        det = map_raw_detection(_make_raw("fire"), "f1", "c1")
        assert det.status == DetectionStatus.PENDING
