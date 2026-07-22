"""
tests/test_domain.py — Unit tests for the Vision domain layer.

Tests in this file are intentionally framework-free:
  • No FastAPI, no SQLAlchemy, no Kafka.
  • Pure Python — runs with 'pytest' in under a second.
  • Covers enums, value objects, entities, and the risk engine.
"""

import pytest

from app.modules.vision.domain.enums import HazardType, RiskLevel
from app.modules.vision.domain.value_objects import BoundingBox, RiskScore
from app.modules.vision.domain.entities import Detection, Hazard, VisionEvent
from app.modules.vision.application.calculate_risk import RiskEngine


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_bbox(x1=0.1, y1=0.1, x2=0.5, y2=0.5) -> BoundingBox:
    return BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)


def _make_detection(
    hazard_type: HazardType = HazardType.NO_HELMET,
    confidence: float = 0.85,
) -> Detection:
    return Detection(
        hazard_type=hazard_type,
        confidence=confidence,
        bounding_box=_make_bbox(),
        frame_id="frame-001",
        camera_id="CAM-01",
    )


# ── RiskLevel ─────────────────────────────────────────────────────────────────

class TestRiskLevel:

    def test_ordering(self):
        assert RiskLevel.LOW < RiskLevel.MEDIUM
        assert RiskLevel.MEDIUM < RiskLevel.HIGH
        assert RiskLevel.HIGH < RiskLevel.CRITICAL
        assert RiskLevel.CRITICAL >= RiskLevel.HIGH

    def test_numeric_values(self):
        assert RiskLevel.LOW.numeric == 1
        assert RiskLevel.CRITICAL.numeric == 4

    def test_string_values(self):
        assert RiskLevel.HIGH.value == "HIGH"


# ── HazardType ────────────────────────────────────────────────────────────────

class TestHazardType:

    def test_compliance_violation(self):
        assert HazardType.NO_HELMET.is_compliance_violation is True
        assert HazardType.NO_VEST.is_compliance_violation is True
        assert HazardType.FIRE.is_compliance_violation is False

    def test_environmental(self):
        assert HazardType.FIRE.is_environmental is True
        assert HazardType.SMOKE.is_environmental is True
        assert HazardType.PERSON.is_environmental is False

    def test_incident(self):
        assert HazardType.FALL.is_incident is True
        assert HazardType.HELMET.is_incident is False


# ── BoundingBox ───────────────────────────────────────────────────────────────

class TestBoundingBox:

    def test_valid_construction(self):
        bb = BoundingBox(x1=0.0, y1=0.0, x2=1.0, y2=1.0)
        assert bb.width == pytest.approx(1.0)
        assert bb.height == pytest.approx(1.0)
        assert bb.area == pytest.approx(1.0)

    def test_area_calculation(self):
        bb = BoundingBox(x1=0.25, y1=0.25, x2=0.75, y2=0.75)
        assert bb.area == pytest.approx(0.25)

    def test_center(self):
        bb = BoundingBox(x1=0.0, y1=0.0, x2=1.0, y2=1.0)
        assert bb.center == pytest.approx((0.5, 0.5))

    def test_invalid_out_of_range(self):
        with pytest.raises(ValueError, match="must be in"):
            BoundingBox(x1=-0.1, y1=0.0, x2=0.5, y2=0.5)

    def test_invalid_x1_ge_x2(self):
        with pytest.raises(ValueError, match="x1"):
            BoundingBox(x1=0.6, y1=0.0, x2=0.5, y2=0.5)

    def test_frozen(self):
        bb = _make_bbox()
        with pytest.raises(Exception):
            bb.x1 = 0.0  # frozen dataclass

    def test_to_pixel(self):
        bb = BoundingBox(x1=0.1, y1=0.2, x2=0.9, y2=0.8)
        px = bb.to_pixel(image_width=1000, image_height=500)
        assert px == (100, 100, 900, 400)

    def test_from_xyxy_pixels(self):
        bb = BoundingBox.from_xyxy_pixels(
            x1=100, y1=100, x2=900, y2=400,
            image_width=1000, image_height=500,
        )
        assert bb.x1 == pytest.approx(0.1)
        assert bb.y2 == pytest.approx(0.8)

    def test_roundtrip_dict(self):
        bb = _make_bbox()
        assert BoundingBox.from_dict(bb.as_dict()) == bb


# ── RiskScore ─────────────────────────────────────────────────────────────────

class TestRiskScore:

    def test_valid(self):
        rs = RiskScore(value=0.5, level=RiskLevel.MEDIUM)
        assert rs.value == 0.5
        assert rs.is_actionable is False

    def test_actionable_at_high(self):
        rs = RiskScore(value=0.75, level=RiskLevel.HIGH)
        assert rs.is_actionable is True

    def test_actionable_at_critical(self):
        rs = RiskScore(value=1.0, level=RiskLevel.CRITICAL)
        assert rs.is_actionable is True

    def test_invalid_value(self):
        with pytest.raises(ValueError, match="must be in"):
            RiskScore(value=1.5, level=RiskLevel.CRITICAL)

    def test_as_dict(self):
        rs = RiskScore(
            value=0.8,
            level=RiskLevel.CRITICAL,
            contributing_hazards=((HazardType.FIRE, 0.72),),
        )
        d = rs.as_dict()
        assert d["level"] == "CRITICAL"
        assert len(d["contributing_hazards"]) == 1


