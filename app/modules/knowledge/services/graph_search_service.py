"""
services/graph_search_service.py — Graph Search and Discovery Service.

Provides text, property, structural, and proximity search over the Knowledge Graph.
"""
from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.application.dto.search_dto import (
    SearchHit,
    SearchRequest,
    SearchResult,
)
from app.modules.knowledge.infrastructure.cypher import search as search_cypher
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository

log = get_logger("knowledge.service.search")


class GraphSearchService:
    """Service providing full-text, property, structural, and proximity graph search."""

    def __init__(self, repo: BaseNeo4jRepository | None = None) -> None:
        self._repo = repo or BaseNeo4jRepository()

    async def search(self, request: SearchRequest) -> SearchResult:
        """Dispatch search request to the appropriate search strategy."""
        t0 = time.monotonic()

        if request.search_type == "proximity" and request.proximity_node_id:
            hits, total = await self._search_proximity(request)
        elif request.search_type == "property" and request.properties:
            hits, total = await self._search_properties(request)
        else:
            hits, total = await self._search_text(request)

        elapsed = (time.monotonic() - t0) * 1000
        log.info(f"Graph search query={request.query!r} returned {len(hits)} hits ({total} total) in {elapsed:.1f}ms")

        return SearchResult(
            query=request.query,
            total=total,
            offset=request.offset,
            limit=request.limit,
            hits=hits,
            execution_time_ms=elapsed,
            search_type=request.search_type,
        )

    async def _search_text(self, request: SearchRequest) -> tuple[list[SearchHit], int]:
        """Perform text matching against node name, title, code, and description."""
        label_filter = request.entity_types[0] if request.entity_types else None

        params = {
            "query": request.query,
            "label": label_filter,
            "skip": request.offset,
            "limit": request.limit,
        }

        try:
            records = await self._repo.execute_query(search_cypher.FULL_TEXT_ANY_NODE, params)
            count_records = await self._repo.execute_query(search_cypher.FULL_TEXT_COUNT, {"query": request.query, "label": label_filter})

            total = count_records[0].get("total", 0) if count_records else len(records)

            hits = []
            for rec in records:
                node = rec.get("n", {})
                props = dict(node._properties) if hasattr(node, "_properties") else dict(node)
                nid = props.get("id", rec.get("node_id", ""))
                label = props.get("entity_type", rec.get("label", "GraphEntity"))
                name = props.get("name") or props.get("title") or props.get("code")

                snippet = f"{label} '{name}'" if name else label

                hits.append(
                    SearchHit(
                        node_id=nid,
                        label=label,
                        name=name,
                        code=props.get("code"),
                        score=1.0,
                        matched_properties=props,
                        snippet=snippet,
                    )
                )

            return hits, total
        except Exception as exc:
            log.error(f"Text search failed for {request.query!r}: {exc}")
            return [], 0

    async def _search_properties(self, request: SearchRequest) -> tuple[list[SearchHit], int]:
        """Search nodes matching property key-value pairs."""
        hits: list[SearchHit] = []
        label = request.entity_types[0] if request.entity_types else "GraphEntity"

        for prop_name, prop_val in request.properties.items():
            params = {
                "entity_type": label,
                "property_name": prop_name,
                "property_value": prop_val,
                "skip": request.offset,
                "limit": request.limit,
            }
            try:
                records = await self._repo.execute_query(search_cypher.PROPERTY_EXACT_MATCH, params)
                for rec in records:
                    node = rec.get("n", {})
                    props = dict(node._properties) if hasattr(node, "_properties") else dict(node)
                    hits.append(
                        SearchHit(
                            node_id=props.get("id", ""),
                            label=props.get("entity_type", label),
                            name=props.get("name") or props.get("title"),
                            code=props.get("code"),
                            score=1.0,
                            matched_properties=props,
                            snippet=f"Matched {prop_name}={prop_val}",
                        )
                    )
            except Exception as exc:
                log.error(f"Property search failed: {exc}")

        return hits, len(hits)

    async def _search_proximity(self, request: SearchRequest) -> tuple[list[SearchHit], int]:
        """Search nodes within N hops of a center node."""
        label_filter = request.entity_types[0] if request.entity_types else None
        params = {
            "center_node_id": request.proximity_node_id,
            "max_hops": request.proximity_hops,
            "filter_type": label_filter,
            "limit": request.limit,
        }
        try:
            records = await self._repo.execute_query(search_cypher.PROXIMITY_SEARCH, params)
            hits = []
            for rec in records:
                node = rec.get("nearby", {})
                props = dict(node._properties) if hasattr(node, "_properties") else dict(node)
                hits.append(
                    SearchHit(
                        node_id=props.get("id", rec.get("node_id", "")),
                        label=props.get("entity_type", rec.get("label", "")),
                        name=props.get("name") or props.get("title"),
                        code=props.get("code"),
                        score=0.9,
                        matched_properties=props,
                        snippet=f"Proximity hop from {request.proximity_node_id}",
                    )
                )
            return hits, len(hits)
        except Exception as exc:
            log.error(f"Proximity search failed for center {request.proximity_node_id}: {exc}")
            return [], 0
