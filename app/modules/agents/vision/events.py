"""events.py — Standardized Vision Domain Event Generator."""

from app.modules.agents.core.events import AgentDomainEvent
from app.modules.agents.vision.models import VisionConfidence, VisionDetection, VisionEventPayload


class VisionEventGenerator:
    """Generates standardized vision domain events for the EventBus."""

    @staticmethod
    def generate_events(
        agent_name: str,
        camera_id: str,
        zone_id: str,
        detections: list[VisionDetection],
        confidence: VisionConfidence,
        trace_id: str,
    ) -> list[AgentDomainEvent]:
        """
        Generate domain events for visual observations.

        Returns:
            list of AgentDomainEvent objects (FireDetected, SmokeDetected, PPEViolation, SpillDetected, CrowdingDetected).
        """
        events: list[AgentDomainEvent] = []
        det_dicts = [d.model_dump() for d in detections]

        labels = set(d.label.lower() for d in detections)

        if any(l in labels for l in ("fire", "flame", "explosion")):
            payload = VisionEventPayload(
                camera_id=camera_id,
                zone_id=zone_id,
                event_type="FireDetected",
                detections=det_dicts,
                confidence=confidence,
            )
            events.append(AgentDomainEvent(event_type="FireDetected", agent_name=agent_name, payload=payload.model_dump(), trace_id=trace_id))

        if any(l in labels for l in ("smoke", "plume")):
            payload = VisionEventPayload(
                camera_id=camera_id,
                zone_id=zone_id,
                event_type="SmokeDetected",
                detections=det_dicts,
                confidence=confidence,
            )
            events.append(AgentDomainEvent(event_type="SmokeDetected", agent_name=agent_name, payload=payload.model_dump(), trace_id=trace_id))

        if any(l in labels for l in ("spill", "chemical_leak", "oil_spill")):
            payload = VisionEventPayload(
                camera_id=camera_id,
                zone_id=zone_id,
                event_type="SpillDetected",
                detections=det_dicts,
                confidence=confidence,
            )
            events.append(AgentDomainEvent(event_type="SpillDetected", agent_name=agent_name, payload=payload.model_dump(), trace_id=trace_id))

        # Always emit a general Observation event for Knowledge Graph updating
        events.append(
            AgentDomainEvent(
                event_type="VisualObservationRecorded",
                agent_name=agent_name,
                payload={"camera_id": camera_id, "zone_id": zone_id, "detection_count": len(detections)},
                trace_id=trace_id,
            )
        )

        return events
