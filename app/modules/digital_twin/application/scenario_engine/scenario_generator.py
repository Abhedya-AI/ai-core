from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger
log = get_logger(__name__)

class TwinScenarioGenerator:
    def __init__(self, graphrag_service: Any = None, risk_service: Any = None, forecast_service: Any = None):
        self.graphrag_service = graphrag_service
        self.risk_service = risk_service
        self.forecast_service = forecast_service

    def _adjust_for_context(self, base_value: float, context: dict[str, Any], scenario_type: str) -> float:
        active_hazards = len(context.get("active_hazards", []))
        recent_incidents = len(context.get("recent_incidents", []))
        
        factor = 1.0 + (active_hazards * 0.1) + (recent_incidents * 0.05)
        if scenario_type == "WORST_CASE":
            return base_value * factor
        elif scenario_type == "BEST_CASE":
            return base_value / factor
        return base_value

    def _compute_confidence(self, data_completeness: float, model_coverage: float) -> float:
        return (data_completeness * 0.6) + (model_coverage * 0.4)

    async def generate_scenarios(self, twin_id: str, twin_state: dict[str, Any], entity_id: str, entity_type: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        t0 = time.perf_counter()
        
        entity_state = twin_state.get(entity_id, {})
        base_risk = entity_state.get("risk_score", 0.1)
        base_health = entity_state.get("health_score", 0.9)
        
        scenarios = []
        
        # BEST_CASE
        scenarios.append({
            "scenario_type": "BEST_CASE",
            "risk_delta": self._adjust_for_context(-0.2, context, "BEST_CASE"),
            "health_delta": self._adjust_for_context(0.15, context, "BEST_CASE"),
            "probability": 0.25,
            "conditions": {"no_incidents": True, "maintenance_on_schedule": True},
            "key_drivers": ["Optimal maintenance", "No unexpected failures"],
            "confidence": self._compute_confidence(0.9, 0.8)
        })
        
        # EXPECTED_CASE
        scenarios.append({
            "scenario_type": "EXPECTED_CASE",
            "risk_delta": self._adjust_for_context(0.05, context, "EXPECTED_CASE"),
            "health_delta": self._adjust_for_context(-0.05, context, "EXPECTED_CASE"),
            "probability": 0.50,
            "conditions": {"current_trajectory": True},
            "key_drivers": ["Business as usual"],
            "confidence": self._compute_confidence(0.9, 0.9)
        })
        
        # WORST_CASE
        scenarios.append({
            "scenario_type": "WORST_CASE",
            "risk_delta": self._adjust_for_context(0.35, context, "WORST_CASE"),
            "health_delta": self._adjust_for_context(-0.30, context, "WORST_CASE"),
            "probability": 0.25,
            "conditions": {"cascade_failure": True, "hazard_escalation": True},
            "key_drivers": ["Simultaneous failures", "Hazard spread"],
            "confidence": self._compute_confidence(0.9, 0.7)
        })
        
        if self.graphrag_service:
            try:
                res = await self.graphrag_service.answer(f"What are potential scenarios for {entity_type} {entity_id}?")
                for s in scenarios:
                    if hasattr(res, "citations"):
                        s["citations"] = res.citations
                    elif isinstance(res, dict) and "citations" in res:
                        s["citations"] = res["citations"]
            except Exception as e:
                log.warning(f"GraphRAG error: {e}")
                
        try:
            from app.modules.risk.application.services.risk_orchestration_service import RiskOrchestrationService
            if not self.risk_service:
                self.risk_service = RiskOrchestrationService()
        except ImportError:
            pass

        try:
            from app.modules.forecast.application.services.forecast_orchestration_service import ForecastOrchestrationService
            if not self.forecast_service:
                self.forecast_service = ForecastOrchestrationService()
        except ImportError:
            pass
            
        latency = (time.perf_counter() - t0) * 1000
        log.info(f"generate_scenarios completed in {latency:.2f}ms")
        
        return scenarios

    async def generate_custom_scenario(self, twin_id: str, twin_state: dict[str, Any], title: str, conditions: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
        return {
            "scenario_type": "CUSTOM",
            "title": title,
            "risk_delta": parameters.get("risk_delta", 0.0),
            "health_delta": parameters.get("health_delta", 0.0),
            "probability": parameters.get("probability", 0.1),
            "conditions": conditions,
            "key_drivers": parameters.get("key_drivers", []),
            "confidence": self._compute_confidence(0.8, 0.8)
        }
