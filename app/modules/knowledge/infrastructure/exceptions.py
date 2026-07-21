"""
exceptions.py — Domain exceptions for the Knowledge Repository layer.

Prevents low-level Neo4j driver exceptions (e.g. ServiceUnavailable, CypherError)
from leaking outside the infrastructure layer.
"""


class KnowledgeGraphError(Exception):
    """Base exception for all Knowledge Graph operations."""


class NodeNotFoundError(KnowledgeGraphError):
    """Raised when a requested graph node does not exist."""

    def __init__(self, node_id: str, label: str | None = None) -> None:
        self.node_id = node_id
        self.label = label
        msg = f"Node '{node_id}'"
        if label:
            msg += f" with label '{label}'"
        msg += " was not found in the knowledge graph."
        super().__init__(msg)


class DuplicateNodeError(KnowledgeGraphError):
    """Raised when attempting to create a node with an existing unique identifier."""

    def __init__(self, node_id: str, label: str | None = None) -> None:
        self.node_id = node_id
        self.label = label
        super().__init__(f"Node '{node_id}' already exists in the graph.")


class RelationshipNotFoundError(KnowledgeGraphError):
    """Raised when a specified relationship between two nodes does not exist."""

    def __init__(self, source_id: str, rel_type: str, target_id: str) -> None:
        super().__init__(
            f"Relationship '{rel_type}' from '{source_id}' to '{target_id}' was not found."
        )


class OntologyValidationError(KnowledgeGraphError):
    """Raised when node data or edge creation violates ontology rules."""


class GraphTraversalError(KnowledgeGraphError):
    """Raised when graph traversal or pathfinding fails."""
