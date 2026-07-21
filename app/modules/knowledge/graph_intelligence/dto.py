"""
dto.py — Shared Intelligence Result DTOs for the Graph Intelligence Engine.

Ensures every algorithm and reasoning module returns a consistent structure
that can be easily composed, serialized, logged, or consumed by GraphRAG and AI Agents.
"""

from typing import Any

from pydantic import BaseModel, Field


class IntelligenceResult(BaseModel):
    """Unified result model returned by all graph intelligence algorithms."""

    algorithm: str = Field(..., description="Name of the executed algorithm or engine module")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score of the analysis")
    execution_time_ms: int = Field(default=0, ge=0, description="Execution duration in milliseconds")
    affected_nodes: list[str] = Field(default_factory=list, description="IDs of affected graph nodes")
    affected_edges: list[str] = Field(default_factory=list, description="Descriptions or IDs of traversed edges")
    evidence: list[str] = Field(default_factory=list, description="List of supporting graph evidence items")
    explanation: str = Field(default="", description="Human-readable natural language reasoning summary")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional algorithm-specific metrics")


class RiskAnalysisReport(BaseModel):
    """Report detailing risk propagation across graph nodes."""

    root_hazard_id: str
    max_risk_score: float
    propagated_risk_scores: dict[str, float] = Field(default_factory=dict)
    affected_node_ids: list[str] = Field(default_factory=list)
    risk_radius_hops: int = 0
    intelligence_result: IntelligenceResult


class CausalReport(BaseModel):
    """Report detailing root cause discovery and event timelines."""

    target_incident_id: str
    candidate_root_causes: list[str] = Field(default_factory=list)
    causal_path: list[str] = Field(default_factory=list)
    timeline_events: list[dict[str, Any]] = Field(default_factory=list)
    intelligence_result: IntelligenceResult


class DependencyReport(BaseModel):
    """Report detailing upstream and downstream asset/zone dependencies."""

    target_node_id: str
    upstream_dependencies: list[str] = Field(default_factory=list)
    downstream_impacts: list[str] = Field(default_factory=list)
    criticality_score: float = 0.0
    intelligence_result: IntelligenceResult
