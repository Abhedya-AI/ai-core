from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class InvestigationStatus(str, Enum):
    INITIATED = "INITIATED"
    EVIDENCE_COLLECTION = "EVIDENCE_COLLECTION"
    TIMELINE_CONSTRUCTION = "TIMELINE_CONSTRUCTION"
    HYPOTHESIS_GENERATION = "HYPOTHESIS_GENERATION"
    ROOT_CAUSE_ANALYSIS = "ROOT_CAUSE_ANALYSIS"
    RECOMMENDATION_GENERATION = "RECOMMENDATION_GENERATION"
    REVIEW = "REVIEW"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
    FAILED = "FAILED"

class EvidenceType(str, Enum):
    SENSOR_READING = "SENSOR_READING"
    VISION_DETECTION = "VISION_DETECTION"
    GRAPH_ENTITY = "GRAPH_ENTITY"
    GRAPHRAG_DOCUMENT = "GRAPHRAG_DOCUMENT"
    AUDIT_LOG = "AUDIT_LOG"
    MAINTENANCE_RECORD = "MAINTENANCE_RECORD"
    INCIDENT_REPORT = "INCIDENT_REPORT"
    SUPERVISOR_DECISION = "SUPERVISOR_DECISION"
    NOTIFICATION = "NOTIFICATION"
    WORKFLOW_EVENT = "WORKFLOW_EVENT"
    EXTERNAL_REPORT = "EXTERNAL_REPORT"

class EvidenceSource(str, Enum):
    SENSOR_INTELLIGENCE = "SENSOR_INTELLIGENCE"
    VISION_INTELLIGENCE = "VISION_INTELLIGENCE"
    KNOWLEDGE_GRAPH = "KNOWLEDGE_GRAPH"
    GRAPHRAG = "GRAPHRAG"
    WORKFLOW_ENGINE = "WORKFLOW_ENGINE"
    INCIDENT_MANAGEMENT = "INCIDENT_MANAGEMENT"
    AUDIT_FRAMEWORK = "AUDIT_FRAMEWORK"
    NOTIFICATION_FRAMEWORK = "NOTIFICATION_FRAMEWORK"
    SUPERVISOR = "SUPERVISOR"
    EXTERNAL = "EXTERNAL"

class HypothesisStatus(str, Enum):
    GENERATED = "GENERATED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"

class RecommendationType(str, Enum):
    IMMEDIATE_ACTION = "IMMEDIATE_ACTION"
    CORRECTIVE_ACTION = "CORRECTIVE_ACTION"
    PREVENTIVE_ACTION = "PREVENTIVE_ACTION"
    MAINTENANCE_TASK = "MAINTENANCE_TASK"
    INSPECTION_PLAN = "INSPECTION_PLAN"
    SHUTDOWN = "SHUTDOWN"
    EVACUATION = "EVACUATION"
    COMPLIANCE = "COMPLIANCE"
    LONG_TERM_IMPROVEMENT = "LONG_TERM_IMPROVEMENT"

class RecommendationPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class CausalRelationType(str, Enum):
    CAUSES = "CAUSES"
    CONTRIBUTES_TO = "CONTRIBUTES_TO"
    PRECEDES = "PRECEDES"
    TRIGGERED = "TRIGGERED"
    AFFECTS = "AFFECTS"
    MITIGATED_BY = "MITIGATED_BY"
    SUPPORTED_BY = "SUPPORTED_BY"

class ReportFormat(str, Enum):
    MARKDOWN = "MARKDOWN"
    JSON = "JSON"
    PDF = "PDF"

class RootCauseBaseModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)

class EvidenceWeight(RootCauseBaseModel):
    sensor_confidence: float = 0.0
    vision_confidence: float = 0.0
    graph_confidence: float = 0.0
    graphrag_confidence: float = 0.0
    historical_similarity: float = 0.0
    evidence_reliability: float = 0.0
    time_consistency: float = 0.0

class EvidenceScore(RootCauseBaseModel):
    overall_score: float
    breakdown: EvidenceWeight
    explanation: str = ""

class Evidence(RootCauseBaseModel):
    evidence_type: EvidenceType
    source: EvidenceSource
    title: str
    description: str
    confidence: float = 0.0
    reliability: float = 0.0
    severity: str = "LOW"
    timestamp: str
    location: str | None = None
    equipment_id: str | None = None
    worker_id: str | None = None
    zone_id: str | None = None
    incident_id: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)
    score: EvidenceScore | None = None
    tags: list[str] = Field(default_factory=list)

