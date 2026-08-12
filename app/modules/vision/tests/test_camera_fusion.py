"""
test_camera_fusion.py — Multi-Camera Fusion Service Unit Tests.
"""
import pytest
from app.modules.vision.intelligence.camera_fusion_service import MultiCameraFusionService


def test_multi_camera_fusion():
    service = MultiCameraFusionService(spatial_match_distance_m=1.5)

    # Camera 1 detection
    dets1 = [{"track_id": "t-1", "global_x": 10.0, "global_y": 20.0, "confidence": 0.9}]
    tracks1 = service.fuse_camera_detections("CAM-01", "ZONE-A", dets1, timestamp=100.0)
    assert len(tracks1) == 1
    fused_id = tracks1[0].fused_worker_id

    # Overlapping Camera 2 detection of same worker 0.5m away
    dets2 = [{"track_id": "t-2", "global_x": 10.3, "global_y": 20.2, "confidence": 0.95}]
    tracks2 = service.fuse_camera_detections("CAM-02", "ZONE-A", dets2, timestamp=100.1)

    assert len(tracks2) == 1
    assert tracks2[0].fused_worker_id == fused_id
    assert "CAM-01" in tracks2[0].camera_ids
    assert "CAM-02" in tracks2[0].camera_ids