# ── Detection ─────────────────────────────────────────────────────────────────

class TestDetection:

    def test_high_confidence(self):
        det = _make_detection(confidence=0.9)
        assert det.is_high_confidence is True

    def test_low_confidence(self):
        det = _make_detection(confidence=0.5)
        assert det.is_high_confidence is False

    def test_critical_hazard(self):
        det = _make_detection(hazard_type=HazardType.FIRE)
        assert det.is_critical_hazard is True

    def test_non_critical_hazard(self):
        det = _make_detection(hazard_type=HazardType.PERSON)
        assert det.is_critical_hazard is False

    def test_invalid_confidence(self):
        with pytest.raises(ValueError):
            Detection(
                hazard_type=HazardType.FIRE,
                confidence=1.5,
                bounding_box=_make_bbox(),
                frame_id="f",
                camera_id="c",
            )


# ── RiskEngine ────────────────────────────────────────────────────────────────

class TestRiskEngine:

    def setup_method(self):
        self.engine = RiskEngine()

    def test_empty_detections(self):
        score, hazards = self.engine.calculate([])
        assert score.value == 0.0
        assert score.level == RiskLevel.LOW
        assert hazards == []

    def test_single_fire_detection(self):
        det = _make_detection(hazard_type=HazardType.FIRE, confidence=0.95)
        score, hazards = self.engine.calculate([det])
        assert score.value == pytest.approx(0.9 * 0.95, rel=1e-3)
        assert score.level == RiskLevel.CRITICAL
        assert len(hazards) == 1
        assert hazards[0].hazard_type == HazardType.FIRE

    def test_helmet_no_risk(self):
        det = _make_detection(hazard_type=HazardType.HELMET, confidence=0.99)
        score, _ = self.engine.calculate([det])
        assert score.value == 0.0
        assert score.level == RiskLevel.LOW

    def test_score_capped_at_one(self):
        detections = [
            _make_detection(HazardType.FIRE, 1.0),
            _make_detection(HazardType.CHEMICAL_SPILL, 1.0),
            _make_detection(HazardType.FALL, 1.0),
        ]
        score, _ = self.engine.calculate(detections)
        assert score.value <= 1.0

    def test_no_helmet_medium_risk(self):
        det = _make_detection(hazard_type=HazardType.NO_HELMET, confidence=0.6)
        score, _ = self.engine.calculate([det])
        # 0.55 * 0.6 = 0.33 → MEDIUM
        assert score.level == RiskLevel.MEDIUM

    def test_contributing_hazards_sorted(self):
        detections = [
            _make_detection(HazardType.PERSON, 0.9),   # weight 0.10 * 0.9 = 0.09
            _make_detection(HazardType.FIRE, 0.8),     # weight 0.90 * 0.8 = 0.72
        ]
        score, _ = self.engine.calculate(detections)
        # Highest contribution should be first
        first_hazard, first_weight = score.contributing_hazards[0]
        assert first_hazard == HazardType.FIRE
        assert first_weight > 0.5


# ── VisionEvent ───────────────────────────────────────────────────────────────

class TestVisionEvent:

    def _make_event(self, risk_level: RiskLevel = RiskLevel.LOW) -> VisionEvent:
        rs = RiskScore(value=0.1 if risk_level == RiskLevel.LOW else 0.9, level=risk_level)
        return VisionEvent(
            camera_id="CAM-01",
            frame_id="frame-001",
            detections=[],
            hazards=[],
            risk_score=rs,
        )

    def test_summary_format(self):
        event = self._make_event()
        summary = event.summary()
        assert "CAM-01" in summary
        assert "LOW" in summary

    def test_is_critical(self):
        event = self._make_event(RiskLevel.CRITICAL)
        assert event.is_critical is True

    def test_not_critical(self):
        event = self._make_event(RiskLevel.HIGH)
        assert event.is_critical is False

    def test_unique_hazard_types(self):
        engine = RiskEngine()
        detections = [
            _make_detection(HazardType.FIRE, 0.9),
            _make_detection(HazardType.FIRE, 0.85),
            _make_detection(HazardType.NO_HELMET, 0.7),
        ]
        score, hazards = engine.calculate(detections)
        event = VisionEvent(
            camera_id="CAM-01",
            frame_id="f-1",
            detections=detections,
            hazards=hazards,
            risk_score=score,
        )
        assert HazardType.FIRE in event.unique_hazard_types
        assert HazardType.NO_HELMET in event.unique_hazard_types