class TimelineEvent(RootCauseBaseModel):
    timestamp: str
    event_type: str
    source: EvidenceSource
    title: str
    description: str
    severity: str = "INFO"
    evidence_ids: list[str] = Field(default_factory=list)
    zone_id: str | None = None
    equipment_id: str | None = None
    worker_id: str | None = None
    is_anomalous: bool = False
    correlation_group: str | None = None

class TimelineSequence(RootCauseBaseModel):
    investigation_id: str
    events: list[TimelineEvent] = Field(default_factory=list)
    start_time: str | None = None
    end_time: str | None = None
    duration_seconds: float = 0.0
    missing_event_gaps: list[dict[str, Any]] = Field(default_factory=list)
    parallel_event_groups: list[list[str]] = Field(default_factory=list)

class CausalNode(RootCauseBaseModel):
    node_type: str
    entity_id: str
    label: str
    description: str = ""
    severity: str = "LOW"
    confidence: float = 0.0
    evidence_ids: list[str] = Field(default_factory=list)
    is_root_cause: bool = False
    is_contributing_factor: bool = False
    depth: int = 0

class CausalEdge(RootCauseBaseModel):
    source_node_id: str
    target_node_id: str
    relation_type: CausalRelationType
    confidence: float = 0.0
    evidence_ids: list[str] = Field(default_factory=list)
    description: str = ""

class CausalChain(RootCauseBaseModel):
    investigation_id: str
    nodes: list[CausalNode] = Field(default_factory=list)
    edges: list[CausalEdge] = Field(default_factory=list)
    root_cause_node_ids: list[str] = Field(default_factory=list)
    contributing_factor_node_ids: list[str] = Field(default_factory=list)
    max_depth: int = 0
    total_paths: int = 0

class HypothesisScore(RootCauseBaseModel):
    probability: float = 0.0
    supporting_evidence_count: int = 0
    contradicting_evidence_count: int = 0
    graph_support_score: float = 0.0
    historical_match_score: float = 0.0
    overall_confidence: float = 0.0

class Hypothesis(RootCauseBaseModel):
    title: str
    description: str
    status: HypothesisStatus = HypothesisStatus.GENERATED
    investigation_id: str
    score: HypothesisScore = Field(default_factory=HypothesisScore)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    affected_equipment_ids: list[str] = Field(default_factory=list)
    affected_worker_ids: list[str] = Field(default_factory=list)
    affected_zone_ids: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    rank: int = 0
    rejection_reason: str | None = None

class PrimaryCause(RootCauseBaseModel):
    hypothesis_id: str
    description: str
    confidence: float
    evidence_ids: list[str] = Field(default_factory=list)
    causal_chain_path: list[str] = Field(default_factory=list)

class SecondaryCause(RootCauseBaseModel):
    hypothesis_id: str | None = None
    description: str
    confidence: float
    evidence_ids: list[str] = Field(default_factory=list)

class ContributingFactor(RootCauseBaseModel):
    description: str
    factor_type: str
    confidence: float
    evidence_ids: list[str] = Field(default_factory=list)
    mitigation: str = ""

class Recommendation(RootCauseBaseModel):
    recommendation_type: RecommendationType
    priority: RecommendationPriority
    title: str
    description: str
    target_role: str = "Safety Officer"
    action_deadline_hours: int | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    policy_references: list[str] = Field(default_factory=list)
    estimated_cost: str | None = None
    equipment_ids: list[str] = Field(default_factory=list)
    zone_ids: list[str] = Field(default_factory=list)

class CorrectiveAction(Recommendation):
    corrective_measure: str = ""
    root_cause_reference: str = ""

class PreventiveAction(Recommendation):
    prevention_strategy: str = ""
    recurrence_risk: str = "MEDIUM"

class InvestigationSummary(RootCauseBaseModel):
    investigation_id: str
    incident_id: str
    status: InvestigationStatus
    primary_cause: PrimaryCause | None = None
    secondary_causes: list[SecondaryCause] = Field(default_factory=list)
    contributing_factors: list[ContributingFactor] = Field(default_factory=list)
    total_evidence_count: int = 0
    total_hypotheses: int = 0
    overall_confidence: float = 0.0
    duration_seconds: float = 0.0
    recommendations_count: int = 0

