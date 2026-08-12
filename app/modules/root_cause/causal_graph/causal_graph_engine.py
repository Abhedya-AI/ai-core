"""causal_graph_engine.py — Causal Graph Construction and Analysis Engine."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository
from app.modules.root_cause.domain.models import (
    Evidence, CausalChain, CausalNode, CausalEdge, CausalRelationType,
)

log = get_logger("root_cause.causal_graph")


class CausalGraphEngine:
    """Builds and analyzes causal graphs from investigation evidence."""

    def __init__(self, base_repo: BaseNeo4jRepository | None = None) -> None:
        self.repo = base_repo

    def build_causal_graph(
        self, investigation_id: str, evidence_list: list[Evidence], incident_id: str,
    ) -> CausalChain:
        log.info(f"Building causal graph for investigation {investigation_id}")
        sorted_evidence = sorted(evidence_list, key=lambda e: e.timestamp)
        nodes: dict[str, CausalNode] = {}
        edges: list[CausalEdge] = []

        for idx, ev in enumerate(sorted_evidence):
            node = CausalNode(
                node_type=ev.evidence_type.value,
                entity_id=ev.id,
                label=ev.title,
                description=ev.description,
                severity=ev.severity,
                confidence=ev.confidence,
                evidence_ids=[ev.id],
                is_root_cause=False,
                is_contributing_factor=False,
                depth=idx,
            )
            nodes[ev.id] = node

        # Build temporal PRECEDES edges
        for idx in range(len(sorted_evidence) - 1):
            src_ev = sorted_evidence[idx]
            tgt_ev = sorted_evidence[idx + 1]
            edges.append(CausalEdge(
                source_node_id=nodes[src_ev.id].id,
                target_node_id=nodes[tgt_ev.id].id,
                relation_type=CausalRelationType.PRECEDES,
                confidence=0.8,
                evidence_ids=[src_ev.id, tgt_ev.id],
                description=f"{src_ev.title} precedes {tgt_ev.title}",
            ))
            # Add CONTRIBUTES_TO for high severity
            if src_ev.severity in ("CRITICAL", "HIGH"):
                edges.append(CausalEdge(
                    source_node_id=nodes[src_ev.id].id,
                    target_node_id=nodes[tgt_ev.id].id,
                    relation_type=CausalRelationType.CONTRIBUTES_TO,
                    confidence=0.9,
                    evidence_ids=[src_ev.id, tgt_ev.id],
                    description=f"High-severity {src_ev.title} contributes to {tgt_ev.title}",
                ))

        # Mark root cause candidates
        root_ids: list[str] = []
        if sorted_evidence:
            first = nodes[sorted_evidence[0].id]
            if first.confidence > 0.6:
                first.is_root_cause = True
                root_ids.append(first.id)

        # Contributing factors: high-severity non-root nodes
        cf_ids: list[str] = []
        for node in nodes.values():
            if not node.is_root_cause and node.severity in ("CRITICAL", "HIGH"):
                node.is_contributing_factor = True
                cf_ids.append(node.id)

        max_depth = max((n.depth for n in nodes.values()), default=0)
        return CausalChain(
            investigation_id=investigation_id,
            nodes=list(nodes.values()),
            edges=edges,
            root_cause_node_ids=root_ids,
            contributing_factor_node_ids=cf_ids,
            max_depth=max_depth,
            total_paths=len(edges),
        )

    def find_root_cause_paths(self, causal_chain: CausalChain) -> list[list[str]]:
        adj: dict[str, list[str]] = {n.id: [] for n in causal_chain.nodes}
        for e in causal_chain.edges:
            adj.setdefault(e.target_node_id, []).append(e.source_node_id)
        root_set = set(causal_chain.root_cause_node_ids)
        leaf_ids = {n.id for n in causal_chain.nodes} - {e.source_node_id for e in causal_chain.edges}
        paths: list[list[str]] = []
        def _dfs(cur: str, path: list[str]) -> None:
            if cur in root_set:
                paths.append(path + [cur])
                return
            for nb in adj.get(cur, []):
                if nb not in path:
                    _dfs(nb, path + [cur])
        for leaf in leaf_ids:
            _dfs(leaf, [])
        return paths

    def compute_influence_scores(self, causal_chain: CausalChain) -> dict[str, float]:
        out_deg: dict[str, int] = {n.id: 0 for n in causal_chain.nodes}
        for e in causal_chain.edges:
            out_deg[e.source_node_id] = out_deg.get(e.source_node_id, 0) + 1
        return {
            n.id: out_deg.get(n.id, 0) * 0.5 + n.confidence * 0.5
            for n in causal_chain.nodes
        }

    def find_critical_path(self, causal_chain: CausalChain) -> list[str]:
        paths = self.find_root_cause_paths(causal_chain)
        if not paths:
            return []
        scores = self.compute_influence_scores(causal_chain)
        best = max(paths, key=lambda p: sum(scores.get(nid, 0) for nid in p))
        return best[::-1]

    def find_failure_chains(self, causal_chain: CausalChain) -> list[list[CausalNode]]:
        paths = self.find_root_cause_paths(causal_chain)
        node_map = {n.id: n for n in causal_chain.nodes}
        return [[node_map[nid] for nid in p[::-1] if nid in node_map] for p in paths]

    def compute_impact_radius(self, causal_chain: CausalChain, node_id: str) -> dict[str, Any]:
        adj: dict[str, list[str]] = {n.id: [] for n in causal_chain.nodes}
        for e in causal_chain.edges:
            adj.setdefault(e.source_node_id, []).append(e.target_node_id)
        visited: set[str] = set()
        queue = [node_id]
        depth: dict[str, int] = {node_id: 0}
        while queue:
            cur = queue.pop(0)
            if cur in visited:
                continue
            visited.add(cur)
            for nb in adj.get(cur, []):
                if nb not in visited:
                    depth[nb] = depth[cur] + 1
                    queue.append(nb)
        return {
            "node_id": node_id,
            "impacted_nodes": list(visited - {node_id}),
            "max_depth": max(depth.values()) if depth else 0,
        }

    async def sync_to_knowledge_graph(self, causal_chain: CausalChain) -> bool:
        if not self.repo:
            log.warning("No Neo4j repository configured — skipping KG sync")
            return False
        try:
            for node in causal_chain.nodes:
                query = """
                MERGE (n:CausalNode {id: $id})
                SET n.node_type = $node_type,
                    n.entity_id = $entity_id,
                    n.label = $label,
                    n.confidence = $confidence,
                    n.is_root_cause = $is_root_cause,
                    n.investigation_id = $investigation_id
                """
                await self.repo.execute_query(query, {
                    "id": node.id,
                    "node_type": node.node_type,
                    "entity_id": node.entity_id,
                    "label": node.label,
                    "confidence": node.confidence,
                    "is_root_cause": node.is_root_cause,
                    "investigation_id": causal_chain.investigation_id,
                })
            for edge in causal_chain.edges:
                rel_type = edge.relation_type.value
                query = f"""
                MATCH (s:CausalNode {{id: $source_id}})
                MATCH (t:CausalNode {{id: $target_id}})
                MERGE (s)-[r:{rel_type}]->(t)
                SET r.confidence = $confidence, r.id = $edge_id
                """
                await self.repo.execute_query(query, {
                    "source_id": edge.source_node_id,
                    "target_id": edge.target_node_id,
                    "confidence": edge.confidence,
                    "edge_id": edge.id,
                })
            log.info(f"Synced causal graph for {causal_chain.investigation_id} to KG")
            return True
        except Exception as exc:
            log.error(f"Failed to sync causal graph to KG: {exc}")
            return False
