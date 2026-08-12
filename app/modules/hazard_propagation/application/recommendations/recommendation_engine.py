from __future__ import annotations

from app.core.logging import get_logger

log = get_logger(__name__)

class HazardRecommendationEngine:
    def __init__(self, graphrag_service=None, knowledge_service=None) -> None:
        self.graphrag_service = graphrag_service
        self.knowledge_service = knowledge_service

    async def generate_recommendations(
        self, propagation_id: str, hazard_type: str, severity: str, 
        exposure_assessment: dict, containment_plan: dict, cascade_risks: list[dict], context: dict
    ) -> list[dict]:
        exp_score = exposure_assessment.get("max_exposure_level", 0.0)
        recs = self._apply_hazard_rules(hazard_type, severity, exp_score)
        
        recs = await self._enrich_with_graphrag(recs, hazard_type, context)
        recs = self.prioritize_recommendations(recs, severity)
        
        for i, r in enumerate(recs):
            r["recommendation_id"] = f"REC-{propagation_id}-{i+1}"
            r["propagation_id"] = propagation_id
            
        return recs

    def _apply_hazard_rules(self, hazard_type: str, severity: str, exposure_score: float) -> list[dict]:
        recs = []
        if severity in ("CATASTROPHIC", "CRITICAL"):
            recs.append({"recommendation_type": "IMMEDIATE_EVACUATION", "priority": "IMMEDIATE", "title": "Evacuate All Personnel", "description": "Initiate full site evacuation.", "rationale": "Severity is critical.", "estimated_effectiveness": 0.9, "time_to_implement_minutes": 5, "operators_required": 5, "resources": ["Alarms"]})
            recs.append({"recommendation_type": "EMERGENCY_SERVICES", "priority": "IMMEDIATE", "title": "Call Emergency Services", "description": "Contact fire and hazmat.", "rationale": "External help needed.", "estimated_effectiveness": 0.85, "time_to_implement_minutes": 2, "operators_required": 1, "resources": ["Phone"]})
            recs.append({"recommendation_type": "EQUIPMENT_SHUTDOWN", "priority": "IMMEDIATE", "title": "Emergency Shutdown", "description": "Trigger ESD.", "rationale": "Prevent cascade.", "estimated_effectiveness": 0.8, "time_to_implement_minutes": 1, "operators_required": 1, "resources": ["ESD System"]})
        elif severity == "MAJOR":
            recs.append({"recommendation_type": "PARTIAL_EVACUATION", "priority": "URGENT", "title": "Evacuate Zone", "description": "Evacuate affected and adjacent zones.", "rationale": "High localized risk.", "estimated_effectiveness": 0.8, "time_to_implement_minutes": 10, "operators_required": 3, "resources": []})
            recs.append({"recommendation_type": "VALVE_ISOLATION", "priority": "URGENT", "title": "Isolate Flow", "description": "Close all boundary valves.", "rationale": "Stop feed to hazard.", "estimated_effectiveness": 0.85, "time_to_implement_minutes": 15, "operators_required": 2, "resources": []})
            if hazard_type == "FIRE":
                recs.append({"recommendation_type": "FIRE_SUPPRESSION", "priority": "URGENT", "title": "Activate Fire Systems", "description": "Start deluge or foam.", "rationale": "Fire containment.", "estimated_effectiveness": 0.75, "time_to_implement_minutes": 5, "operators_required": 1, "resources": []})
        elif severity == "MODERATE":
            recs.append({"recommendation_type": "MONITORING_INCREASE", "priority": "HIGH", "title": "Increase Monitoring", "description": "Deploy extra sensors.", "rationale": "Track hazard spread.", "estimated_effectiveness": 0.6, "time_to_implement_minutes": 30, "operators_required": 1, "resources": []})
            recs.append({"recommendation_type": "BARRIER_DEPLOYMENT", "priority": "HIGH", "title": "Deploy Barriers", "description": "Setup physical barriers.", "rationale": "Limit spread.", "estimated_effectiveness": 0.65, "time_to_implement_minutes": 45, "operators_required": 2, "resources": []})
            recs.append({"recommendation_type": "VENTILATION_INCREASE", "priority": "HIGH", "title": "Adjust Ventilation", "description": "Maximize exhaust.", "rationale": "Clear air.", "estimated_effectiveness": 0.7, "time_to_implement_minutes": 10, "operators_required": 1, "resources": []})
        else:
            recs.append({"recommendation_type": "MONITORING_INCREASE", "priority": "MEDIUM", "title": "Continue Monitoring", "description": "Maintain normal monitoring.", "rationale": "Risk is low.", "estimated_effectiveness": 0.5, "time_to_implement_minutes": 0, "operators_required": 0, "resources": []})
        return recs

    async def _enrich_with_graphrag(self, recommendations: list[dict], hazard_type: str, context: dict) -> list[dict]:
        if not self.graphrag_service:
            return recommendations
            
        enriched = []
        for r in recommendations:
            r_copy = dict(r)
            try:
                pass
            except Exception as e:
                log.warning(f"GraphRAG enrichment error: {e}")
            enriched.append(r_copy)
        return enriched

    def prioritize_recommendations(self, recs: list[dict], severity: str) -> list[dict]:
        priority_map = {"IMMEDIATE": 1, "URGENT": 2, "HIGH": 3, "MEDIUM": 4, "LOW": 5}
        return sorted(recs, key=lambda x: (priority_map.get(x.get("priority", "MEDIUM"), 99), -x.get("estimated_effectiveness", 0.0)))

    def compute_recommendation_effectiveness(self, rec_type: str, hazard_type: str, intensity: float) -> float:
        lookup = {
            "IMMEDIATE_EVACUATION": 0.9,
            "VALVE_ISOLATION": 0.85,
            "EMERGENCY_SERVICES": 0.85,
            "EQUIPMENT_SHUTDOWN": 0.8,
            "PARTIAL_EVACUATION": 0.8,
            "FIRE_SUPPRESSION": 0.75,
            "VENTILATION_INCREASE": 0.7,
            "BARRIER_DEPLOYMENT": 0.65,
            "MONITORING_INCREASE": 0.5
        }
        return float(lookup.get(rec_type, 0.5))