class InvestigationReport(RootCauseBaseModel):
    investigation_id: str
    title: str
    summary: InvestigationSummary
    evidence_list: list[Evidence] = Field(default_factory=list)
    timeline: TimelineSequence | None = None
    causal_graph: CausalChain | None = None
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    primary_cause: PrimaryCause | None = None
    secondary_causes: list[SecondaryCause] = Field(default_factory=list)
    contributing_factors: list[ContributingFactor] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    corrective_actions: list[CorrectiveAction] = Field(default_factory=list)
    preventive_actions: list[PreventiveAction] = Field(default_factory=list)
    graphrag_citations: list[str] = Field(default_factory=list)
    knowledge_graph_paths: list[list[str]] = Field(default_factory=list)
    confidence_explanation: str = ""
    alternative_hypotheses_rejected: list[dict[str, Any]] = Field(default_factory=list)
    lessons_learned: list[str] = Field(default_factory=list)
    format: ReportFormat = ReportFormat.JSON
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Investigation(RootCauseBaseModel):
    incident_id: str
    title: str
    description: str = ""
    status: InvestigationStatus = InvestigationStatus.INITIATED
    triggered_by: str = "system"
    assigned_to: str | None = None
    zone_id: str | None = None
    equipment_ids: list[str] = Field(default_factory=list)
    worker_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    hypothesis_ids: list[str] = Field(default_factory=list)
    recommendation_ids: list[str] = Field(default_factory=list)
    primary_cause: PrimaryCause | None = None
    secondary_causes: list[SecondaryCause] = Field(default_factory=list)
    contributing_factors: list[ContributingFactor] = Field(default_factory=list)
    overall_confidence: float = 0.0
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str | None = None
    duration_seconds: float = 0.0
    audit_trail: list[dict[str, Any]] = Field(default_factory=list)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEW: Enterprise Investigation Intelligence Models
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PatternType(str, Enum):
    GAS_LEAK = "GAS_LEAK"
    PRESSURE_FAILURE = "PRESSURE_FAILURE"
    BOILER_EXPLOSION = "BOILER_EXPLOSION"
    ELECTRICAL_FIRE = "ELECTRICAL_FIRE"
    WORKER_INJURY = "WORKER_INJURY"
    EQUIPMENT_FAILURE = "EQUIPMENT_FAILURE"
    CHEMICAL_SPILL = "CHEMICAL_SPILL"
    SENSOR_FAILURE = "SENSOR_FAILURE"
    VISION_FAILURE = "VISION_FAILURE"
    COMPOSITE_FAILURE = "COMPOSITE_FAILURE"
    CUSTOM = "CUSTOM"

class ScenarioType(str, Enum):
    MAINTENANCE_COMPLETED = "MAINTENANCE_COMPLETED"
    PPE_COMPLIANT = "PPE_COMPLIANT"
    EARLIER_DETECTION = "EARLIER_DETECTION"
    SENSOR_AVAILABLE = "SENSOR_AVAILABLE"
    EVACUATION_TRIGGERED = "EVACUATION_TRIGGERED"
    CUSTOM_INTERVENTION = "CUSTOM_INTERVENTION"

class FeedbackOutcome(str, Enum):
    EXECUTED = "EXECUTED"
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"
    IGNORED = "IGNORED"
    DELAYED = "DELAYED"
    PARTIAL = "PARTIAL"

class EvidenceFingerprint(RootCauseBaseModel):
    """Lightweight fingerprint for investigation similarity matching."""
    evidence_type_counts: dict[str, int] = Field(default_factory=dict)
    source_counts: dict[str, int] = Field(default_factory=dict)
    severity_counts: dict[str, int] = Field(default_factory=dict)
    zone_ids: list[str] = Field(default_factory=list)
    equipment_ids: list[str] = Field(default_factory=list)
    total_evidence: int = 0
    avg_confidence: float = 0.0

class LessonLearned(RootCauseBaseModel):
    investigation_id: str
    lesson_text: str
    lesson_category: str = "GENERAL"
    applies_to_zones: list[str] = Field(default_factory=list)
    applies_to_equipment_types: list[str] = Field(default_factory=list)
    applies_to_pattern_types: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    validated: bool = False
    tags: list[str] = Field(default_factory=list)

class FailurePattern(RootCauseBaseModel):
    name: str
    pattern_type: PatternType
    description: str
    trigger_conditions: list[str] = Field(default_factory=list)
    evidence_fingerprint: dict[str, Any] = Field(default_factory=dict)
    causal_chain_template: list[str] = Field(default_factory=list)
    prior_probability: float = 0.1
    historical_matches: int = 0
    confidence_score: float = 0.5
    version: int = 1
    is_seeded: bool = True
    required_evidence_types: list[str] = Field(default_factory=list)
    required_sources: list[str] = Field(default_factory=list)
    typical_severity: str = "HIGH"
    typical_zones: list[str] = Field(default_factory=list)
    typical_equipment_types: list[str] = Field(default_factory=list)

class PatternMatch(RootCauseBaseModel):
    pattern_id: str
    pattern_name: str
    pattern_type: PatternType
    similarity_score: float
    confidence: float
    matched_evidence_count: int
    missing_evidence_types: list[str] = Field(default_factory=list)
    match_explanation: str = ""

