"""rca_ontology_extension.py — RCA-specific ontology extension for the Knowledge Graph.

Bootstraps 7 new node label types and 8 new relationship types.
All operations are idempotent (IF NOT EXISTS).
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository

log = get_logger("root_cause.ontology")

RCA_NODE_LABELS = [
    "LessonLearned",
    "FailurePattern",
    "InvestigationMemory",
    "CounterfactualScenario",
    "RecommendationFeedback",
    "PreventiveMeasure",
    "CorrectiveMeasure",
]

RCA_RELATIONSHIP_TYPES = [
    "VALIDATED_BY",
    "CONTRADICTS",
    "PREVENTED",
    "RESULTED_IN",
    "LEARNED_FROM",
    "SIMILAR_TO",
    "FOLLOWED_BY",
    "EVALUATED_BY",
]

RCA_FULLTEXT_LABELS = ["LessonLearned", "FailurePattern", "InvestigationMemory"]


class RCAOntologyExtension:
    """Bootstraps RCA-specific ontology constraints and indexes in Neo4j."""

    def __init__(self, repo: BaseNeo4jRepository | None = None) -> None:
        self._repo = repo or BaseNeo4jRepository()

    async def initialize(self) -> dict[str, Any]:
        """Idempotently create all RCA constraints and indexes."""
        created_constraints = 0
        created_indexes = 0
        errors: list[str] = []

        for label in RCA_NODE_LABELS:
            constraint_name = f"rca_{label.lower()}_id_unique"
            query = (
                f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.id IS UNIQUE"
            )
            try:
                await self._repo.execute_query(query)
                created_constraints += 1
                log.debug(f"Constraint ensured: {constraint_name}")
            except Exception as exc:
                errors.append(f"Constraint {constraint_name}: {exc}")

        for label in RCA_FULLTEXT_LABELS:
            index_name = f"rca_{label.lower()}_fulltext"
            query = (
                f"CREATE FULLTEXT INDEX {index_name} IF NOT EXISTS "
                f"FOR (n:{label}) ON EACH [n.title, n.description, n.lesson_text, n.name]"
            )
            try:
                await self._repo.execute_query(query)
                created_indexes += 1
                log.debug(f"Fulltext index ensured: {index_name}")
            except Exception as exc:
                errors.append(f"Index {index_name}: {exc}")

        result = {
            "rca_constraints_created": created_constraints,
            "rca_indexes_created": created_indexes,
            "rca_node_labels": RCA_NODE_LABELS,
            "rca_relationship_types": RCA_RELATIONSHIP_TYPES,
            "errors": errors,
        }
        log.info(f"RCA ontology extension initialized: {result}")
        return result

    async def create_relationship(
        self,
        source_id: str,
        source_label: str,
        target_id: str,
        target_label: str,
        rel_type: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Create an RCA-domain relationship between two nodes."""
        if rel_type not in RCA_RELATIONSHIP_TYPES:
            log.warning(f"Unknown RCA relationship type: {rel_type}")
        props = properties or {}
        query = f"""
        MATCH (s:{source_label} {{id: $source_id}})
        MATCH (t:{target_label} {{id: $target_id}})
        MERGE (s)-[r:{rel_type}]->(t)
        SET r += $props
        RETURN r
        """
        try:
            await self._repo.execute_query(query, {
                "source_id": source_id,
                "target_id": target_id,
                "props": props,
            })
            return True
        except Exception as exc:
            log.error(f"RCA relationship creation failed: {exc}")
            return False
