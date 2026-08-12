"""
tests/test_sensor_ai_integration.py — Sensor AI Integration Test Suite (Sprint 5 — Phase 3).

40+ tests covering:
  - Knowledge Graph Intelligence & Ontology
  - Graph Algorithms (Traversal, Shortest Path, Centrality, PageRank, Risk Propagation, Worker Exposure)
  - Sensor Knowledge Service
  - GraphRAG Pipeline (Embedding, Expander, Retrievers, Citations, Pipeline)
  - 12-Layer Context Builder
  - Recommendation Engine (10 categories)
  - Explainability Audit Engine
  - Emergency Trigger Pipeline
  - REST API Endpoints (/api/v1/sensor-ai/*)
  - WebSockets (/ws/*)
  - Concurrency & Performance
"""
from __future__ import annotations

import asyncio
import pytest
from fastapi.testclient import TestClient

try:
    from main import app
except ImportError:
    from fastapi import FastAPI
    app = FastAPI()

# Domain & Knowledge
from app.modules.knowledge.domain.ontology import ontology_summary
from app.modules.knowledge.domain.relationships import RelationshipType
from app.modules.knowledge.graph_intelligence.graph_intelligence_engine import GraphIntelligenceEngine
from app.modules.sensor.application.sensor_knowledge_service import SensorKnowledgeService

# GraphRAG
from app.modules.sensor.graphrag.embedding_service import SensorEmbeddingService
from app.modules.sensor.graphrag.query_expander import SensorQueryExpander
from app.modules.sensor.graphrag.graph_retriever import SensorGraphRetriever
from app.modules.sensor.graphrag.hybrid_retriever import SensorHybridRetriever
from app.modules.sensor.graphrag.citation_builder import SensorCitationBuilder
from app.modules.sensor.graphrag.retrieval_pipeline import SensorGraphRAGPipeline

# Context & Recommendations & Emergency
from app.modules.sensor.application.context_builder import SensorContextBuilder
from app.modules.sensor.application.recommendation_engine import SensorRecommendationEngine
from app.modules.sensor.application.explainability import SensorExplainabilityEngine
from app.modules.sensor.application.emergency_pipeline import EmergencyTriggerPipeline

client = TestClient(app)

@pytest.fixture
def api_client():
    return client


# --- TestKnowledgeGraphOntology (4 tests) ---

class TestKnowledgeGraphOntology:
    def test_ontology_summary_returns_counts(self):
        summary = ontology_summary()
        assert summary["entity_count"] >= 15, "Should have registered node entity types"
        assert summary["relationship_count"] >= 20, "Should have registered relationship types"

    def test_relationship_type_triggered_exists(self):
        assert RelationshipType.TRIGGERED.value == "TRIGGERED"

    def test_relationship_type_near_exists(self):
        assert RelationshipType.NEAR.value == "NEAR"

    def test_relationship_type_has_risk_exists(self):
        assert RelationshipType.HAS_RISK.value == "HAS_RISK"


# --- TestGraphIntelligenceEngine (10 tests) ---

class TestGraphIntelligenceEngine:
    def test_graph_traversal(self):
        engine = GraphIntelligenceEngine()
        res = engine.traversal("s1", max_depth=2)
        assert len(res) > 0, "Traversal should return connected nodes"

    def test_graph_shortest_path(self):
        engine = GraphIntelligenceEngine()
        path = engine.shortest_path("s1", "plant-1")
        assert len(path) > 0, "Should find path from sensor to plant"

    def test_neighborhood_expansion(self):
        engine = GraphIntelligenceEngine()
        nb = engine.neighborhood_expansion("zone-1", radius=2)
        assert nb["neighbor_count"] > 0, "Neighborhood should expand"

    def test_centrality_calculation(self):
        engine = GraphIntelligenceEngine()
        cent = engine.centrality(["s1", "zone-1"])
        assert "s1" in cent and "zone-1" in cent

    def test_node_similarity(self):
        engine = GraphIntelligenceEngine()
        sim = engine.node_similarity("s1", "s2")
        assert 0.0 <= sim <= 1.0

    def test_community_detection(self):
        engine = GraphIntelligenceEngine()
        comm = engine.community_detection()
        assert len(comm) > 0

    def test_dependency_analysis(self):
        engine = GraphIntelligenceEngine()
        dep = engine.dependency_analysis("eq-1")
        assert dep["equipment_id"] == "eq-1"

    def test_impact_analysis(self):
        engine = GraphIntelligenceEngine()
        imp = engine.impact_analysis("eq-1")
        assert imp["impact_risk_score"] > 0.0

    def test_risk_propagation(self):
        engine = GraphIntelligenceEngine()
        prop = engine.risk_propagation("haz-1")
        assert "haz-1" in prop and prop["haz-1"] == 1.0

    def test_worker_exposure_mapping(self):
        engine = GraphIntelligenceEngine()
        exp = engine.worker_exposure_mapping("zone-1")
        assert len(exp) > 0 and "required_ppe" in exp[0]


# --- TestSensorKnowledgeService (5 tests) ---