class InvestigationMemory(RootCauseBaseModel):
    investigation_id: str
    incident_id: str
    title: str
    root_cause_description: str = ""
    overall_confidence: float = 0.0
    duration_seconds: float = 0.0
    status: InvestigationStatus = InvestigationStatus.COMPLETED
    zone_ids: list[str] = Field(default_factory=list)
    equipment_ids: list[str] = Field(default_factory=list)
    worker_ids: list[str] = Field(default_factory=list)
    matched_pattern_ids: list[str] = Field(default_factory=list)
    lesson_ids: list[str] = Field(default_factory=list)
    recommendation_count: int = 0
    evidence_count: int = 0
    hypothesis_count: int = 0
    fingerprint: EvidenceFingerprint | None = None
    lessons_learned: list[str] = Field(default_factory=list)
    graphrag_citations: list[str] = Field(default_factory=list)
    kg_node_ids: list[str] = Field(default_factory=list)
    retrieved_count: int = 0
    completed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BayesianEvidenceBreakdown(RootCauseBaseModel):
    sensor_prior: float = 0.0
    sensor_likelihood: float = 0.0
    sensor_posterior: float = 0.0
    vision_prior: float = 0.0
    vision_likelihood: float = 0.0
    vision_posterior: float = 0.0
    graph_prior: float = 0.0
    graph_likelihood: float = 0.0
    graph_posterior: float = 0.0
    graphrag_prior: float = 0.0
    graphrag_likelihood: float = 0.0
    graphrag_posterior: float = 0.0
    historical_prior: float = 0.0
    historical_likelihood: float = 0.0
    historical_posterior: float = 0.0

class BayesianConfidenceReport(RootCauseBaseModel):
    investigation_id: str
    prior_probability: float
    likelihood: float
    posterior_probability: float
    evidence_breakdown: BayesianEvidenceBreakdown
    pattern_prior: float = 0.0
    historical_confidence: float = 0.0
    fused_confidence: float = 0.0
    explanation: str = ""
    evidence_count: int = 0
    convergence_score: float = 0.0

class CounterfactualScenario(RootCauseBaseModel):
    investigation_id: str
    scenario_type: ScenarioType
    intervention_description: str
    original_root_cause: str
    alternative_root_cause: str = ""
    risk_reduction_pct: float = 0.0
    prevented_incident_types: list[str] = Field(default_factory=list)
    alternative_timeline_events: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    counterfactual_evidence: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    impact_summary: str = ""

class InvestigationContext(RootCauseBaseModel):
    investigation_id: str
    incident_id: str
    sensor_readings_summary: list[dict[str, Any]] = Field(default_factory=list)
    vision_detections_summary: list[dict[str, Any]] = Field(default_factory=list)
    kg_entities: list[dict[str, Any]] = Field(default_factory=list)
    kg_relationships: list[dict[str, Any]] = Field(default_factory=list)
    rag_documents: list[str] = Field(default_factory=list)
    similar_incidents: list[str] = Field(default_factory=list)
    maintenance_records: list[dict[str, Any]] = Field(default_factory=list)
    active_policies: list[str] = Field(default_factory=list)
    applicable_regulations: list[str] = Field(default_factory=list)
    supervisor_decisions: list[dict[str, Any]] = Field(default_factory=list)
    historical_recommendations: list[str] = Field(default_factory=list)
    zone_risk_level: str = "UNKNOWN"
    equipment_health_summary: dict[str, Any] = Field(default_factory=dict)
    context_completeness_score: float = 0.0

class RecommendationFeedback(RootCauseBaseModel):
    recommendation_id: str
    investigation_id: str
    outcome: FeedbackOutcome
    impact_description: str = ""
    executed_by: str = ""
    executed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    effectiveness_score: float = 0.0
    cost_actual: str = ""
    lessons_generated: list[str] = Field(default_factory=list)
    pattern_confidence_delta: float = 0.0

class InvestigationAnalytics(RootCauseBaseModel):
    total_investigations: int = 0
    completed_investigations: int = 0
    avg_confidence: float = 0.0
    avg_duration_seconds: float = 0.0
    top_root_causes: list[dict[str, Any]] = Field(default_factory=list)
    top_patterns: list[dict[str, Any]] = Field(default_factory=list)
    zone_incident_counts: dict[str, int] = Field(default_factory=dict)
    equipment_incident_counts: dict[str, int] = Field(default_factory=dict)
    recommendation_effectiveness_rate: float = 0.0
    false_positive_rate: float = 0.0
    mttr_seconds: float = 0.0
    period_start: str = ""
    period_end: str = ""
