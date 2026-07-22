"""events.py — Standardized Predictive Domain Event Generator."""

from app.modules.agents.core.events import AgentDomainEvent
from app.modules.agents.prediction.models import PredictionOutput


class PredictionEventGenerator:
    """Generates domain events from model predictions for the EventBus."""

    @staticmethod
    def generate_events(
        agent_name: str,
        predictions: list[PredictionOutput],
        trace_id: str,
    ) -> list[AgentDomainEvent]:
        """
        Generate predictive domain events.

        Returns:
            list of AgentDomainEvent objects (EquipmentFailurePredicted, IncidentProbabilityHigh, MaintenanceRecommended).
        """
        events: list[AgentDomainEvent] = []
        for p in predictions:
            payload = p.model_dump()
            if p.prediction_type == "EQUIPMENT_FAILURE" and p.probability >= 0.60:
                events.append(
                    AgentDomainEvent(
                        event_type="EquipmentFailurePredicted",
                        agent_name=agent_name,
                        payload=payload,
                        trace_id=trace_id,
                    )
                )
            elif p.prediction_type == "INCIDENT_PROBABILITY" and p.probability >= 0.50:
                events.append(
                    AgentDomainEvent(
                        event_type="IncidentProbabilityHigh",
                        agent_name=agent_name,
                        payload=payload,
                        trace_id=trace_id,
                    )
                )
            elif p.prediction_type == "MAINTENANCE_FORECAST" and p.probability >= 0.50:
                events.append(
                    AgentDomainEvent(
                        event_type="MaintenanceRecommended",
                        agent_name=agent_name,
                        payload=payload,
                        trace_id=trace_id,
                    )
                )

        events.append(
            AgentDomainEvent(
                event_type="PredictionForecastGenerated",
                agent_name=agent_name,
                payload={"prediction_count": len(predictions)},
                trace_id=trace_id,
            )
        )
        return events
