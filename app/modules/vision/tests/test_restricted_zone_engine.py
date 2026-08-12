"""
test_restricted_zone_engine.py — Restricted Zone Engine Unit Tests.
"""
import pytest
from app.modules.vision.intelligence.restricted_zone_engine import RestrictedZoneEngine


def test_polygon_raycasting():
    polygon = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    assert RestrictedZoneEngine.is_point_in_polygon(5.0, 5.0, polygon) is True
    assert RestrictedZoneEngine.is_point_in_polygon(15.0, 5.0, polygon) is False


def test_unauthorized_entry():
    engine = RestrictedZoneEngine()
    polygon = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    is_inside, status, viol = engine.evaluate_zone_access(
        worker_id="w-1",
        worker_role="OPERATOR",
        camera_id="CAM-01",
        zone_id="ZONE-HAZARD",
        worker_x=5.0,
        worker_y=5.0,
        zone_polygon=polygon,
        allowed_roles=["ENGINEER"],
    )
    assert is_inside is True
    assert status == "UNAUTHORIZED_ENTRY"
    assert viol is not None
    assert viol.severity == "CRITICAL"
