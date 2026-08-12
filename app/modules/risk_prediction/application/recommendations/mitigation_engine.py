import uuid
from typing import List
from datetime import datetime, timezone
from app.core.logging import get_logger
from app.modules.risk_prediction.domain.enums import (
    RiskLevel, MitigationType, MitigationPriority, RiskType
)
from app.modules.risk_prediction.domain.models import (
    RiskAssessment, MitigationPlan, RiskRecommendation, RiskScore, RiskFactor
)
from app.modules.risk_prediction.application.graph.graph_risk_service import GraphRiskService, GraphContext

log = get_logger(__name__)

class MitigationEngine:
    def __init__(self, graph_service: GraphRiskService):
        self.graph_service = graph_service
    
    async def generate_plan(
        self,
        assessment: RiskAssessment,
        graphrag_context: str,
        graph_context: GraphContext,
    ) -> MitigationPlan:
        '''Generate a complete MitigationPlan for the given risk assessment.'''
        log.info(f"Generating mitigation plan for assessment {assessment.id}")
        
        recommendations = []
        requires_approval = assessment.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.EXTREME)
        
        if assessment.entity_type.name == "EQUIPMENT":
            recommendations.extend(self._generate_equipment_recommendations(assessment.current_score, assessment.factors, graph_context))
        elif assessment.entity_type.name == "WORKER":
            recommendations.extend(self._generate_worker_recommendations(assessment.current_score, assessment.factors))
        elif assessment.entity_type.name == "ZONE":
            recommendations.extend(self._generate_zone_recommendations(assessment.current_score, assessment.factors, graph_context))
        else:
            if assessment.risk_level == RiskLevel.EXTREME:
                recommendations.extend([
                    RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.EVACUATION, description="Immediate evacuation required", priority=MitigationPriority.IMMEDIATE, estimated_risk_reduction=0.8, action_items=[], assigned_to=None, due_at=None),
                    RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.SHUTDOWN, description="Emergency shutdown", priority=MitigationPriority.IMMEDIATE, estimated_risk_reduction=0.7, action_items=[], assigned_to=None, due_at=None),
                    RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.EMERGENCY_RESPONSE, description="Activate emergency response", priority=MitigationPriority.IMMEDIATE, estimated_risk_reduction=0.5, action_items=[], assigned_to=None, due_at=None)
                ])
            elif assessment.risk_level == RiskLevel.CRITICAL:
                recommendations.extend([
                    RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.SHUTDOWN, description="Controlled shutdown", priority=MitigationPriority.URGENT, estimated_risk_reduction=0.7, action_items=[], assigned_to=None, due_at=None),
                    RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.MAINTENANCE, description="Urgent maintenance", priority=MitigationPriority.URGENT, estimated_risk_reduction=0.4, action_items=[], assigned_to=None, due_at=None),
                    RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.WORKER_RELOCATION, description="Relocate workers", priority=MitigationPriority.URGENT, estimated_risk_reduction=0.6, action_items=[], assigned_to=None, due_at=None)
                ])
            elif assessment.risk_level == RiskLevel.MEDIUM:
                recommendations.extend([
                    RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.INSPECTION, description="Schedule inspection", priority=MitigationPriority.MEDIUM, estimated_risk_reduction=0.2, action_items=[], assigned_to=None, due_at=None),
                    RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.MONITORING_INCREASE, description="Increase monitoring frequency", priority=MitigationPriority.MEDIUM, estimated_risk_reduction=0.1, action_items=[], assigned_to=None, due_at=None)
                ])
            elif assessment.risk_level == RiskLevel.LOW:
                recommendations.extend([
                    RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.MONITORING_INCREASE, description="Routine monitoring", priority=MitigationPriority.LOW, estimated_risk_reduction=0.1, action_items=[], assigned_to=None, due_at=None)
                ])

        risk_types = [f.risk_type for f in assessment.factors] if assessment.factors else []
        if RiskType.FIRE in risk_types and not any(r.type == MitigationType.EVACUATION for r in recommendations):
             recommendations.extend([
                 RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.EVACUATION, description="Fire detected - evacuate", priority=MitigationPriority.IMMEDIATE, estimated_risk_reduction=0.8, action_items=[], assigned_to=None, due_at=None),
                 RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.EMERGENCY_RESPONSE, description="Call fire department", priority=MitigationPriority.IMMEDIATE, estimated_risk_reduction=0.6, action_items=[], assigned_to=None, due_at=None),
                 RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.SHUTDOWN, description="Shutdown affected area", priority=MitigationPriority.IMMEDIATE, estimated_risk_reduction=0.7, action_items=[], assigned_to=None, due_at=None)
             ])
        if RiskType.GAS_LEAK in risk_types and not any(r.type == MitigationType.EVACUATION for r in recommendations):
             recommendations.extend([
                 RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.EVACUATION, description="Gas leak - evacuate", priority=MitigationPriority.IMMEDIATE, estimated_risk_reduction=0.8, action_items=[], assigned_to=None, due_at=None),
                 RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.SHUTDOWN, description="Isolate gas source", priority=MitigationPriority.IMMEDIATE, estimated_risk_reduction=0.7, action_items=[], assigned_to=None, due_at=None),
                 RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.MONITORING_INCREASE, description="Monitor gas levels", priority=MitigationPriority.HIGH, estimated_risk_reduction=0.1, action_items=[], assigned_to=None, due_at=None)
             ])
             
        if graph_context.is_on_critical_path and assessment.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.EXTREME):
            if not any(r.type == MitigationType.INSPECTION for r in recommendations):
                recommendations.append(RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.INSPECTION, description="Critical path inspection", priority=MitigationPriority.URGENT, estimated_risk_reduction=0.2, action_items=[], assigned_to=None, due_at=None))
            if not any(r.type == MitigationType.SHUTDOWN for r in recommendations):
                recommendations.append(RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.SHUTDOWN, description="Critical path shutdown", priority=MitigationPriority.URGENT, estimated_risk_reduction=0.7, action_items=[], assigned_to=None, due_at=None))

        recommendations = self._enrich_with_graphrag(recommendations, graphrag_context)
        
        unique_recs = {r.type: r for r in recommendations}.values()
        final_recommendations = list(unique_recs)
        final_recommendations.sort(key=lambda r: r.estimated_risk_reduction, reverse=True)

        estimated_reduction = self._estimate_total_reduction(final_recommendations)
        
        return MitigationPlan(
            id=str(uuid.uuid4()),
            assessment_id=assessment.id,
            entity_id=assessment.entity_id,
            entity_type=assessment.entity_type,
            created_at=datetime.now(timezone.utc).isoformat(),
            recommendations=final_recommendations,
            estimated_total_reduction=estimated_reduction,
            requires_approval=requires_approval,
            status="DRAFT" if requires_approval else "AUTO_APPROVED"
        )
    
    def _generate_equipment_recommendations(
        self, risk_score: RiskScore, factors: List[RiskFactor], graph_ctx: GraphContext
    ) -> List[RiskRecommendation]:
        '''Rule-based equipment mitigation recommendations.'''
        recs = []
        if risk_score.probability > 0.7:
             recs.extend([
                RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.INSPECTION, description="Equipment inspection", priority=MitigationPriority.HIGH, estimated_risk_reduction=0.2, action_items=[], assigned_to=None, due_at=None),
                RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.MAINTENANCE, description="Equipment maintenance", priority=MitigationPriority.HIGH, estimated_risk_reduction=0.4, action_items=[], assigned_to=None, due_at=None),
                RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.MONITORING_INCREASE, description="Increase monitoring", priority=MitigationPriority.HIGH, estimated_risk_reduction=0.1, action_items=[], assigned_to=None, due_at=None)
             ])
        return recs
    
    def _generate_worker_recommendations(
        self, risk_score: RiskScore, factors: List[RiskFactor]
    ) -> List[RiskRecommendation]:
        '''Worker safety mitigation recommendations.'''
        recs = []
        if risk_score.probability > 0.7:
            recs.extend([
                RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.PPE_RECOMMENDATION, description="Check PPE compliance", priority=MitigationPriority.HIGH, estimated_risk_reduction=0.3, action_items=[], assigned_to=None, due_at=None),
                RiskRecommendation(id=str(uuid.uuid4()), type=MitigationType.WORKER_RELOCATION, description="Relocate worker", priority=MitigationPriority.HIGH, estimated_risk_reduction=0.6, action_items=[], assigned_to=None, due_at=None)
            ])
        return recs
    
    def _generate_zone_recommendations(
        self, risk_score: RiskScore, factors: List[RiskFactor], graph_ctx: GraphContext
    ) -> List[RiskRecommendation]:
        '''Zone-level mitigation recommendations.'''
        return []
    
    def _enrich_with_graphrag(
        self, recommendations: List[RiskRecommendation], graphrag_context: str
    ) -> List[RiskRecommendation]:
        '''Add GraphRAG citations to recommendations.'''
        if graphrag_context:
            for rec in recommendations:
                rec = RiskRecommendation(
                    id=rec.id, type=rec.type, description=f"{rec.description} [Context: {graphrag_context[:50]}]",
                    priority=rec.priority, estimated_risk_reduction=rec.estimated_risk_reduction,
                    action_items=rec.action_items, assigned_to=rec.assigned_to, due_at=rec.due_at
                )
        return recommendations
    
    def _estimate_total_reduction(
        self, recommendations: List[RiskRecommendation]
    ) -> float:
        '''Estimate combined risk reduction (not simply additive).'''
        product = 1.0
        for rec in recommendations:
            product *= (1.0 - rec.estimated_risk_reduction)
        return 1.0 - product
    
    def _compute_timeline(
        self, recommendations: List[RiskRecommendation], risk_level: RiskLevel
    ) -> str:
        '''Compute overall implementation timeline string.'''
        if risk_level in (RiskLevel.EXTREME, RiskLevel.CRITICAL):
            return "IMMEDIATE"
        return "WITHIN_24_HOURS"
