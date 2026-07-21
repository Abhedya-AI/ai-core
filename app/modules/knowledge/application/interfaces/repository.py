"""
repository.py — Abstract Knowledge Repository Interface (IKnowledgeRepository).

All domain services, agents, and GraphRAG modules depend ONLY on this interface.
They NEVER import Neo4j drivers or Cypher modules directly.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.modules.knowledge.application.dto import (
    CreateNodeRequest,
    CreateRelationshipRequest,
    TraversalRequest,
    TraversalResult,
    UpdateNodeRequest,
)


class IKnowledgeRepository(ABC):
    """Abstract interface defining operations on the Knowledge Graph."""

    @abstractmethod
    async def create_node(self, request: CreateNodeRequest) -> dict[str, Any]:
        """Create a graph node from a CreateNodeRequest."""

    @abstractmethod
    async def update_node(self, request: UpdateNodeRequest) -> dict[str, Any]:
        """Update properties of an existing node."""

    @abstractmethod
    async def delete_node(self, node_id: str, label: str | None = None) -> bool:
        """Delete a node and its attached relationships."""

    @abstractmethod
    async def find_by_id(self, node_id: str, label: str | None = None) -> dict[str, Any] | None:
        """Fetch a node by its unique id."""

    @abstractmethod
    async def exists(self, node_id: str, label: str | None = None) -> bool:
        """Check if a node exists."""

    @abstractmethod
    async def count(self, label: str | None = None) -> int:
        """Count nodes with an optional label filter."""

    @abstractmethod
    async def create_relationship(self, request: CreateRelationshipRequest) -> bool:
        """Create a directed edge between two nodes."""

    @abstractmethod
    async def delete_relationship(self, source_id: str, rel_type: str, target_id: str) -> bool:
        """Delete a relationship edge."""

    @abstractmethod
    async def get_neighbors(
        self,
        node_id: str,
        rel_type: str | None = None,
        direction: str = "OUTGOING",
    ) -> list[dict[str, Any]]:
        """Get neighboring nodes connected to node_id."""

    @abstractmethod
    async def traverse(self, request: TraversalRequest) -> TraversalResult:
        """Perform multi-hop graph traversal."""

    @abstractmethod
    async def execute_query(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute a raw parameterized graph query and return result records."""
