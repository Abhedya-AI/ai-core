"""
tests/test_domain.py — Unit tests for the Vision domain layer.

Tests in this file are intentionally framework-free:
  • No FastAPI, no SQLAlchemy, no Kafka.
  • Pure Python — runs with 'pytest' in under a second.
  • Covers enums, value objects, entities, and the risk engine.
"""

import pytest

from app.modules.vision.domain.enums import DetectionStatus, HazardType, RiskLevel
from app.modules.vision.domain.value_objects import BoundingBox, RiskScore
from app.modules.vision.domain.entities import Detection, Hazard, VisionEvent
from app.modules.vision.application.calculate_risk import RiskEngine


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_bbox(
    x_min: float = 0.1,
    y_min: float = 0.1,
    x_max: float = 0.5,
    y_max: float = 0.5,
) -> BoundingBox:
    return BoundingBox(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max)


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

    def test_string_values(self):
        assert RiskLevel.LOW.value == "LOW"
        assert RiskLevel.MEDIUM.value == "MEDIUM"
        assert RiskLevel.HIGH.value == "HIGH"
        assert RiskLevel.CRITICAL.value == "CRITICAL"

    def test_is_str_enum(self):
        """RiskLevel(str, Enum) must serialise directly as a string."""
        assert isinstance(RiskLevel.HIGH, str)
        assert RiskLevel.HIGH == "HIGH"


# ── HazardType ────────────────────────────────────────────────────────────────

class TestHazardType:

    def test_compliance_violation(self):
        assert HazardType.NO_HELMET.is_compliance_violation is True
        assert HazardType.NO_SAFETY_VEST.is_compliance_violation is True
        assert HazardType.FIRE.is_compliance_violation is False
        # old name NO_VEST must not exist
        assert not hasattr(HazardType, "NO_VEST")

    def test_safety_vest_replaces_vest(self):
        assert HazardType.SAFETY_VEST.value == "SAFETY_VEST"
        assert not hasattr(HazardType, "VEST")

    def test_no_safety_vest_replaces_no_vest(self):
        assert HazardType.NO_SAFETY_VEST.value == "NO_SAFETY_VEST"

    def test_unknown_present(self):
        assert HazardType.UNKNOWN.value == "UNKNOWN"

    def test_environmental(self):
        assert HazardType.FIRE.is_environmental is True
        assert HazardType.SMOKE.is_environmental is True
        assert HazardType.PERSON.is_environmental is False

    def test_incident(self):
        assert HazardType.FALL.is_incident is True
        assert HazardType.HELMET.is_incident is False

    def test_compliant_presence(self):
        assert HazardType.HELMET.is_compliant_presence is True
        assert HazardType.SAFETY_VEST.is_compliant_presence is True
        assert HazardType.NO_HELMET.is_compliant_presence is False

    def test_is_str_enum(self):
        assert isinstance(HazardType.FIRE, str)
        assert HazardType.FIRE == "FIRE"


# ── DetectionStatus ───────────────────────────────────────────────────────────

class TestDetectionStatus:

    def test_values(self):
        assert DetectionStatus.PENDING.value == "PENDING"
        assert DetectionStatus.VERIFIED.value == "VERIFIED"
        assert DetectionStatus.REJECTED.value == "REJECTED"
        assert DetectionStatus.ARCHIVED.value == "ARCHIVED"

    def test_is_active(self):
        assert DetectionStatus.PENDING.is_active is True
        assert DetectionStatus.VERIFIED.is_active is True
        assert DetectionStatus.REJECTED.is_active is False
        assert DetectionStatus.ARCHIVED.is_active is False

    def test_is_terminal(self):
        assert DetectionStatus.REJECTED.is_terminal is True
        assert DetectionStatus.ARCHIVED.is_terminal is True
        assert DetectionStatus.PENDING.is_terminal is False

    def test_is_str_enum(self):
        assert isinstance(DetectionStatus.PENDING, str)


# ── BoundingBox ───────────────────────────────────────────────────────────────

