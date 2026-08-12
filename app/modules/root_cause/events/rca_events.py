"""rca_events.py — RCA Platform Event Definitions and Publishers."""
from __future__ import annotations
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus

log = get_logger("root_cause.events")


class RCATopics:
    INVESTIGATION_STARTED = "rca.investigation.started"
    EVIDENCE_COLLECTED = "rca.evidence.collected"
    TIMELINE_COMPLETED = "rca.timeline.completed"
    HYPOTHESIS_GENERATED = "rca.hypothesis.generated"
    ROOT_CAUSE_IDENTIFIED = "rca.root_cause.identified"
    RECOMMENDATION_GENERATED = "rca.recommendation.generated"
    INVESTIGATION_COMPLETED = "rca.investigation.completed"
    INVESTIGATION_ARCHIVED = "rca.investigation.archived"


def _uuid() -> str:
    return str(uuid.uuid4())

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BaseRCAEvent:
    event_id: str = field(default_factory=_uuid)
    timestamp: str = field(default_factory=_now)
    source_module: str = "root_cause_analysis"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class InvestigationStarted(BaseRCAEvent):
    investigation_id: str = ""
    incident_id: str = ""
    triggered_by: str = ""
    event_type: str = "InvestigationStarted"


@dataclass
class EvidenceCollected(BaseRCAEvent):
    investigation_id: str = ""
    evidence_count: int = 0
    sources: list[str] = field(default_factory=list)
    event_type: str = "EvidenceCollected"


@dataclass
class TimelineCompleted(BaseRCAEvent):
    investigation_id: str = ""
    event_count: int = 0
    duration_seconds: float = 0.0
    event_type: str = "TimelineCompleted"


@dataclass
class HypothesisGenerated(BaseRCAEvent):
    investigation_id: str = ""
    hypothesis_count: int = 0
    top_hypothesis: str = ""
    event_type: str = "HypothesisGenerated"


@dataclass
class RootCauseIdentified(BaseRCAEvent):
    investigation_id: str = ""
    primary_cause_description: str = ""
    confidence: float = 0.0
    event_type: str = "RootCauseIdentified"


@dataclass
class RecommendationGenerated(BaseRCAEvent):
    investigation_id: str = ""
    recommendation_count: int = 0
    critical_count: int = 0
    event_type: str = "RecommendationGenerated"


@dataclass
class InvestigationCompleted(BaseRCAEvent):
    investigation_id: str = ""
    incident_id: str = ""
    overall_confidence: float = 0.0
    duration_seconds: float = 0.0
    event_type: str = "InvestigationCompleted"


@dataclass
class InvestigationArchived(BaseRCAEvent):
    investigation_id: str = ""
    event_type: str = "InvestigationArchived"


async def publish_rca_event(event: BaseRCAEvent, topic: str) -> bool:
    try:
        payload = event.to_dict()
        key = getattr(event, "investigation_id", None) or event.event_id
        bus = EventBus.get()
        result = await bus.publish(topic=topic, payload=payload, key=key)
        log.info(f"Published RCA event {getattr(event, 'event_type', 'unknown')} to {topic}")
        return result
    except Exception as exc:
        log.error(f"Failed to publish RCA event: {exc}")
        return False