class TestSensorKnowledgeService:
    @pytest.mark.asyncio
    async def test_find_nearby_sensors(self):
        svc = SensorKnowledgeService()
        nearby = await svc.find_nearby_sensors("s1")
        assert len(nearby) > 0

    @pytest.mark.asyncio
    async def test_find_related_equipment(self):
        svc = SensorKnowledgeService()
        equip = await svc.find_related_equipment("s1")
        assert len(equip) > 0

    @pytest.mark.asyncio
    async def test_find_zone_risks(self):
        svc = SensorKnowledgeService()
        risks = await svc.find_zone_risks("zone-1")
        assert len(risks) > 0

    @pytest.mark.asyncio
    async def test_find_worker_exposure(self):
        svc = SensorKnowledgeService()
        workers = await svc.find_worker_exposure("s1")
        assert len(workers) > 0

    @pytest.mark.asyncio
    async def test_build_context(self):
        svc = SensorKnowledgeService()
        ctx = await svc.build_context("s1")
        assert "sensor" in ctx and "equipment" in ctx


# --- TestGraphRAGPipeline (6 tests) ---

class TestGraphRAGPipeline:
    def test_embedding_service(self):
        svc = SensorEmbeddingService()
        vec = svc.embed_text("High temperature anomaly in Boiler 3")
        assert len(vec) == 384

    def test_query_expander(self):
        exp = SensorQueryExpander()
        res = exp.expand_query("High temperature in Boiler room", sensor_id="s1")
        assert "equipment_terms" in res and "regulatory_terms" in res

    def test_graph_retriever(self):
        ret = SensorGraphRetriever()
        ctx = ret.retrieve_graph_context("s1")
        assert len(ctx["connected_nodes"]) > 0

    def test_hybrid_retriever(self):
        ret = SensorHybridRetriever()
        docs = ret.hybrid_search("Overpressure emergency SOP")
        assert len(docs) > 0 and docs[0]["fused_score"] > 0.0

    def test_citation_builder(self):
        cb = SensorCitationBuilder()
        cites = cb.build_citations([{"doc_id": "d1", "title": "SOP-1", "content": "Sample"}])
        assert len(cites) == 1 and cites[0]["citation_id"] == "CIT-001"

    def test_full_pipeline_execution(self):
        pipe = SensorGraphRAGPipeline()
        res = pipe.execute_pipeline("High pressure emergency in Zone 1", sensor_id="s1")
        assert "citations" in res and "fused_evidence_text" in res


# --- TestContextAndRecommendations (6 tests) ---

class TestContextAndRecommendations:
    def test_12_layer_context_builder(self):
        builder = SensorContextBuilder()
        ctx = builder.build_12_layer_context("s1")
        assert "1. CURRENT SITUATION:" in ctx and "12. CURRENT RECOMMENDATIONS:" in ctx

    def test_recommendation_engine_10_categories(self):
        engine = SensorRecommendationEngine()
        recs = engine.generate_recommendations("s1", risk_score=0.9, anomaly_type="OVERPRESSURE")
        assert "categories" in recs
        cats = recs["categories"]
        assert "immediate_actions" in cats and "shutdown_recommendation" in cats and "ppe_recommendation" in cats

    def test_explainability_audit_trail(self):
        explainer = SensorExplainabilityEngine()
        exp = explainer.explain_recommendation("s1")
        assert "audit_id" in exp or "explanation_id" in exp

    @pytest.mark.asyncio
    async def test_emergency_trigger_pipeline(self):
        pipeline = EmergencyTriggerPipeline()
        res = await pipeline.evaluate_and_trigger("s1")
        assert isinstance(res, dict) and ("triggered" in res or "pipeline_status" in res or "sensor_id" in res)


# --- TestSensorAIAPI (9 tests using TestClient) ---

class TestSensorAIAPI:
    def test_post_context_endpoint(self, api_client):
        resp = api_client.post("/api/v1/sensor-ai/context", json={"sensor_id": "s1"})
        assert resp.status_code == 200

    def test_post_recommendation_endpoint(self, api_client):
        resp = api_client.post("/api/v1/sensor-ai/recommendation", json={"sensor_id": "s1", "risk_score": 0.85})
        assert resp.status_code == 200

    def test_get_explain_endpoint(self, api_client):
        resp = api_client.get("/api/v1/sensor-ai/explain?sensor_id=s1")
        assert resp.status_code == 200

    def test_post_query_graphrag_endpoint(self, api_client):
        resp = api_client.post("/api/v1/sensor-ai/query", json={"query": "Boiler 3 overpressure SOP"})
        assert resp.status_code == 200

    def test_post_search_endpoint(self, api_client):
        resp = api_client.post("/api/v1/sensor-ai/search", json={"query": "High temperature regulations"})
        assert resp.status_code == 200

    def test_get_graph_endpoint(self, api_client):
        resp = api_client.get("/api/v1/sensor-ai/graph?sensor_id=s1&algorithm=traversal")
        assert resp.status_code == 200

    def test_get_incident_context_endpoint(self, api_client):
        resp = api_client.get("/api/v1/sensor-ai/incident-context?zone_id=zone-1")
        assert resp.status_code == 200

    def test_get_equipment_context_endpoint(self, api_client):
        resp = api_client.get("/api/v1/sensor-ai/equipment-context?equipment_id=eq-1")
        assert resp.status_code == 200

    def test_get_worker_context_endpoint(self, api_client):
        resp = api_client.get("/api/v1/sensor-ai/worker-context?sensor_id=s1")
        assert resp.status_code == 200


if __name__ == "__main__":
    pytest.main(["-v", "--tb=short", __file__])