class TestBoundingBox:

    def test_valid_construction(self):
        bb = BoundingBox(x_min=0.0, y_min=0.0, x_max=1.0, y_max=1.0)
        assert bb.width == pytest.approx(1.0)
        assert bb.height == pytest.approx(1.0)
        assert bb.area == pytest.approx(1.0)

    def test_area_calculation(self):
        bb = BoundingBox(x_min=0.25, y_min=0.25, x_max=0.75, y_max=0.75)
        assert bb.area == pytest.approx(0.25)

    def test_center(self):
        bb = BoundingBox(x_min=0.0, y_min=0.0, x_max=1.0, y_max=1.0)
        assert bb.center == pytest.approx((0.5, 0.5))

    def test_invalid_out_of_range(self):
        with pytest.raises(Exception, match="less than or equal to 1"):
            BoundingBox(x_min=-0.1, y_min=0.0, x_max=0.5, y_max=0.5)

    def test_invalid_x_min_ge_x_max(self):
        with pytest.raises(Exception, match="x_min must be less than x_max"):
            BoundingBox(x_min=0.6, y_min=0.0, x_max=0.5, y_max=0.5)

    def test_invalid_y_min_ge_y_max(self):
        with pytest.raises(Exception, match="y_min must be less than y_max"):
            BoundingBox(x_min=0.1, y_min=0.8, x_max=0.5, y_max=0.5)

    def test_frozen(self):
        """Pydantic frozen model must reject attribute assignment."""
        bb = _make_bbox()
        with pytest.raises(Exception):
            bb.x_min = 0.0

    def test_to_pixel(self):
        bb = BoundingBox(x_min=0.1, y_min=0.2, x_max=0.9, y_max=0.8)
        px = bb.to_pixel(image_width=1000, image_height=500)
        assert px == (100, 100, 900, 400)

    def test_from_xyxy_pixels(self):
        bb = BoundingBox.from_xyxy_pixels(
            x_min=100, y_min=100, x_max=900, y_max=400,
            image_width=1000, image_height=500,
        )
        assert bb.x_min == pytest.approx(0.1)
        assert bb.y_max == pytest.approx(0.8)

    def test_roundtrip_dict(self):
        bb = _make_bbox()
        assert BoundingBox.from_dict(bb.as_dict()) == bb

    def test_as_dict_keys(self):
        bb = _make_bbox()
        d = bb.as_dict()
        assert set(d.keys()) == {"x_min", "y_min", "x_max", "y_max"}


# ── RiskScore ─────────────────────────────────────────────────────────────────

class TestRiskScore:

    def test_valid(self):
        rs = RiskScore(score=0.5, level=RiskLevel.MEDIUM)
        assert rs.score == 0.5
        assert rs.is_critical is False

    def test_percentage(self):
        rs = RiskScore(score=0.873, level=RiskLevel.HIGH)
        assert rs.percentage == pytest.approx(87.3)

    def test_is_critical_at_critical(self):
        rs = RiskScore(score=1.0, level=RiskLevel.CRITICAL)
        assert rs.is_critical is True

    def test_is_critical_false_for_high(self):
        rs = RiskScore(score=0.75, level=RiskLevel.HIGH)
        assert rs.is_critical is False

    def test_invalid_score_above_one(self):
        with pytest.raises(Exception):
            RiskScore(score=1.5, level=RiskLevel.CRITICAL)

    def test_invalid_score_below_zero(self):
        with pytest.raises(Exception):
            RiskScore(score=-0.1, level=RiskLevel.LOW)

    def test_reason_field(self):
        rs = RiskScore(score=0.8, level=RiskLevel.CRITICAL, reason="Fire detected.")
        assert rs.reason == "Fire detected."

    def test_reason_default_empty(self):
        rs = RiskScore(score=0.1, level=RiskLevel.LOW)
        assert rs.reason == ""

    def test_frozen(self):
        rs = RiskScore(score=0.5, level=RiskLevel.MEDIUM)
        with pytest.raises(Exception):
            rs.score = 0.9

    def test_no_value_field(self):
        """Confirm old 'value' field does not exist."""
        rs = RiskScore(score=0.5, level=RiskLevel.MEDIUM)
        assert not hasattr(rs, "value")


