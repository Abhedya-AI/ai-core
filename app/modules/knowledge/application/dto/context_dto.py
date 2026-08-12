"""
dto/context_dto.py — DTOs for Graph Context Assembly (used by LLM / GraphRAG).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ContextRequest(BaseModel):
    """Request to assemble a graph context window for LLM/GraphRAG prompt injection."""

    node_id: str = Field(..., description="Root node to build context around")
    depth: int = Field(default=2, ge=1, le=4, description="Hop depth for context extraction")
    include_properties: list[str] = Field(
        default_factory=list,
        description="Specific property names to include (empty = all)",
    )
    exclude_types: list[str] = Field(
        default_factory=list,
        description="Relationship types to exclude from context",
    )
    max_nodes: int = Field(default=50, ge=1, le=200, description="Hard cap on context node count")
    format: str = Field(
        default="structured",
        description="Output format: structured | narrative | triplets",
    )
    include_risk_context: bool = Field(
        default=True,
        description="Include risk/hazard context even if beyond depth limit",
    )


class ContextNode(BaseModel):
    """A node in the assembled graph context."""

    id: str
    label: str
    name: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    distance_from_root: int = 0
    is_root: bool = False


class ContextEdge(BaseModel):
    """An edge (relationship) in the assembled graph context."""

    source_id: str
    target_id: str
    rel_type: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphContext(BaseModel):
    """
    Assembled graph context ready for LLM prompt injection or GraphRAG retrieval.

    Contains the structural representation of the neighborhood around a root node.
    """

    root_node_id: str
    root_label: str
    depth: int
    nodes: list[ContextNode] = Field(default_factory=list)
    edges: list[ContextEdge] = Field(default_factory=list)
    narrative: str | None = Field(default=None, description="Human-readable description of the subgraph")
    triplets: list[tuple[str, str, str]] = Field(
        default_factory=list,
        description="(subject_id, predicate, object_id) tuples",
    )
    token_estimate: int = Field(default=0, description="Approximate LLM token count for this context")
    cached: bool = False

    def to_prompt_text(self) -> str:
        """Generate a concise text representation suitable for LLM prompt injection."""
        lines: list[str] = [
            f"=== Knowledge Graph Context: {self.root_label} [{self.root_node_id}] ===",
        ]

        if self.narrative:
            lines.append(self.narrative)
            lines.append("")

        # Nodes grouped by label
        by_label: dict[str, list[ContextNode]] = {}
        for node in self.nodes:
            by_label.setdefault(node.label, []).append(node)

        for label, label_nodes in sorted(by_label.items()):
            lines.append(f"[{label}]")
            for node in label_nodes:
                name_str = f" '{node.name}'" if node.name else ""
                lines.append(f"  • {node.id}{name_str}")

        # Relationships
        if self.edges:
            lines.append("\n[Relationships]")
            for edge in self.edges:
                lines.append(f"  {edge.source_id} --[{edge.rel_type}]--> {edge.target_id}")

        return "\n".join(lines)

    def to_triplets_text(self) -> str:
        """Render triplets as RDF-like text for semantic retrieval."""
        return "\n".join(f"({s}, {p}, {o})" for s, p, o in self.triplets)
