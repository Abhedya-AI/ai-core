"""
test_api_routes.py — Knowledge Graph API Integration & Route Unit Tests.
"""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status


def test_get_graph_nodes(client, auth_headers):
    response = client.get("/api/v1/graph/nodes", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0


def test_get_graph_subgraph(client, auth_headers):
    response = client.get("/api/v1/graph/subgraph/ZONE-B", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert data["center_node_id"] == "ZONE-B"
    assert "nodes" in data
    assert "edges" in data


def test_get_impact_path(client, auth_headers):
    response = client.get(
        "/api/v1/graph/paths/impact?source_id=TANK-T07&target_id=SOP-GH-04",
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert data["source_id"] == "TANK-T07"
    assert data["target_id"] == "SOP-GH-04"
    assert data["path_found"] is True


def test_post_graph_query(client, auth_headers):
    payload = {"query": "MATCH (n:Zone) RETURN n", "limit": 10}
    response = client.post("/api/v1/graph/query", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert "nodes" in data
    assert "edges" in data


def test_get_ontology(client, auth_headers):
    with patch(
        "app.modules.knowledge.infrastructure.repositories.ontology_repository.OntologyRepository.get_schema_summary",
        new_callable=AsyncMock,
    ) as mock_summary:
        mock_summary.return_value = {"entity_count": 30, "relationships": ["MONITORS"]}
        response = client.get("/api/v1/graph/ontology", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert "entity_count" in data


def test_post_analytics(client, auth_headers):
    with patch(
        "app.modules.knowledge.services.graph_analytics_service.GraphAnalyticsService.run_analytics",
        new_callable=AsyncMock,
    ) as mock_run:
        from app.modules.knowledge.application.dto.analytics_dto import AnalyticsResult, CentralityResult, NodeScore
        mock_run.return_value = AnalyticsResult(
            algorithm="degree",
            centrality=CentralityResult(
                algorithm="centrality_degree",
                entity_type=None,
                total_nodes=1,
                results=[NodeScore(node_id="eq-1", label="Equipment", score=5.0, rank=1)],
                execution_time_ms=1.2,
            ),
        )
        payload = {"algorithm": "degree"}
        response = client.post("/api/v1/graph/analytics", json=payload, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["algorithm"] == "degree"
        assert data["centrality"]["results"][0]["node_id"] == "eq-1"


def test_post_search(client, auth_headers):
    with patch(
        "app.modules.knowledge.services.graph_search_service.GraphSearchService.search",
        new_callable=AsyncMock,
    ) as mock_search:
        from app.modules.knowledge.application.dto.search_dto import SearchHit, SearchResult
        mock_search.return_value = SearchResult(
            query="boiler",
            total=1,
            offset=0,
            limit=20,
            hits=[SearchHit(node_id="eq-1", label="Equipment", name="Boiler 3")],
            execution_time_ms=0.5,
            search_type="text",
        )
        payload = {"query": "boiler", "search_type": "text"}
        response = client.post("/api/v1/graph/search", json=payload, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["query"] == "boiler"
        assert data["hits"][0]["node_id"] == "eq-1"
