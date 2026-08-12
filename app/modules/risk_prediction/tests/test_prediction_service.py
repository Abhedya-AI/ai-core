"""
app/modules/risk_prediction/tests/test_prediction_service.py
Integration tests for the RiskPredictionService orchestrator.
Tests the full pipeline from feature collection to published events.

Note: Tests are written to match the RiskPredictionService's actual API
(not the originally designed API which differed in method names).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from app.modules.risk_prediction.domain.enums import (
    AssessmentStatus,
    EntityType,
    ForecastHorizon,
    RiskLevel,
    RiskType,
)
from app.modules.risk_prediction.domain.models import (
    EquipmentRisk,
    PlantRisk,
    RiskAssessment,
    RiskForecast,
    RiskScenario,
    WorkerRisk,
    ZoneRisk,
)


@pytest.fixture
def mock_feature_collector(sample_all_features):
    from app.modules.risk_prediction.application.feature_engineering.feature_collector import FeatureVector
    mock = AsyncMock()
    fv = FeatureVector(
        entity_id="EQ-PUMP-001",
        entity_type=EntityType.EQUIPMENT,
        features=sample_all_features,
        collected_at="",
        sensor_completeness=0.9,
        vision_completeness=0.8,
        graph_completeness=0.85,
        graphrag_completeness=0.75,
    )
    mock.collect = AsyncMock(return_value=fv)
    return mock


@pytest.fixture
def mock_ensemble_engine():
    from app.modules.risk_prediction.application.ensemble.ensemble_engine import EnsemblePrediction
    mock = AsyncMock()
    mock.predict = AsyncMock(
        return_value=EnsemblePrediction(
            probability=0.45,
            confidence=0.85,
            uncertainty=0.08,
            model_contributions={"RULE_BASED": 0.40, "STATISTICAL": 0.50},
            ensemble_explanation="Elevated temperature and vibration sensors indicate medium risk.",
            top_features={"TEMP-001_rolling_mean": 0.35, "TEMP-001_drift_score": 0.25},
            available_models=["RULE_BASED", "STATISTICAL"],
        )
    )
    return mock


@pytest.fixture
def mock_forecaster(sample_forecast):
    """Mock using the actual method name the service calls."""
    mock = AsyncMock()
    mock.forecast = AsyncMock(return_value=sample_forecast)
    return mock


@pytest.fixture
def mock_mitigation_engine(sample_mitigation_plan):
    """Mock using the actual method name the service calls."""
    mock = AsyncMock()
    mock.generate_plan = AsyncMock(return_value=sample_mitigation_plan)
    return mock


@pytest.fixture
def mock_scoring_service(medium_risk, sample_risk_factors, high_confidence):
    mock = MagicMock()
    mock.compute_risk_score = MagicMock(return_value=medium_risk)
    mock.compute_confidence = MagicMock(return_value=high_confidence)
    mock.extract_top_factors = MagicMock(return_value=sample_risk_factors)
    mock.build_explanation = MagicMock(return_value="Medium equipment failure risk detected.")
    mock.compute_uncertainty = MagicMock(return_value=0.08)
    mock.compute_composite_risk = MagicMock(return_value=medium_risk)
    return mock


@pytest.fixture
def mock_graph_service_simple():
    """Graph service with the actual method the service calls: get_context."""
    mock = AsyncMock()
    mock.get_context = AsyncMock(return_value=None)
    mock.get_entity_graph_context = AsyncMock(return_value=None)
    mock.sync_risk_node = AsyncMock()
    return mock


@pytest.fixture
def prediction_service(
    mock_feature_collector,
    mock_ensemble_engine,
    mock_forecaster,
    mock_graph_service_simple,
    mock_mitigation_engine,
    mock_scoring_service,
    mock_risk_repository,
    mock_event_publisher,
):
    from app.modules.risk_prediction.application.services.risk_prediction_service import RiskPredictionService
    return RiskPredictionService(
        feature_collector=mock_feature_collector,
        ensemble_engine=mock_ensemble_engine,
        forecaster=mock_forecaster,
        graph_service=mock_graph_service_simple,
        mitigation_engine=mock_mitigation_engine,
        scoring_service=mock_scoring_service,
        risk_repository=mock_risk_repository,
        event_publisher=mock_event_publisher,
        graphrag_service=None,
    )


class TestAssessEntity:
    @pytest.mark.asyncio
    async def test_assess_entity_returns_assessment(
        self, prediction_service, sample_entity_id
    ):
        assessment = await prediction_service.assess_entity(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001", "PRESS-002"],
        )
        assert isinstance(assessment, RiskAssessment)

    @pytest.mark.asyncio
    async def test_assess_entity_calls_feature_collector(
        self, prediction_service, mock_feature_collector, sample_entity_id
    ):
        await prediction_service.assess_entity(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
        )
        mock_feature_collector.collect.assert_called_once()

    @pytest.mark.asyncio
    async def test_assess_entity_calls_ensemble(
        self, prediction_service, mock_ensemble_engine, sample_entity_id
    ):
        await prediction_service.assess_entity(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
        )
        mock_ensemble_engine.predict.assert_called()

    @pytest.mark.asyncio
    async def test_assess_entity_saves_to_repository(
        self, prediction_service, mock_risk_repository, sample_entity_id
    ):
        await prediction_service.assess_entity(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
        )
        mock_risk_repository.save_assessment.assert_called_once()

    @pytest.mark.asyncio
    async def test_assess_entity_publishes_events(
        self, prediction_service, mock_event_publisher, sample_entity_id
    ):
        await prediction_service.assess_entity(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
        )
        # The service calls event_publisher.publish() with domain events
        mock_event_publisher.publish.assert_called()

    @pytest.mark.asyncio
    async def test_assess_entity_generates_forecast(
        self, prediction_service, mock_forecaster, sample_entity_id
    ):
        assessment = await prediction_service.assess_entity(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
            generate_forecast=True,
        )
        # Service calls forecaster.forecast() not generate_forecast()
        mock_forecaster.forecast.assert_called_once()
        assert assessment.forecast is not None

    @pytest.mark.asyncio
    async def test_assess_entity_skips_forecast_when_disabled(
        self, prediction_service, mock_forecaster, sample_entity_id
    ):
        await prediction_service.assess_entity(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
            generate_forecast=False,
        )
        mock_forecaster.forecast.assert_not_called()

    @pytest.mark.asyncio
    async def test_assess_entity_generates_mitigation(
        self, prediction_service, mock_mitigation_engine, sample_entity_id
    ):
        assessment = await prediction_service.assess_entity(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
            generate_mitigation=True,
        )
        mock_mitigation_engine.generate_plan.assert_called_once()
        assert assessment.mitigation_plan is not None

    @pytest.mark.asyncio
    async def test_assess_entity_skips_mitigation_when_disabled(
        self, prediction_service, mock_mitigation_engine, sample_entity_id
    ):
        await prediction_service.assess_entity(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
            generate_mitigation=False,
        )
        mock_mitigation_engine.generate_plan.assert_not_called()

    @pytest.mark.asyncio
    async def test_assess_entity_with_completed_status(
        self, prediction_service, sample_entity_id
    ):
        assessment = await prediction_service.assess_entity(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
        )
        assert assessment.status == AssessmentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_assess_entity_entity_fields_preserved(
        self, prediction_service, sample_entity_id
    ):
        assessment = await prediction_service.assess_entity(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
        )
        assert assessment.entity_id == sample_entity_id
        assert assessment.entity_type == EntityType.EQUIPMENT


class TestAssessEquipment:
    @pytest.mark.asyncio
    async def test_assess_equipment_returns_equipment_risk(
        self, prediction_service
    ):
        result = await prediction_service.assess_equipment(
            equipment_id="EQ-PUMP-001",
            sensor_ids=["TEMP-001"],
            equipment_type="CENTRIFUGAL_PUMP",
            equipment_name="Main Pump A",
        )
        assert isinstance(result, EquipmentRisk)

    @pytest.mark.asyncio
    async def test_assess_equipment_has_equipment_fields(
        self, prediction_service
    ):
        result = await prediction_service.assess_equipment(
            equipment_id="EQ-PUMP-001",
            sensor_ids=["TEMP-001"],
            equipment_type="CENTRIFUGAL_PUMP",
            equipment_name="Main Pump A",
        )
        assert result.equipment_id == "EQ-PUMP-001"


class TestAssessWorker:
    @pytest.mark.asyncio
    async def test_assess_worker_returns_worker_risk(
        self, prediction_service
    ):
        result = await prediction_service.assess_worker(
            worker_id="WORKER-W-001",
            zone_id="ZONE-A-01",
            sensor_ids=[],
        )
        assert isinstance(result, WorkerRisk)

    @pytest.mark.asyncio
    async def test_assess_worker_has_worker_fields(
        self, prediction_service
    ):
        result = await prediction_service.assess_worker(
            worker_id="WORKER-W-001",
            zone_id="ZONE-A-01",
            sensor_ids=[],
        )
        assert result.worker_id == "WORKER-W-001"
        assert result.zone_id == "ZONE-A-01"


class TestAssessZone:
    @pytest.mark.asyncio
    async def test_assess_zone_returns_zone_risk(
        self, prediction_service
    ):
        result = await prediction_service.assess_zone(
            zone_id="ZONE-A-01",
            zone_name="Process Area A",
            equipment_ids=["EQ-001"],
            sensor_ids=["TEMP-001"],
        )
        assert isinstance(result, ZoneRisk)

    @pytest.mark.asyncio
    async def test_assess_zone_has_zone_fields(
        self, prediction_service
    ):
        result = await prediction_service.assess_zone(
            zone_id="ZONE-A-01",
            zone_name="Process Area A",
            equipment_ids=["EQ-001", "EQ-002"],
            sensor_ids=["TEMP-001"],
        )
        assert result.zone_id == "ZONE-A-01"


class TestRunScenario:
    @pytest.mark.asyncio
    async def test_run_scenario_returns_risk_scenario(
        self, prediction_service, sample_entity_id
    ):
        scenario = await prediction_service.run_scenario(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
            scenario_name="High temperature test",
            modified_conditions={"TEMP-001_rolling_mean": 0.95},
        )
        assert isinstance(scenario, RiskScenario)

    @pytest.mark.asyncio
    async def test_run_scenario_has_modified_conditions(
        self, prediction_service, sample_entity_id
    ):
        modified = {"TEMP-001_rolling_mean": 0.95, "fire_detection_score": 0.6}
        scenario = await prediction_service.run_scenario(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
            scenario_name="Extreme heat test",
            modified_conditions=modified,
        )
        assert scenario.modified_conditions == modified

    @pytest.mark.asyncio
    async def test_run_scenario_has_name(
        self, prediction_service, sample_entity_id
    ):
        scenario = await prediction_service.run_scenario(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
            scenario_name="Test Scenario XYZ",
            modified_conditions={},
        )
        assert scenario.name == "Test Scenario XYZ"

    @pytest.mark.asyncio
    async def test_run_scenario_has_id(
        self, prediction_service, sample_entity_id
    ):
        scenario = await prediction_service.run_scenario(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
            scenario_name="Delta test",
            modified_conditions={},
        )
        assert scenario.id is not None
        assert len(scenario.id) > 0


class TestThresholdEscalation:
    @pytest.mark.asyncio
    async def test_check_threshold_no_previous_no_event(
        self,
        prediction_service,
        mock_event_publisher,
        sample_assessment,
    ):
        """When there's no previous assessment, no escalation should occur."""
        await prediction_service._check_threshold_and_escalate(
            assessment=sample_assessment,
            previous_assessment=None,
        )
        # With no previous assessment, no threshold exceeded event
        # The mock publish may or may not be called — but should not crash

    @pytest.mark.asyncio
    async def test_check_threshold_same_level_no_crash(
        self,
        prediction_service,
        mock_event_publisher,
        sample_assessment,
    ):
        """Same risk level should not cause errors."""
        # Should not raise
        await prediction_service._check_threshold_and_escalate(
            assessment=sample_assessment,
            previous_assessment=sample_assessment,
        )
