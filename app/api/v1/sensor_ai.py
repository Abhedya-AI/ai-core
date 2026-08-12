"""
app/api/v1/sensor_ai.py — Sensor AI Integration REST API.

Tag: Sensor AI
Prefix: /sensor-ai

Provides contextual reasoning, GraphRAG queries, recommendation engines,
explainability audit trails, and emergency decision intelligence.
"""
from __future__ import annotations
import uuid
from typing import Optional, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Query, Path, Body
from pydantic import BaseModel, Field

from app.api.responses import StandardResponse, make_response
from app.api.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger

log = get_logger("api.v1.sensor_ai")

router = APIRouter(prefix="/sensor-ai", tags=["Sensor AI"])


# ── Request Models ─────────────────────────────────────────────────────────────

class ContextRequest(BaseModel):
    sensor_id: str = Field(..., description="Target sensor ID")
    value: Optional[float] = Field(None, description="Current value override")
    zone_id: Optional[str] = Field(None, description="Zone ID override")

class RecommendationRequest(BaseModel):
    sensor_id: str = Field(..., description="Target sensor ID")
    risk_score: float = Field(0.5, ge=0.0, le=1.0, description="Risk score from 0 to 1")
    anomaly_type: Optional[str] = Field(None, description="Type of anomaly if present")
    context_override: Optional[str] = Field(None, description="Optional extra context")

class GraphRAGQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query string")
    sensor_id: Optional[str] = Field(None, description="Target sensor ID")
    zone_id: Optional[str] = Field(None, description="Target zone ID")
    top_k: int = Field(5, ge=1, le=20, description="Max search results")

class HybridSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    vector_weight: float = Field(0.5, ge=0.0, le=1.0, description="Weight for vector search")
    graph_weight: float = Field(0.5, ge=0.0, le=1.0, description="Weight for graph search")
    limit: int = Field(10, ge=1, le=50)


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/context", response_model=StandardResponse, summary="Get Sensor AI 12-Layer Context")
async def get_sensor_context(request: ContextRequest):
    """
    Build 12-Layer natural language situational context for LLM reasoning.
    """
    try:
        from app.modules.sensor.application.context_builder import SensorContextBuilder
        builder = SensorContextBuilder()
        context_str = builder.build_12_layer_context(
            sensor_id=request.sensor_id,
            zone_id=request.zone_id
        )
        return make_response(
            data={"sensor_id": request.sensor_id, "context": context_str, "timestamp": datetime.now(timezone.utc).isoformat()},
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to build context for {request.sensor_id}: {str(e)}")
        raise ValidationError(message=f"Context generation failed: {str(e)}")


@router.post("/recommendation", response_model=StandardResponse, summary="Get Sensor AI Recommendations")
async def get_sensor_recommendation(request: RecommendationRequest):
    """
    Generate 10 categories of industrial safety recommendations.
    """
    try:
        from app.modules.sensor.application.recommendation_engine import SensorRecommendationEngine
        engine = SensorRecommendationEngine()
        recs = engine.generate_recommendations(
            sensor_id=request.sensor_id,
            risk_score=request.risk_score,
            anomaly_type=request.anomaly_type
        )
        return make_response(
            data=recs,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to generate recommendations for {request.sensor_id}: {str(e)}")
        raise ValidationError(message=f"Recommendation generation failed: {str(e)}")


@router.get("/explain", response_model=StandardResponse, summary="Explain AI Recommendation Audit Trail")
async def explain_recommendation(sensor_id: str = Query(..., description="Sensor ID")):
    """
    Generate transparent audit trail explaining AI reasoning and citations.
    """
    try:
        from app.modules.sensor.application.explainability import SensorExplainabilityEngine
        explainer = SensorExplainabilityEngine()
        explanation = explainer.explain_recommendation(sensor_id=sensor_id)
        return make_response(
            data=explanation,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to explain recommendations for {sensor_id}: {str(e)}")
        raise ValidationError(message=f"Explainability failed: {str(e)}")


@router.post("/query", response_model=StandardResponse, summary="GraphRAG Pipeline Natural Language Query")
async def query_sensor_graphrag(request: GraphRAGQueryRequest):
    """
    Execute full GraphRAG pipeline (Query Expander → Retrievers → Hybrid Fusion → Citations).
    """
    try:
        from app.modules.sensor.graphrag.retrieval_pipeline import SensorGraphRAGPipeline
        pipeline = SensorGraphRAGPipeline()
        result = pipeline.execute_pipeline(
            query=request.query,
            sensor_id=request.sensor_id,
            zone_id=request.zone_id,
            top_k=request.top_k
        )
        return make_response(
            data=result,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed GraphRAG query: {str(e)}")
        raise ValidationError(message=f"GraphRAG query failed: {str(e)}")


@router.post("/search", response_model=StandardResponse, summary="Hybrid Vector & Graph Search")
async def search_sensor_knowledge(request: HybridSearchRequest):
    """
    Execute hybrid vector similarity + graph distance search.
    """
    try:
        from app.modules.sensor.graphrag.hybrid_retriever import SensorHybridRetriever
        retriever = SensorHybridRetriever()
        results = retriever.hybrid_search(
            query=request.query,
            top_k=request.limit
        )
        return make_response(
            data=results,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed hybrid search: {str(e)}")
        raise ValidationError(message=f"Search failed: {str(e)}")


@router.get("/graph", response_model=StandardResponse, summary="Knowledge Graph Topology & Algorithms")
async def get_graph_intelligence(
    sensor_id: Optional[str] = Query(None, description="Sensor ID"),
    algorithm: str = Query("traversal", description="Graph algorithm: traversal, page_rank, centrality, impact")
):
    """
    Run graph intelligence algorithm over industrial topology.
    """
    try:
        from app.modules.knowledge.graph_intelligence.graph_intelligence_engine import GraphIntelligenceEngine
        engine = GraphIntelligenceEngine()
        if algorithm == "traversal" and sensor_id:
            res = engine.traversal(sensor_id)
        elif algorithm == "centrality":
            res = engine.centrality([sensor_id] if sensor_id else ["s1", "s2"])
        else:
            res = engine.neighborhood_expansion(sensor_id or "s1")

        return make_response(
            data={"algorithm": algorithm, "result": res},
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed graph algorithm {algorithm}: {str(e)}")
        raise ValidationError(message=f"Graph execution failed: {str(e)}")


@router.get("/incident-context", response_model=StandardResponse, summary="Historical Incident Context")
async def get_incident_context(
    zone_id: Optional[str] = Query(None, description="Zone ID"),
    equipment_id: Optional[str] = Query(None, description="Equipment ID")
):
    """
    Retrieve historical incident context and parallel failure patterns.
    """
    try:
        from app.modules.sensor.application.sensor_knowledge_service import SensorKnowledgeService
        svc = SensorKnowledgeService()
        incidents = await svc.find_previous_incidents(zone_id=zone_id, equipment_id=equipment_id)
        return make_response(
            data=incidents,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to get incident context: {str(e)}")
        raise ValidationError(message=f"Incident context failed: {str(e)}")


@router.get("/equipment-context", response_model=StandardResponse, summary="Equipment Dependency & Risk")
async def get_equipment_context(equipment_id: str = Query(..., description="Equipment ID")):
    """
    Retrieve equipment dependency chain and risk propagation context.
    """
    try:
        from app.modules.sensor.application.sensor_knowledge_service import SensorKnowledgeService
        svc = SensorKnowledgeService()
        deps = await svc.find_dependency_chain(equipment_id=equipment_id)
        return make_response(
            data=deps,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to get equipment context: {str(e)}")
        raise ValidationError(message=f"Equipment context failed: {str(e)}")


@router.get("/worker-context", response_model=StandardResponse, summary="Worker Exposure & PPE Mapping")
async def get_worker_context(
    sensor_id: Optional[str] = Query(None, description="Sensor ID"),
    zone_id: Optional[str] = Query(None, description="Zone ID")
):
    """
    Retrieve worker proximity exposure mapping and PPE requirements.
    """
    try:
        from app.modules.sensor.application.sensor_knowledge_service import SensorKnowledgeService
        svc = SensorKnowledgeService()
        exposure = await svc.find_worker_exposure(target_id=sensor_id or zone_id or "zone-1")
        return make_response(
            data=exposure,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to get worker context: {str(e)}")
        raise ValidationError(message=f"Worker context failed: {str(e)}")
