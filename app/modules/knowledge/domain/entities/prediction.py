from pydantic import Field

from app.modules.knowledge.domain.entities.base import EventEntity


class Prediction(EventEntity):
    """AI agent predictive insight or risk forecast."""

    model_name: str
    target_entity_id: str
    predicted_risk_score: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
    recommended_action: str
    entity_type: str = Field(default="Prediction")
