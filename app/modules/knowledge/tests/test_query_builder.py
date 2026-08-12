"""
test_query_builder.py — Unit Tests for GraphQueryBuilder.
"""
import pytest
from app.modules.knowledge.infrastructure.query_builder import GraphQueryBuilder


def test_match_basic_node():
    builder = GraphQueryBuilder()
    query, params = builder.node("Equipment", "e").build()
    assert "MATCH (e:Equipment)" in query
    assert "RETURN e" in query


def test_match_where_equality():
    builder = GraphQueryBuilder()
    query, params = builder.node("Sensor", "s").where(status="ACTIVE", unit="PSI").build()
    assert "MATCH (s:Sensor)" in query
    assert "WHERE s.status = $status_" in query
    assert "s.unit = $unit_" in query
    assert params["status_0"] == "ACTIVE"
    assert params["unit_1"] == "PSI"


def test_match_relationship():
    builder = GraphQueryBuilder()
    query, params = (
        builder.node("Sensor", "s")
        .related("MONITORS", direction="OUTGOING")
        .to("Equipment", "e")
        .build()
    )
    assert "MATCH (s:Sensor)-[r:MONITORS]->(e:Equipment)" in query
    assert "RETURN e" in query


def test_match_relationship_with_hops():
    builder = GraphQueryBuilder()
    query, params = (
        builder.node("Zone", "z")
        .relationship("CONNECTED_TO", alias="r", direction="BOTH", min_hops=1, max_hops=3)
        .to("Zone", "z2")
        .build()
    )
    assert "MATCH (z:Zone)-[r:CONNECTED_TO*1..3]-(z2:Zone)" in query


def test_where_in():
    builder = GraphQueryBuilder()
    query, params = (
        builder.node("Worker", "w")
        .where_in("role", ["OPERATOR", "TECHNICIAN"])
        .build()
    )
    assert "WHERE w.role IN $role_0" in query
    assert params["role_0"] == ["OPERATOR", "TECHNICIAN"]


def test_where_contains():
    builder = GraphQueryBuilder()
    query, params = (
        builder.node("Incident", "i")
        .where_contains("title", "leak", case_insensitive=True)
        .build()
    )
    assert "WHERE toLower(coalesce(i.title, '')) CONTAINS toLower($title_0)" in query
    assert params["title_0"] == "leak"


def test_order_by_skip_limit():
    builder = GraphQueryBuilder()
    query, params = (
        builder.node("Equipment", "e")
        .order_by("e.name", desc=True)
        .skip(10)
        .limit(20)
        .build()
    )
    assert "ORDER BY e.name DESC" in query
    assert "SKIP $__skip" in query
    assert "LIMIT $__limit" in query
    assert params["__skip"] == 10
    assert params["__limit"] == 20


def test_merge_builder():
    builder = GraphQueryBuilder()
    query, params = (
        builder.merge("Sensor", {"id": "S-01"}, {"name": "Temp 1", "status": "ACTIVE"})
        .build()
    )
    assert "MERGE (n:Sensor {id: $match_id_0})" in query
    assert "ON CREATE SET n += $set_props_1" in query
    assert "ON MATCH  SET n += $set_props_1" in query
    assert params["match_id_0"] == "S-01"
    assert params["set_props_1"]["name"] == "Temp 1"


def test_unwind_and_with():
    builder = GraphQueryBuilder()
    query, params = (
        builder.node("Worker", "w")
        .unwind("node_ids", "id")
        .build()
    )
    assert "MATCH (w:Worker)" in query
    assert "UNWIND $node_ids AS id" in query