# ── Detection ─────────────────────────────────────────────────────────────────

class TestDetection:

    def test_default_status_is_pending(self):
        det = _make_detection()
        assert det.status == DetectionStatus.PENDING
        assert det.is_pending is True

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

    def test_verify_returns_new_detection(self):
        det = _make_detection()
        verified = det.verify()
        assert verified.status == DetectionStatus.VERIFIED
        assert det.status == DetectionStatus.PENDING  # original unchanged

    def test_reject_returns_new_detection(self):
        det = _make_detection()
        rejected = det.reject()
        assert rejected.status == DetectionStatus.REJECTED

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
        assert score.score == 0.0
        assert score.level == RiskLevel.LOW
        assert hazards == []
        assert score.reason != ""

    def test_single_fire_detection(self):
        det = _make_detection(hazard_type=HazardType.FIRE, confidence=0.95)
        score, hazards = self.engine.calculate([det])
        assert score.score == pytest.approx(0.9 * 0.95, rel=1e-3)
        assert score.level == RiskLevel.CRITICAL
        assert len(hazards) == 1
        assert hazards[0].hazard_type == HazardType.FIRE

    def test_helmet_no_risk(self):
        det = _make_detection(hazard_type=HazardType.HELMET, confidence=0.99)
        score, _ = self.engine.calculate([det])
        assert score.score == 0.0
        assert score.level == RiskLevel.LOW

    def test_safety_vest_no_risk(self):
        det = _make_detection(hazard_type=HazardType.SAFETY_VEST, confidence=0.99)
        score, _ = self.engine.calculate([det])
        assert score.score == 0.0

    def test_no_safety_vest_medium_risk(self):
        det = _make_detection(hazard_type=HazardType.NO_SAFETY_VEST, confidence=0.7)
        score, _ = self.engine.calculate([det])
        # 0.45 * 0.7 = 0.315 → MEDIUM
        assert score.level == RiskLevel.MEDIUM

    def test_score_capped_at_one(self):
        detections = [
            _make_detection(HazardType.FIRE, 1.0),
            _make_detection(HazardType.CHEMICAL_SPILL, 1.0),
            _make_detection(HazardType.FALL, 1.0),
        ]
        score, _ = self.engine.calculate(detections)
        assert score.score <= 1.0

    def test_no_helmet_medium_risk(self):
        det = _make_detection(hazard_type=HazardType.NO_HELMET, confidence=0.6)
        score, _ = self.engine.calculate([det])
        # 0.55 * 0.6 = 0.33 → MEDIUM
        assert score.level == RiskLevel.MEDIUM

    def test_reason_populated(self):
        det = _make_detection(hazard_type=HazardType.FIRE, confidence=0.9)
        score, _ = self.engine.calculate([det])
        assert score.reason != ""
        assert "FIRE" in score.reason

    def test_no_old_contributing_hazards_field(self):
        det = _make_detection(hazard_type=HazardType.FIRE, confidence=0.9)
        score, _ = self.engine.calculate([det])
        assert not hasattr(score, "contributing_hazards")


# ── VisionEvent ───────────────────────────────────────────────────────────────

class TestVisionEvent:

    def _make_event(self, risk_level: RiskLevel = RiskLevel.LOW) -> VisionEvent:
        rs = RiskScore(
            score=0.1 if risk_level == RiskLevel.LOW else 1.0,
            level=risk_level,
        )
        return VisionEvent(
            camera_id="CAM-01",
            frame_id="frame-001",
            detections=[],
            hazards=[],
            risk_score=rs,
        )

    def test_summary_uses_score(self):
        event = self._make_event()
        summary = event.summary()
        assert "CAM-01" in summary
        assert "LOW" in summary
        assert "0.10" in summary

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
