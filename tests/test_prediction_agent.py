import pytest

from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.prediction import (
    FeatureEngineer,
    MultiHorizonForecaster,
    PredictionAgent,
    PredictionAgentResult,
    PredictionModelRegistry,
)


def test_feature_engineering_and_model_registry():
    """Verify FeatureEngineer transforms context and PredictionModelRegistry lists registered models."""
    ctx = AgentContext(
        query="Predict failure risk for Pump P-7",
        target_entity_id="PUMP-P7",
        sensor_data=[{"type": "vibration", "value": 25.0}, {"type": "temp", "value": 82.0}],
        metadata={"maintenance_logs": [{"overdue_days": 14}]},
    )
    features = FeatureEngineer.extract_features(ctx)
    assert features.target_entity_id == "PUMP-P7"
    assert features.sensor_vibration_delta_pct == 25.0
    assert features.sensor_temp_c == 82.0
    assert features.maintenance_overdue_days == 14

    registry = PredictionModelRegistry.get()
    assert "equipment_failure" in registry.list_models()
    assert "incident_prediction" in registry.list_models()


def test_multi_horizon_forecaster():
    """Verify MultiHorizonForecaster produces multi-horizon prediction outputs."""
    ctx = AgentContext(
        query="Forecast PUMP-P7",
        target_entity_id="PUMP-P7",
        sensor_data=[{"type": "vibration", "value": 30.0}, {"type": "temp", "value": 85.0}],
    )
    features = FeatureEngineer.extract_features(ctx)
    forecaster = MultiHorizonForecaster()

    outputs = forecaster.forecast_horizons("equipment_failure", features)
    assert len(outputs) == 3
    horizons = [o.prediction_window.horizon_label for o in outputs]
    assert "1h" in horizons
    assert "24h" in horizons
    assert outputs[0].probability > 0.30


@pytest.mark.asyncio
async def test_prediction_agent_end_to_end_execution():
    """Verify PredictionAgent end-to-end execution workflow returning PredictionAgentResult."""
    agent = PredictionAgent()
    ctx = AgentContext(
        query="Which equipment is likely to fail in the next 24 hours?",
        target_entity_id="EQ-PUMP-7",
        sensor_data=[{"type": "vibration", "value": 40.0}, {"type": "temp", "value": 88.0}],
        metadata={"maintenance_logs": [{"overdue_days": 32}]},
    )

    result = await agent.execute(ctx)
    assert isinstance(result, PredictionAgentResult)
    assert result.success is True
    assert len(result.predictions) >= 6
    assert len(result.events) >= 1
    event_types = [e.event_type for e in result.events]
    assert "EquipmentFailurePredicted" in event_types
    assert "Immediate" in result.recommended_actions
