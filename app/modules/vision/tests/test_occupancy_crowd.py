"""
test_occupancy_crowd.py — Occupancy & Crowd Analysis Unit Tests.
"""
import pytest
from app.modules.vision.intelligence.occupancy_engine import OccupancyEngine
from app.modules.vision.intelligence.crowd_analysis import CrowdAnalysisEngine
from app.modules.vision.intelligence.heatmap_engine import HeatmapEngine


def test_occupancy_capacity_excess():
    engine = OccupancyEngine()
    occ = engine.evaluate_occupancy("ZONE-A", detected_worker_count=60, capacity_limit=50)
    assert occ.is_capacity_exceeded is True
    assert occ.is_congested is True


def test_crowd_bottleneck():
    engine = CrowdAnalysisEngine()
    res = engine.analyze_crowd("ZONE-A", worker_count=20, average_velocity=0.2)
    assert res["is_congested"] is True
    assert res["is_bottlenecked"] is True
    assert res["congestion_severity"] == "HIGH"


def test_heatmap_generation():
    engine = HeatmapEngine()
    centroids = [(0.5, 0.5), (0.5, 0.5), (0.1, 0.1)]
    grid = engine.generate_grid_heatmap("ZONE-A", "CAM-01", centroids, 10, 10)
    assert len(grid.cells) == 100
    cell = next(c for c in grid.cells if c.x_cell == 5 and c.y_cell == 5)
    assert cell.detection_count == 2
