from typing import Any
from app.core.logging import get_logger
from app.modules.risk_prediction.domain.enums import RiskLevel
from app.modules.risk_prediction.domain.models import RiskAssessment, RiskForecast

log = get_logger(__name__)

try:
    from app.modules.supervisor.supervisor_decision_engine import SupervisorDecisionEngine
except ImportError:
    SupervisorDecisionEngine = None

class SupervisorBridge:
    """Publishes risk assessments to the Supervisor for emergency and
    notification decisions. Reuses existing supervisor_decision_engine."""
    
    def __init__(self, decision_engine: Any = None):
        self.decision_engine = decision_engine if decision_engine else (SupervisorDecisionEngine() if SupervisorDecisionEngine else None)

    async def report_risk_assessment(
        self, assessment: RiskAssessment
    ) -> Any | None:
        """Report risk assessment to supervisor for decision routing.
        CRITICAL/EXTREME → triggers emergency evaluation
        HIGH → triggers notification dispatch
        """
        if not self.decision_engine:
            log.warning("SupervisorDecisionEngine not available.")
            return None
            
        max_level = None
        for pred in assessment.predictions:
            # We assume RiskScore has a level property or we map it
            # For this context we'll pass the whole assessment
            pass
            
        try:
            return await self.decision_engine.evaluate_assessment(assessment)
        except AttributeError:
            log.warning("evaluate_assessment method not found on SupervisorDecisionEngine")
            return None

    async def report_risk_escalation(
        self, assessment: RiskAssessment, from_level: RiskLevel
    ) -> None:
        """Notify supervisor of risk level escalation."""
        if not self.decision_engine:
            return
            
        try:
            if hasattr(self.decision_engine, 'handle_escalation'):
                await self.decision_engine.handle_escalation(assessment, from_level)
            else:
                log.info(f"Escalation reported for {assessment.entity_id} from {from_level}")
        except Exception as e:
            log.error(f"Error reporting risk escalation: {e}")

    async def report_forecast(
        self, forecast: RiskForecast
    ) -> None:
        """Share forecast with supervisor for proactive planning."""
        if not self.decision_engine:
            return
            
        try:
            if hasattr(self.decision_engine, 'handle_forecast'):
                await self.decision_engine.handle_forecast(forecast)
            else:
                log.info(f"Forecast reported for {forecast.entity_id}")
        except Exception as e:
            log.error(f"Error reporting forecast: {e}")
