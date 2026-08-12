"""
test_vision_safety_api.py — FastAPI Integration Tests for All Vision Safety Endpoints.
"""
from unittest.mock import AsyncMock, patch
import pytest
from fastapi import status


def test_post_ppe_check(client, auth_headers):
    payload = {
        "camera_id": "CAM-01",
        "zone_id": "ZONE-A",
        "detected_ppe": ["HELMET", "SAFETY_VEST"],
        "worker_id": "w-1",
    }
    response = client.post("/api/v1/ppe/check", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert data["compliance_score_pct"] == 100.0


def test_get_ppe_repeat_offenders(client, auth_headers):
    response = client.get("/api/v1/ppe/repeat-offenders", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK


def test_get_vision_violations(client, auth_headers):
    response = client.get("/api/v1/vision-violations", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert len(data) > 0


def test_post_evaluate_zone_access(client, auth_headers):
    payload = {
        "camera_id": "CAM-01",
        "zone_id": "ZONE-A",
        "worker_id": "w-1",
        "worker_role": "OPERATOR",
        "worker_x": 5.0,
        "worker_y": 5.0,
        "polygon": [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0]],
        "allowed_roles": ["OPERATOR"],
    }
    response = client.post("/api/v1/restricted-zones/evaluate-access", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert data["is_inside_zone"] is True
    assert data["access_status"] == "AUTHORIZED"


def test_get_compliance_summary(client, auth_headers):
    response = client.get("/api/v1/vision-analytics/compliance-summary?zone_id=ZONE-A", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert "overall_compliance_index" in data


def test_get_zone_occupancy(client, auth_headers):
    response = client.get("/api/v1/occupancy/ZONE-A?worker_count=10", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert data["worker_count"] == 10


def test_post_evaluate_worker_interaction(client, auth_headers):
    payload = {
        "camera_id": "CAM-01",
        "zone_id": "ZONE-A",
        "worker_id": "w-1",
        "equipment_id": "forklift-01",
        "equipment_type": "FORKLIFT",
        "worker_pos": [10.0, 10.0],
        "equipment_pos": [10.0, 15.0],
    }
    response = client.post("/api/v1/worker-interactions/evaluate", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert data["equipment_type"] == "FORKLIFT"


def test_post_evaluate_fall(client, auth_headers):
    payload = {
        "camera_id": "CAM-01",
        "zone_id": "ZONE-A",
        "worker_id": "w-1",
        "bbox_aspect_ratio": 1.5,
        "downward_velocity": 2.0,
    }
    response = client.post("/api/v1/fall-detection/evaluate", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK


def test_post_verify_fire(client, auth_headers):
    payload = {
        "camera_id": "CAM-01",
        "zone_id": "ZONE-A",
        "visual_type": "FIRE",
        "camera_confidence": 0.9,
        "sensor_smoke_detected": True,
    }
    response = client.post("/api/v1/fire-verification/verify", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK


def test_post_vision_ai_process(client, auth_headers):
    with patch(
        "app.modules.vision.intelligence.vision_ai_service.VisionAIService.sync_to_knowledge_graph",
        new_callable=AsyncMock,
    ), patch(
        "app.modules.vision.intelligence.risk_context_builder.MultiSourceRiskContextBuilder.build_context",
        new_callable=AsyncMock,
    ) as mock_ctx:
        from app.modules.vision.intelligence.risk_context_builder import VisionRiskContext
        mock_ctx.return_value = VisionRiskContext(zone_id="ZONE-A", camera_id="CAM-01")
        payload = {
            "camera_id": "CAM-01",
            "zone_id": "ZONE-A",
            "detected_ppe": ["HELMET", "SAFETY_VEST"],
            "worker_id": "w-1",
        }
        response = client.post("/api/v1/vision-ai/process", json=payload, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert "assessment" in data
        assert "explanation" in data


def test_post_vision_ai_explain(client, auth_headers):
    with patch(
        "app.modules.vision.intelligence.vision_ai_service.VisionAIService.sync_to_knowledge_graph",
        new_callable=AsyncMock,
    ), patch(
        "app.modules.vision.intelligence.risk_context_builder.MultiSourceRiskContextBuilder.build_context",
        new_callable=AsyncMock,
    ) as mock_ctx:
        from app.modules.vision.intelligence.risk_context_builder import VisionRiskContext
        mock_ctx.return_value = VisionRiskContext(zone_id="ZONE-A", camera_id="CAM-01")
        payload = {
            "camera_id": "CAM-01",
            "zone_id": "ZONE-A",
            "detected_ppe": ["SAFETY_VEST"],
            "worker_id": "w-1",
        }
        response = client.post("/api/v1/vision-ai/explain", json=payload, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert "explanation_id" in data
        assert "alternative_interpretations" in data


def test_post_vision_ai_context(client, auth_headers):
    with patch(
        "app.modules.knowledge.infrastructure.repositories.traversal_repository.TraversalRepository.get_neighborhood",
        new_callable=AsyncMock,
    ) as mock_nb:
        mock_nb.return_value = {"nodes": [], "edges": []}
        url = "/api/v1/vision-ai/context?camera_id=CAM-01&zone_id=ZONE-A&primary_entity_id=w-1"
        response = client.post(url, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert "graphrag_narrative" in data
