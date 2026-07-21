"""
base_repository.py — Base Neo4j repository implementation of IKnowledgeRepository.

Interacts with Neo4j driver using async sessions. Handles parameter binding,
ontology rule validation, transaction boundaries, and exception translation.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from neo4j import AsyncDriver, AsyncSession
from neo4j.exceptions import Neo4jError

from app.core.logging import get_logger
from app.infrastructure.neo4j.driver import get_driver
from app.infrastructure.neo4j.session import get_neo4j_session
from app.modules.knowledge.application.dto import (
    CreateNodeRequest,
    CreateRelationshipRequest,
    TraversalPath,
    TraversalRequest,
    TraversalResult,
    UpdateNodeRequest,
)
from app.modules.knowledge.application.interfaces.repository import IKnowledgeRepository
from app.modules.knowledge.domain.ontology import validate_entity_data, validate_graph_edge
from app.modules.knowledge.infrastructure.cypher import common as common_cypher
from app.modules.knowledge.infrastructure.exceptions import (
    DuplicateNodeError,
    GraphTraversalError,
    KnowledgeGraphError,
    NodeNotFoundError,
    OntologyValidationError,
    RelationshipNotFoundError,
)

log = get_logger("knowledge.repository.base")


class BaseNeo4jRepository(IKnowledgeRepository):
    """
    Base Neo4j implementation of IKnowledgeRepository interface.

    Accepts an optional AsyncDriver for dependency injection/testing.
    Defaults to the application Neo4j driver.
    """

    def __init__(self, driver: AsyncDriver | None = None) -> None:
        self._driver = driver

    async def _get_session(self) -> AsyncSession:
        if self._driver is not None:
            return self._driver.session(database="neo4j")
        driver = await get_driver()
        return driver.session(database="neo4j")

    @asynccontextmanager
    async def transaction(self):
        """Async context manager exposing an explicit transaction session boundary."""
        session = await self._get_session()
        tx = await session.begin_transaction()
        try:
            yield tx
            await tx.commit()
        except Exception as exc:
            await tx.rollback()
            log.error(f"Transaction rolled back: {exc}")
            raise self._translate_error(exc) from exc
        finally:
            await session.close()

    def _translate_error(self, exc: Exception) -> Exception:
        """Translate Neo4j driver errors to domain KnowledgeGraphError exceptions."""
        if isinstance(exc, KnowledgeGraphError):
            return exc
        if isinstance(exc, Neo4jError):
            if "already exists" in str(exc) or "ConstraintValidationFailed" in str(exc):
                return DuplicateNodeError(str(exc))
            return KnowledgeGraphError(f"Neo4j database error: {exc}")
        return KnowledgeGraphError(str(exc))

    async def create_node(self, request: CreateNodeRequest) -> dict[str, Any]:
        """Create a graph node after validating properties against the ontology."""
        try:
            # Validate against domain ontology if entity type is registered
            try:
                entity = validate_entity_data(request.label, request.properties)
                props = entity.to_graph_properties()
            except ValueError:
                # Unregistered label, fallback to raw properties
                props = request.properties
                props.setdefault("entity_type", request.label)

            if request.node_id:
                props["id"] = request.node_id

            props.setdefault("created_at", datetime.now(tz=timezone.utc).isoformat())
            props.setdefault("updated_at", datetime.now(tz=timezone.utc).isoformat())

            query = common_cypher.MERGE_NODE.format(label=request.label)
            records = await self.execute_query(query, {"id": props["id"], "properties": props})
            if not records:
                raise KnowledgeGraphError(f"Failed to create node of label '{request.label}'")
            return records[0].get("n", props)
        except Exception as exc:
            raise self._translate_error(exc) from exc

    async def update_node(self, request: UpdateNodeRequest) -> dict[str, Any]:
        """Update node properties."""
        try:
            if not await self.exists(request.node_id):
                raise NodeNotFoundError(request.node_id, request.label)

            props = dict(request.properties)
            props["updated_at"] = datetime.now(tz=timezone.utc).isoformat()

            records = await self.execute_query(
                common_cypher.UPDATE_NODE,
                {"id": request.node_id, "properties": props, "updated_at": props["updated_at"]},
            )
            if not records:
                raise NodeNotFoundError(request.node_id)
            return records[0].get("n", props)
        except Exception as exc:
            raise self._translate_error(exc) from exc

    async def delete_node(self, node_id: str, label: str | None = None) -> bool:
        """Detach and delete a node by ID."""
        try:
            records = await self.execute_query(common_cypher.DELETE_NODE, {"id": node_id})
            if records and records[0].get("deleted_count", 0) > 0:
                return True
            return False
        except Exception as exc:
            raise self._translate_error(exc) from exc

    async def find_by_id(self, node_id: str, label: str | None = None) -> dict[str, Any] | None:
        """Find node properties by ID."""
        try:
            records = await self.execute_query(common_cypher.FIND_NODE_BY_ID, {"id": node_id})
            if records and "n" in records[0]:
                node_data = records[0]["n"]
                if hasattr(node_data, "_properties"):
                    return dict(node_data._properties)
                return dict(node_data)
            return None
        except Exception as exc:
            raise self._translate_error(exc) from exc

    async def exists(self, node_id: str, label: str | None = None) -> bool:
        """Return True if node exists in Neo4j."""
        try:
            records = await self.execute_query(common_cypher.NODE_EXISTS, {"id": node_id})
            if records:
                return bool(records[0].get("exists", False))
            return False
        except Exception as exc:
            raise self._translate_error(exc) from exc

    async def count(self, label: str | None = None) -> int:
        """Count nodes by label or total nodes."""
        try:
            if label:
                query = common_cypher.COUNT_NODES.format(label=label)
                records = await self.execute_query(query)
            else:
                records = await self.execute_query(common_cypher.COUNT_ALL_NODES)
            if records:
                return int(records[0].get("count", 0))
            return 0
        except Exception as exc:
            raise self._translate_error(exc) from exc

    async def create_relationship(self, request: CreateRelationshipRequest) -> bool:
        """Create a directed relationship edge."""
        try:
            query = common_cypher.CREATE_RELATIONSHIP.format(rel_type=request.rel_type.value)
            records = await self.execute_query(
                query,
                {
                    "source_id": request.source_id,
                    "target_id": request.target_id,
                    "properties": request.properties,
                },
            )
            if records and records[0].get("created_count", 0) > 0:
                return True
            return False
        except Exception as exc:
            raise self._translate_error(exc) from exc

    async def delete_relationship(self, source_id: str, rel_type: str, target_id: str) -> bool:
        """Delete a relationship edge."""
        try:
            query = common_cypher.DELETE_RELATIONSHIP.format(rel_type=rel_type)
            records = await self.execute_query(
                query,
                {"source_id": source_id, "target_id": target_id},
            )
            if records and records[0].get("deleted_count", 0) > 0:
                return True
            return False
        except Exception as exc:
            raise self._translate_error(exc) from exc

    async def get_neighbors(
        self,
        node_id: str,
        rel_type: str | None = None,
        direction: str = "OUTGOING",
    ) -> list[dict[str, Any]]:
        """Get neighboring nodes."""
        try:
            records = await self.execute_query(common_cypher.GET_NEIGHBORS, {"node_id": node_id})
            neighbors = []
            for record in records:
                n = record.get("n")
                if n:
                    props = dict(n._properties) if hasattr(n, "_properties") else dict(n)
                    props["_relationship"] = record.get("relationship")
                    neighbors.append(props)
            return neighbors
        except Exception as exc:
            raise self._translate_error(exc) from exc

    async def traverse(self, request: TraversalRequest) -> TraversalResult:
        """Multi-hop subgraph traversal."""
        try:
            query = common_cypher.TRAVERSE_SUBGRAPH.format(max_depth=request.max_depth)
            records = await self.execute_query(
                query,
                {"start_node_id": request.start_node_id, "limit": 100},
            )
            paths: list[TraversalPath] = []
            for rec in records:
                p = rec.get("path")
                if p:
                    nodes = [dict(n._properties) if hasattr(n, "_properties") else dict(n) for n in getattr(p, "nodes", [])]
                    rels = [dict(r._properties) if hasattr(r, "_properties") else dict(r) for r in getattr(p, "relationships", [])]
                    paths.append(TraversalPath(nodes=nodes, relationships=rels, depth=len(rels)))

            return TraversalResult(
                start_node_id=request.start_node_id,
                paths=paths,
                total_nodes_found=sum(len(p.nodes) for p in paths),
            )
        except Exception as exc:
            raise GraphTraversalError(f"Traversal failed for {request.start_node_id}: {exc}") from exc

    async def execute_query(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute a raw parameterized Cypher query using an async session."""
        session = await self._get_session()
        try:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records
        except Exception as exc:
            raise self._translate_error(exc) from exc
        finally:
            await session.close()
