"""
test_vision_ai_service.py — Vision AI Facade Service Integration Unit Tests.
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.modules.vision.intelligence.risk_context_builder import VisionRiskContext
from app.modules.vision.intelligence.vision_ai_service import VisionAIService


@pytest.mark.asyncio
async def test_process_vision_frame_intelligence():
    service = VisionAIService()

    mock_risk_context = VisionRiskContext(
        zone_id="ZONE-A",
        camera_id="CAM-01",
        zone_risk_level="HIGH",
        active_sensor_alerts=[],
        nearby_equipment_types=["FORKLIFT"],
        zone_worker_count=2,
        historical_incident_count=1,
        requires_strict_ppe=True,
    )

    with patch.object(service, "sync_to_knowledge_graph", new_callable=AsyncMock) as mock_sync, \
         patch.object(service._risk_context, "build_context", new_callable=AsyncMock) as mock_ctx_build, \
         patch("app.infrastructure.kafka.producer.EventBus.get") as mock_bus_get:

        mock_ctx_build.return_value = mock_risk_context
        mock_bus = AsyncMock()
        mock_bus.publish.return_value = True
        mock_bus_get.return_value = mock_bus
        mock_sync.return_value = True

        assessment, explanation = await service.process_vision_frame_intelligence(
            camera_id="CAM-01",
            zone_id="ZONE-A",
            detected_ppe=["SAFETY_VEST"],  # Missing helmet!
            worker_id="w-101",
            velocity=1.2,
        )

        assert assessment.camera_id == "CAM-01"
        assert assessment.overall_risk_score > 0.0
        assert explanation.explanation_id.startswith("expl-")
        mock_sync.assert_called_once()
