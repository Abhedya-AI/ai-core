"""
test_worker_equipment_engine.py — Worker Equipment Proximity Unit Tests.
"""
import pytest
from app.modules.vision.intelligence.worker_equipment_engine import WorkerEquipmentEngine


def test_unsafe_forklift_proximity():
    engine = WorkerEquipmentEngine()
    interaction = engine.evaluate_interaction(
        worker_id="w-1",
        equipment_id="forklift-01",
        equipment_type="FORKLIFT",
        worker_pos=(10.0, 10.0),
        equipment_pos=(10.0, 20.0),  # 10px * 0.05 = 0.5m
        camera_id="CAM-01",
        zone_id="ZONE-A",
    )
    assert interaction.distance_meters == 0.5
    assert interaction.is_unsafe_proximity is True
    assert interaction.interaction_type == "WORKER_NEAR_FORKLIFT"
