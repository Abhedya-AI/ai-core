from __future__ import annotations

import logging

log = logging.getLogger(__name__)

class ForecastSupervisorBridge:
    def __init__(self):
        try:
            from app.modules.supervisor.supervisor_decision_engine import SupervisorDecisionEngine
            self._supervisor = SupervisorDecisionEngine()
        except ImportError:
            self._supervisor = None

    async def notify_forecast_result(self, forecast_result: dict) -> None:
        """Publishes ForecastResult to Supervisor for downstream decisions."""
        log.info(f"Notifying supervisor of forecast result: {forecast_result.get('forecast_id')}")
        if self._supervisor and hasattr(self._supervisor, 'process_event'):
            try:
                await self._supervisor.process_event({"type": "FORECAST_RESULT", "data": forecast_result})
            except Exception as e:
                log.error(f"Supervisor notification failed: {e}")

    async def notify_scenario_comparison(self, comparison: dict) -> None:
        """Publishes ScenarioComparison for Supervisor hazard propagation decisions."""
        log.info(f"Notifying supervisor of scenario comparison")
        if self._supervisor and hasattr(self._supervisor, 'process_event'):
            try:
                await self._supervisor.process_event({"type": "SCENARIO_COMPARISON", "data": comparison})
            except Exception as e:
                log.error(f"Supervisor notification failed: {e}")

    async def notify_threshold_exceeded(self, entity_id: str, forecast_type: str, value: float, threshold: float) -> None:
        """Triggers Supervisor emergency planning if threshold exceeded."""
        log.warning(f"Threshold exceeded for {entity_id} ({forecast_type}): {value} > {threshold}")
        if self._supervisor and hasattr(self._supervisor, 'process_event'):
            try:
                await self._supervisor.process_event({
                    "type": "THRESHOLD_EXCEEDED",
                    "data": {"entity_id": entity_id, "forecast_type": forecast_type, "value": value, "threshold": threshold}
                })
            except Exception as e:
                log.error(f"Supervisor notification failed: {e}")

    async def notify_maintenance_critical(self, equipment_id: str, rul_hours: float, urgency: str) -> None:
        """Triggers Supervisor maintenance planning workflow."""
        log.warning(f"Critical maintenance for {equipment_id}, RUL: {rul_hours}h, Urgency: {urgency}")
        if self._supervisor and hasattr(self._supervisor, 'process_event'):
            try:
                await self._supervisor.process_event({
                    "type": "MAINTENANCE_CRITICAL",
                    "data": {"equipment_id": equipment_id, "rul_hours": rul_hours, "urgency": urgency}
                })
            except Exception as e:
                log.error(f"Supervisor notification failed: {e}")
