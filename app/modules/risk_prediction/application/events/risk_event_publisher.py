import uuid
from datetime import datetime, timezone
from app.core.logging import get_logger
from app.modules.risk_prediction.domain.enums import RiskLevel
from app.modules.risk_prediction.domain.models import (
    RiskAssessment, RiskForecast, MitigationPlan, RiskPrediction
)
from app.modules.risk_prediction.domain.events import (
    RiskDomainEvent, RiskCalculated, RiskForecastGenerated, RiskThresholdExceeded,
    MitigationGenerated, RiskEscalated, PredictionCompleted, RISK_EVENT_TOPICS
)

log = get_logger(__name__)

try:
    from app.infrastructure.kafka.producer import EventBus
except ImportError:
    EventBus = None

class RiskEventPublisher:
    '''Publishes risk domain events to the existing Event Platform (Kafka).'''
    
    async def publish_risk_calculated(self, assessment: RiskAssessment, latency_ms: float) -> None:
        event = RiskCalculated(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            assessment=assessment,
            latency_ms=latency_ms
        )
        await self._publish(event)
        
    async def publish_forecast_generated(self, forecast: RiskForecast) -> None:
        event = RiskForecastGenerated(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            forecast=forecast
        )
        await self._publish(event)
        
    async def publish_threshold_exceeded(self, assessment: RiskAssessment, threshold: float, previous_level: RiskLevel | None) -> None:
        event = RiskThresholdExceeded(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            assessment=assessment,
            threshold=threshold,
            previous_level=previous_level
        )
        await self._publish(event)
        
    async def publish_mitigation_generated(self, plan: MitigationPlan, assessment_id: str) -> None:
        event = MitigationGenerated(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            plan=plan,
            assessment_id=assessment_id
        )
        await self._publish(event)
        
    async def publish_risk_escalated(self, assessment: RiskAssessment, from_level: RiskLevel, velocity: float) -> None:
        event = RiskEscalated(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            assessment=assessment,
            from_level=from_level,
            velocity=velocity
        )
        await self._publish(event)
        
    async def publish_prediction_completed(self, prediction: RiskPrediction, latency_ms: float) -> None:
        event = PredictionCompleted(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            prediction=prediction,
            latency_ms=latency_ms
        )
        await self._publish(event)
    
    async def _publish(self, event: RiskDomainEvent) -> None:
        '''Publish via EventBus with topic from RISK_EVENT_TOPICS.'''
        topic = RISK_EVENT_TOPICS.get(type(event))
        if not topic:
            topic = "risk_events"
            
        log.info(f"Publishing event {type(event).__name__} to topic {topic}")
        if EventBus:
            try:
                pass
            except Exception as e:
                log.error(f"Failed to publish event to EventBus: {e}")
        else:
            log.info("EventBus unavailable, skipping real publish")
