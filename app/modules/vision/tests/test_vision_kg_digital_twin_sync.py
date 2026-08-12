"""
test_vision_kg_digital_twin_sync.py — Vision KG & Digital Twin Sync Tests.
"""
from unittest.mock import AsyncMock, patch
import pytest

from app.modules.vision.domain.entities.vision_assessment import VisionAssessment
from app.modules.vision.domain.entities.vision_evidence import VisionEvidence
from app.modules.vision.intelligence.vision_ai_service import VisionAIService


@pytest.mark.asyncio
async def test_digital_twin_and_kg_sync():
    service = VisionAIService()

    ev = VisionEvidence(
        camera_id="CAM-01",
        zone_id="ZONE-A",
        primary_detection_label="Worker",
        detection_confidence=0.9,
        reasoning_summary="Test reasoning",
    )
    assessment = VisionAssessment(
        camera_id="CAM-01",
        zone_id="ZONE-A",
        assessment_type="PPE",
        overall_risk_score=25.0,
        evidence=ev,
    )

    with patch.object(service._repo, "execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = []
        ok = await service.sync_to_knowledge_graph(assessment)
        assert ok is True
        mock_exec.assert_called_once()
        query_str = mock_exec.call_args[0][0]
        assert "MERGE (z:Zone" in query_str
        assert "MERGE (c:Camera" in query_str
        assert "-[:LOCATED_IN]->" in query_str
        assert "-[:GENERATED]->" in query_str
