"""
repositories/ontology_repository.py — Ontology and Schema Management Repository.

Manages Neo4j constraints, indexes, and schema introspection.
Idempotent DDL operations for production environment stability.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.neo4j.session import get_neo4j_session
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository

log = get_logger("knowledge.repository.ontology")


class OntologyRepository(BaseNeo4jRepository):
    """Repository for managing Neo4j constraints, indexes, and schema metadata."""

    async def create_unique_constraint(
        self,
        label: str,
        property_name: str = "id",
    ) -> bool:
        """Create a unique constraint on label.property_name. Idempotent."""
        constraint_name = f"{label.lower()}_{property_name}_unique"
        cypher = f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS FOR (n:{label}) REQUIRE n.{property_name} IS UNIQUE"
        try:
            async with get_neo4j_session() as session:
                await session.run(cypher)
            log.info(f"Unique constraint created/verified: {constraint_name}")
            return True
        except Exception as exc:
            log.error(f"Failed to create constraint {constraint_name}: {exc}")
            return False

    async def create_fulltext_index(
        self,
        label: str,
        properties: list[str] | None = None,
        index_name: str | None = None,
    ) -> bool:
        """Create a full-text search index. Idempotent."""
        idx_name = index_name or f"{label.lower()}_fulltext"
        props = properties or ["name", "title", "code", "description"]
        props_str = ", ".join(f"n.{p}" for p in props)
        cypher = f"CREATE FULLTEXT INDEX {idx_name} IF NOT EXISTS FOR (n:{label}) ON EACH [{props_str}]"
        try:
            async with get_neo4j_session() as session:
                await session.run(cypher)
            log.info(f"Full-text index created/verified: {idx_name}")
            return True
        except Exception as exc:
            log.error(f"Failed to create fulltext index {idx_name}: {exc}")
            return False

    async def list_constraints(self) -> list[dict[str, Any]]:
        """List all constraints in the Neo4j database."""
        cypher = "SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties RETURN name, type, labelsOrTypes, properties"
        try:
            records = await self.execute_query(cypher)
            return [
                {
                    "name": rec.get("name"),
                    "type": rec.get("type"),
                    "labels": rec.get("labelsOrTypes"),
                    "properties": rec.get("properties"),
                }
                for rec in records
            ]
        except Exception as exc:
            log.error(f"Failed to list constraints: {exc}")
            return []

    async def list_indexes(self) -> list[dict[str, Any]]:
        """List all indexes in the Neo4j database."""
        cypher = "SHOW INDEXES YIELD name, type, labelsOrTypes, properties, state RETURN name, type, labelsOrTypes, properties, state"
        try:
            records = await self.execute_query(cypher)
            return [
                {
                    "name": rec.get("name"),
                    "type": rec.get("type"),
                    "labels": rec.get("labelsOrTypes"),
                    "properties": rec.get("properties"),
                    "state": rec.get("state"),
                }
                for rec in records
            ]
        except Exception as exc:
            log.error(f"Failed to list indexes: {exc}")
            return []

    async def drop_constraint(self, constraint_name: str) -> bool:
        """Drop a constraint by name if it exists."""
        cypher = f"DROP CONSTRAINT {constraint_name} IF EXISTS"
        try:
            async with get_neo4j_session() as session:
                await session.run(cypher)
            log.info(f"Dropped constraint: {constraint_name}")
            return True
        except Exception as exc:
            log.error(f"Failed to drop constraint {constraint_name}: {exc}")
            return False

    async def get_all_labels(self) -> list[str]:
        """Return all distinct node labels in the graph."""
        cypher = "CALL db.labels() YIELD label RETURN label ORDER BY label"
        try:
            records = await self.execute_query(cypher)
            return [rec["label"] for rec in records if rec.get("label")]
        except Exception as exc:
            log.error(f"Failed to fetch db.labels: {exc}")
            return []

    async def get_all_relationship_types(self) -> list[str]:
        """Return all distinct relationship types in the graph."""
        cypher = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType"
        try:
            records = await self.execute_query(cypher)
            return [rec["relationshipType"] for rec in records if rec.get("relationshipType")]
        except Exception as exc:
            log.error(f"Failed to fetch db.relationshipTypes: {exc}")
            return []

    async def get_schema_summary(self) -> dict[str, Any]:
        """Return full schema summary: constraints, indexes, labels, relationship types."""
        constraints = await self.list_constraints()
        indexes = await self.list_indexes()
        labels = await self.get_all_labels()
        rel_types = await self.get_all_relationship_types()

        from app.modules.knowledge.domain.ontology import ontology_summary
        domain_summary = ontology_summary()

        return {
            "registered_domain_ontology": domain_summary,
            "database_schema": {
                "active_labels": labels,
                "label_count": len(labels),
                "active_relationship_types": rel_types,
                "relationship_type_count": len(rel_types),
                "constraints": constraints,
                "constraint_count": len(constraints),
                "indexes": indexes,
                "index_count": len(indexes),
            },
        }

    async def validate_node_count(self, expected_labels: list[str]) -> dict[str, int]:
        """Count nodes per label across expected_labels."""
        counts: dict[str, int] = {}
        for label in expected_labels:
            try:
                cnt = await self.count(label=label)
                counts[label] = cnt
            except Exception:
                counts[label] = 0
        return counts
