"""
services/context_service.py — Graph Context Builder Service (LLM / GraphRAG).

Assembles rich graph context windows around root nodes for LLM prompt injection
and GraphRAG retrieval.

Features:
  - Multi-hop neighborhood expansion
  - Narrative generation (human-readable graph summary)
  - Triplet extraction (subject, predicate, object)
  - Property filtering and token count estimation
  - Redis cache integration via GraphCacheService
"""
from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.application.dto.context_dto import (
    ContextEdge,
    ContextNode,
    ContextRequest,
    GraphContext,
)
from app.modules.knowledge.infrastructure.repositories.traversal_repository import (
    TraversalRepository,
)
from app.modules.knowledge.services.graph_cache_service import GraphCacheService

log = get_logger("knowledge.service.context")


class ContextService:
    """Service assembling graph context structures for LLM / GraphRAG prompt injection."""

    def __init__(
        self,
        traversal_repo: TraversalRepository | None = None,
        cache_service: GraphCacheService | None = None,
    ) -> None:
        self._traversal = traversal_repo or TraversalRepository()
        self._cache = cache_service or GraphCacheService()

    async def assemble_context(self, request: ContextRequest) -> GraphContext:
        """
        Extract k-hop subgraph around node_id and format as GraphContext.
        Checks Redis cache first.
        """
        t0 = time.monotonic()

        # Check cache
        cached_dict = await self._cache.get_context(request.node_id, request.depth)
        if cached_dict:
            log.info(f"Graph context cache hit for {request.node_id} (depth={request.depth})")
            ctx = GraphContext(**cached_dict)
            ctx.cached = True
            return ctx

        # Fetch k-hop neighborhood
        nb_data = await self._traversal.get_neighborhood(
            node_id=request.node_id,
            hops=request.depth,
            limit=request.max_nodes,
        )

        nodes_raw = nb_data.get("nodes", [])
        edges_raw = nb_data.get("edges", [])

        # Process nodes
        context_nodes: list[ContextNode] = []
        root_label = "GraphEntity"

        for node_dict in nodes_raw:
            nid = node_dict.get("id", "")
            label = node_dict.get("entity_type", node_dict.get("type", "GraphEntity"))
            is_root = nid == request.node_id
            if is_root:
                root_label = label

            # Filter properties if specified
            props = dict(node_dict)
            if request.include_properties:
                props = {k: v for k, v in props.items() if k in request.include_properties or k in ("id", "name", "code")}

            context_nodes.append(
                ContextNode(
                    id=nid,
                    label=label,
                    name=node_dict.get("name") or node_dict.get("title") or node_dict.get("code"),
                    properties=props,
                    distance_from_root=0 if is_root else 1,
                    is_root=is_root,
                )
            )

        # Process edges
        context_edges: list[ContextEdge] = []
        triplets: list[tuple[str, str, str]] = []

        for edge_dict in edges_raw:
            rel_type = edge_dict.get("rel_type", "")
            if request.exclude_types and rel_type in request.exclude_types:
                continue

            src = edge_dict.get("source_id", "")
            tgt = edge_dict.get("target_id", "")
            context_edges.append(
                ContextEdge(
                    source_id=src,
                    target_id=tgt,
                    rel_type=rel_type,
                    properties=edge_dict.get("properties", {}),
                )
            )
            triplets.append((src, rel_type, tgt))

        # Generate narrative text summary
        narrative = self._generate_narrative(
            root_node_id=request.node_id,
            root_label=root_label,
            nodes=context_nodes,
            edges=context_edges,
        )

        # Estimate token count (rough heuristic: 4 chars per token)
        prompt_text = narrative + "\n" + "\n".join(f"{s} -> {p} -> {o}" for s, p, o in triplets)
        token_estimate = max(1, len(prompt_text) // 4)

        ctx = GraphContext(
            root_node_id=request.node_id,
            root_label=root_label,
            depth=request.depth,
            nodes=context_nodes,
            edges=context_edges,
            narrative=narrative,
            triplets=triplets,
            token_estimate=token_estimate,
            cached=False,
        )

        # Cache result
        await self._cache.set_context(
            request.node_id, request.depth, ctx.model_dump(), ttl=180
        )

        elapsed = (time.monotonic() - t0) * 1000
        log.info(
            f"Assembled context for {request.node_id}: {len(context_nodes)} nodes, "
            f"{len(context_edges)} edges ({token_estimate} tokens) in {elapsed:.1f}ms"
        )
        return ctx

    def _generate_narrative(
        self,
        root_node_id: str,
        root_label: str,
        nodes: list[ContextNode],
        edges: list[ContextEdge],
    ) -> str:
        """Generate a concise natural language narrative describing the subgraph."""
        node_count = len(nodes)
        edge_count = len(edges)
        root_node = next((n for n in nodes if n.is_root), None)
        root_name = root_node.name if root_node and root_node.name else root_node_id

        summary_lines = [
            f"Target entity '{root_name}' ({root_label}) is connected to {node_count - 1} neighboring entities "
            f"across {edge_count} relationship links in the Knowledge Graph.",
        ]

        # Summarize key relationships
        rel_counts: dict[str, int] = {}
        for edge in edges:
            rel_counts[edge.rel_type] = rel_counts.get(edge.rel_type, 0) + 1

        if rel_counts:
            rel_summary = ", ".join(f"{type_}: {cnt}" for type_, cnt in rel_counts.items())
            summary_lines.append(f"Relationship distribution: {rel_summary}.")

        return " ".join(summary_lines)
