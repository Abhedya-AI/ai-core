"""
tests/test_vision_intelligence.py — Comprehensive Vision Intelligence Test Suite.

Tests for:
  - Camera, CameraGroup, CameraHealth, VideoStream, Frame, FrameMetadata entities
  - HazardType, CameraType, CameraStatus, StreamEventType enums
  - DetectionClass registry & resolution
  - CameraZone polygon ray-casting containment
  - TrackingObject, ZoneCrossing, TrackingHistory
  - DetectionEvent, VisionAlert, VisionIncident
  - In-memory repositories (Camera, Frame, Tracking, Alert)
  - FastAPI routers (/cameras, /video-streams, /detections, /tracking, /frame-history, /camera-health, /vision-alerts)
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Domain imports
from app.modules.vision.domain.entities.camera import Camera
from app.modules.vision.domain.entities.camera_group import CameraGroup
from app.modules.vision.domain.entities.camera_health import CameraHealth
from app.modules.vision.domain.entities.camera_zone import CameraZone
from app.modules.vision.domain.entities.detection_class import (
    DETECTION_CLASS_REGISTRY,
    DetectionClass,
    resolve_detection_class,
)
from app.modules.vision.domain.entities.detection_event import AlertSeverity, DetectionEvent
from app.modules.vision.domain.entities.frame import Frame, FrameFormat
from app.modules.vision.domain.entities.frame_metadata import FrameMetadata
from app.modules.vision.domain.entities.tracking_history import TrackingHistory
from app.modules.vision.domain.entities.tracking_object import TrackingObject, ZoneCrossing
from app.modules.vision.domain.entities.video_stream import StreamProtocol, StreamStatus, VideoStream
from app.modules.vision.domain.entities.vision_alert import AlertStatus, VisionAlert
from app.modules.vision.domain.entities.vision_incident import VisionIncident
from app.modules.vision.domain.enums.camera_status import CameraStatus
from app.modules.vision.domain.enums.camera_type import CameraType
from app.modules.vision.domain.enums.hazard_type import HazardType
from app.modules.vision.domain.enums.stream_event_type import StreamEventType

# Infrastructure imports
from app.modules.vision.infrastructure.repositories.in_memory_alert_repository import InMemoryAlertRepository
from app.modules.vision.infrastructure.repositories.in_memory_camera_repository import InMemoryCameraRepository
from app.modules.vision.infrastructure.repositories.in_memory_frame_repository import InMemoryFrameRepository
from app.modules.vision.infrastructure.repositories.in_memory_tracking_repository import InMemoryTrackingRepository

# Router imports
from app.api.v1.vision_alerts import router as alerts_router
from app.api.v1.vision_cameras import router as cameras_router
from app.api.v1.vision_detections import router as detections_router
from app.api.v1.vision_frame_history import router as frame_history_router
from app.api.v1.vision_streams import router as streams_router
from app.api.v1.vision_tracking import router as tracking_router


# ==============================================================================
# Domain Unit Tests
# ==============================================================================

class TestCameraEntity:
    def test_camera_defaults(self):
        cam = Camera(name="Cam 1", location="Zone A")
        assert cam.name == "Cam 1"
        assert cam.health_status == CameraStatus.OFFLINE
        assert cam.is_active is True
        assert cam.is_online is False

    def test_camera_state_transitions(self):
        cam = Camera(name="Cam 1", location="Zone A")
        online = cam.mark_online()
        assert online.health_status == CameraStatus.ONLINE
        assert online.is_online is True

        degraded = online.mark_degraded()
        assert degraded.health_status == CameraStatus.DEGRADED

        reconnecting = degraded.mark_reconnecting()
        assert reconnecting.health_status == CameraStatus.RECONNECTING

        offline = reconnecting.mark_offline()
        assert offline.health_status == CameraStatus.OFFLINE

    def test_camera_recording_and_last_seen(self):
        cam = Camera(name="Cam 1", location="Zone A")
        rec = cam.set_recording(True)
        assert rec.is_recording is True

        seen = rec.update_last_seen()
        assert seen.last_seen_at is not None

    def test_camera_properties(self):
        cam = Camera(name="RTSP Cam", camera_type=CameraType.RTSP, location="Zone A")
        assert cam.is_rtsp is True
        assert f"{cam.id}:RTSP" in cam.stream_key


class TestCameraGroupEntity:
    def test_camera_group_add_remove(self):
        group = CameraGroup(name="Building 1")
        assert group.camera_count == 0

        g1 = group.add_camera("cam-1")
        assert g1.camera_count == 1

        g2 = g1.add_camera("cam-1")  # duplicate check
        assert g2.camera_count == 1

        g3 = g2.add_camera("cam-2")
        assert g3.camera_count == 2

        g4 = g3.remove_camera("cam-1")
        assert g4.camera_count == 1
        assert "cam-1" not in g4.camera_ids


class TestCameraHealthEntity:
    def test_camera_health_is_healthy(self):
        h = CameraHealth(camera_id="cam-1", status=CameraStatus.ONLINE, frame_drop_rate=0.05, fps_actual=5.0, fps_configured=5)
        assert h.is_healthy is True
        assert h.fps_efficiency == 1.0
        assert h.uptime_hours == 0.0

    def test_camera_health_unhealthy_on_high_drop(self):
        h = CameraHealth(camera_id="cam-1", status=CameraStatus.ONLINE, frame_drop_rate=0.25)
        assert h.is_healthy is False


class TestVideoStreamEntity:
    def test_video_stream_lifecycle(self):
        stream = VideoStream(camera_id="cam-1", protocol=StreamProtocol.RTSP)
        assert stream.is_active is True
        assert stream.status == StreamStatus.INITIALIZING

        s1 = stream.start_streaming()
        assert s1.status == StreamStatus.STREAMING

        s2 = s1.increment_frame(dropped=True)
        assert s2.frame_count == 1
        assert s2.dropped_frames == 1
        assert s2.drop_rate == 1.0

        s3 = s2.pause()
        assert s3.status == StreamStatus.PAUSED

        s4 = s3.stop()
        assert s4.status == StreamStatus.STOPPED
        assert s4.stopped_at is not None


class TestFrameEntity:
    def test_frame_properties(self):
        f = Frame(camera_id="cam-1", sequence_number=10, width=1920, height=1080, size_bytes=250000)
        assert f.resolution == "1920x1080"
        assert f.megapixels == 2.074
        assert f.has_storage is False

    def test_frame_metadata(self):
        fm = FrameMetadata(frame_id="f-1", camera_id="c-1", blur_score=150.0, detection_count=3)
        assert fm.is_sharp is True
        assert fm.has_detections is True


class TestHazardTypeEnum:
    def test_hazard_type_properties(self):
        assert HazardType.NO_HELMET.is_compliance_violation is True
        assert HazardType.NO_SAFETY_VEST.is_compliance_violation is True
        assert HazardType.NO_MASK.is_compliance_violation is True

        assert HazardType.FIRE.is_environmental is True
        assert HazardType.SMOKE.is_environmental is True

        assert HazardType.FALL.is_incident is True

        assert HazardType.FORKLIFT.is_equipment is True
        assert HazardType.CRANE.is_equipment is True
        assert HazardType.TRUCK.is_equipment is True

        assert HazardType.HELMET.is_compliant_presence is True


class TestDetectionClassRegistry:
    def test_resolve_labels(self):
        dc_person = resolve_detection_class("person")
        assert dc_person.hazard_type == HazardType.PERSON
        assert dc_person.is_violation is False

        dc_no_helmet = resolve_detection_class("no-helmet")
        assert dc_no_helmet.hazard_type == HazardType.NO_HELMET
        assert dc_no_helmet.is_violation is True

        dc_fire = resolve_detection_class("fire")
        assert dc_fire.hazard_type == HazardType.FIRE

        dc_unknown = resolve_detection_class("unregistered_label_123")
        assert dc_unknown.hazard_type == HazardType.UNKNOWN


class TestCameraZonePolygon:
    def test_camera_zone_contains_point(self):
        square_zone = CameraZone(
            zone_id="z-1",
            camera_id="c-1",
            zone_name="Restricted Area",
            polygon_points=[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)],
            is_restricted=True,
        )
        assert square_zone.contains_point(5.0, 5.0) is True
        assert square_zone.contains_point(15.0, 5.0) is False

    def test_bbox_centroid_in_zone(self):
        zone = CameraZone(
            zone_id="z-1",
            camera_id="c-1",
            zone_name="Work Cell",
            polygon_points=[(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)],
        )
        bbox_inside = {"x_min": 10.0, "y_min": 10.0, "x_max": 20.0, "y_max": 20.0}
        bbox_outside = {"x_min": 150.0, "y_min": 150.0, "x_max": 200.0, "y_max": 200.0}

        assert zone.bbox_centroid_in_zone(bbox_inside) is True
        assert zone.bbox_centroid_in_zone(bbox_outside) is False


class TestTrackingObjectEntity:
    def test_tracking_object_updates(self):
        t = TrackingObject(camera_id="c-1", object_class="PERSON", confidence=0.92)
        assert t.is_person is True
        assert t.duration_seconds >= 0.0

        crossing = ZoneCrossing(zone_id="z-1", zone_name="Danger Zone", direction="ENTERED")
        t_crossed = t.add_zone_crossing(crossing)
        assert t_crossed.crossed_restricted_zone is True

        t_deactive = t_crossed.deactivate()
        assert t_deactive.is_active is False
        assert t_deactive.exit_zone == "z-1"


class TestVisionAlertEntity:
    def test_alert_lifecycle(self):
        alert = VisionAlert(camera_id="c-1", alert_type="PPEViolation", severity=AlertSeverity.HIGH, description="No helmet detected")
        assert alert.is_active is True
        assert alert.is_critical is False

        ack = alert.acknowledge(user="operator1")
        assert ack.status == AlertStatus.ACKNOWLEDGED
        assert ack.acknowledged_by == "operator1"

        res = ack.resolve(user="supervisor1")
        assert res.status == AlertStatus.RESOLVED
        assert res.is_active is False


class TestVisionIncidentEntity:
    def test_vision_incident(self):
        inc = VisionIncident(camera_id="c-1", incident_type="FireDetected", severity=AlertSeverity.CRITICAL, detection_event_id="e-1", description="Flame detected")
        assert inc.is_submitted is False
        sub = inc.mark_submitted()
        assert sub.is_submitted is True


# ==============================================================================
# Infrastructure Repository Tests
# ==============================================================================

class TestInMemoryRepositories:
    @pytest.mark.asyncio
    async def test_camera_repository(self):
        repo = InMemoryCameraRepository()
        cam = Camera(name="Test Cam", location="Gate A", zone_id="z-1")
        saved = await repo.save_camera(cam)
        assert saved.id == cam.id

        fetched = await repo.get_camera(cam.id)
        assert fetched is not None
        assert fetched.name == "Test Cam"

        zone_cams = await repo.list_by_zone("z-1")
        assert len(zone_cams) == 1

        await repo.delete_camera(cam.id)
        assert await repo.get_camera(cam.id) is None

    @pytest.mark.asyncio
    async def test_frame_repository(self):
        repo = InMemoryFrameRepository()
        f = Frame(camera_id="c-1", sequence_number=1, width=1280, height=720, size_bytes=5000)
        await repo.save_frame(f)

        fetched = await repo.get_frame(f.id)
        assert fetched is not None
        assert fetched.camera_id == "c-1"

        frames = await repo.list_frames_by_camera("c-1")
        assert len(frames) == 1

    @pytest.mark.asyncio
    async def test_tracking_repository(self):
        repo = InMemoryTrackingRepository()
        t = TrackingObject(camera_id="c-1", object_class="FORKLIFT", confidence=0.88)
        await repo.save_track(t)

        active = await repo.list_active_tracks("c-1")
        assert len(active) == 1
        assert active[0].object_class == "FORKLIFT"

    @pytest.mark.asyncio
    async def test_alert_repository(self):
        repo = InMemoryAlertRepository()
        a = VisionAlert(camera_id="c-1", zone_id="z-1", alert_type="FireDetected", severity=AlertSeverity.CRITICAL, description="Fire in zone")
        await repo.save_alert(a)

        active_count = await repo.count_active_alerts("z-1")
        assert active_count == 1

        alerts = await repo.list_alerts(zone_id="z-1")
        assert len(alerts) == 1


# ==============================================================================
# API Endpoint Integration Tests
# ==============================================================================

@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(cameras_router)
    app.include_router(streams_router)
    app.include_router(detections_router)
    app.include_router(tracking_router)
    app.include_router(frame_history_router)
    app.include_router(alerts_router)
    return TestClient(app)


class TestVisionAPI:
    def test_register_and_list_cameras(self, client: TestClient):
        response = client.post(
            "/cameras",
            json={"name": "Dock Cam", "location": "Loading Dock", "camera_type": "IP"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Dock Cam"
        cam_id = data["id"]

        # Get by ID
        get_res = client.get(f"/cameras/{cam_id}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == cam_id

        # List
        list_res = client.get("/cameras")
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1

    def test_camera_heartbeat_and_health(self, client: TestClient):
        cam_res = client.post("/cameras", json={"name": "Health Cam", "location": "Zone B"})
        cam_id = cam_res.json()["id"]

        hb_res = client.post(f"/cameras/{cam_id}/heartbeat")
        assert hb_res.status_code == 200

        health_res = client.get(f"/cameras/{cam_id}/health")
        assert health_res.status_code in {200, 404}

    def test_video_stream_endpoints(self, client: TestClient):
        start_res = client.post("/video-streams/cam-101/start")
        assert start_res.status_code == 200
        assert start_res.json()["status"] == "STREAMING"

        status_res = client.get("/video-streams/cam-101/status")
        assert status_res.status_code == 200
        assert status_res.json()["status"] == "STREAMING"

        stop_res = client.delete("/video-streams/cam-101/stop")
        assert stop_res.status_code == 200
        assert stop_res.json()["status"] == "STOPPED"

    def test_detection_endpoints(self, client: TestClient):
        stats_res = client.get("/detections/stats")
        assert stats_res.status_code == 200
        assert "by_hazard_type" in stats_res.json()

        ppe_res = client.get("/detections/ppe-compliance")
        assert ppe_res.status_code == 200
        assert ppe_res.json()["compliance_rate_pct"] == 100.0

        list_res = client.get("/detections")
        assert list_res.status_code == 200

    def test_tracking_endpoints(self, client: TestClient):
        stats_res = client.get("/tracking/stats")
        assert stats_res.status_code == 200

        list_res = client.get("/tracking")
        assert list_res.status_code == 200

    def test_frame_history_endpoints(self, client: TestClient):
        stats_res = client.get("/frame-history/stats")
        assert stats_res.status_code == 200

        list_res = client.get("/frame-history")
        assert list_res.status_code == 200

    def test_alerts_and_health_endpoints(self, client: TestClient):
        health_list = client.get("/camera-health")
        assert health_list.status_code == 200

        alert_stats = client.get("/vision-alerts/stats")
        assert alert_stats.status_code == 200

        alerts_list = client.get("/vision-alerts")
        assert alerts_list.status_code == 200
