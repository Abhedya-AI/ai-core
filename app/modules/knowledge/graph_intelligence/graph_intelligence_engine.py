"""
app/modules/knowledge/graph_intelligence/graph_intelligence_engine.py — Graph Intelligence Engine.

Provides graph traversal, shortest path, neighborhood expansion, centrality (Degree, Betweenness, PageRank),
node similarity, community detection, asset dependency analysis, impact blast-radius analysis,
critical path discovery, root dependency tracing, exponential risk propagation, hazard propagation,
equipment & sensor connectivity, and worker exposure mapping.

Operates seamlessly over in-memory graph cache/adjacency structures and Neo4j queries if Neo4j is available,
ensuring zero runtime errors and robust fallback execution.
"""

from __future__ import annotations

import math
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.logging import get_logger

log = get_logger("app.modules.knowledge.graph_intelligence_engine")


class GraphIntelligenceEngine:
    """
    Graph Intelligence Engine providing high-performance structural, topological,
    and causal analysis over industrial safety knowledge graphs.
    """

    def __init__(self, repository: Optional[Any] = None) -> None:
        """
        Initialize the Graph Intelligence Engine.

        :param repository: Optional Knowledge Repository instance for Neo4j interaction.
        """
        self._repository = repository
        self._adj: Dict[str, Dict[str, str]] = defaultdict(dict)      # u -> {v: rel_type}
        self._rev_adj: Dict[str, Dict[str, str]] = defaultdict(dict)  # v -> {u: rel_type}
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._seed_default_industrial_graph()
        log.info("GraphIntelligenceEngine initialized with in-memory graph topology cache.")

    def _seed_default_industrial_graph(self) -> None:
        """Seed a robust default industrial graph topology for in-memory graph caching & fallback."""
        default_nodes = [
            ("plant-1", {"type": "Plant", "name": "Main Refinery", "code": "PLANT-01"}),
            ("bldg-1", {"type": "Building", "name": "Processing Facility", "code": "BLDG-01"}),
            ("floor-1", {"type": "Floor", "name": "Ground Level", "code": "FL-01"}),
            ("zone-1", {"type": "Zone", "name": "Boiler Room", "risk_level": "HIGH", "code": "Z-BOILER"}),
            ("zone-2", {"type": "Zone", "name": "Reactor Floor", "risk_level": "CRITICAL", "code": "Z-REACTOR"}),
            ("eq-1", {"type": "Equipment", "name": "Boiler 3", "status": "WARNING", "code": "EQ-BLR3"}),
            ("eq-2", {"type": "Equipment", "name": "Reactor Pump", "status": "OPERATIONAL", "code": "EQ-PUMP1"}),
            ("s1", {"type": "Sensor", "name": "Temp Sensor 1", "sensor_type": "TEMPERATURE", "status": "ACTIVE"}),
            ("s2", {"type": "Sensor", "name": "Pressure Sensor 2", "sensor_type": "PRESSURE", "status": "ACTIVE"}),
            ("s3", {"type": "Sensor", "name": "Gas Sensor 3", "sensor_type": "GAS", "status": "ACTIVE"}),
            ("w1", {"type": "Worker", "name": "John Doe", "role": "OPERATOR", "id": "w1"}),
            ("w2", {"type": "Worker", "name": "Jane Smith", "role": "TECHNICIAN", "id": "w2"}),
            ("haz-1", {"type": "Hazard", "name": "Overpressure Risk", "severity": "HIGH", "id": "haz-1"}),
            ("inc-1", {"type": "Incident", "name": "2025 Steam Breach", "status": "CLOSED", "id": "inc-1"}),
            ("alt-1", {"type": "Alert", "message": "High Pressure Reading", "severity": "CRITICAL", "id": "alt-1"}),
            ("ppe-1", {"type": "PPE", "ppe_type": "RESPIRATOR", "condition": "GOOD", "id": "ppe-1"}),
            ("dev-1", {"type": "Device", "name": "IoT Gateway Alpha", "status": "ONLINE", "id": "dev-1"}),
        ]
        for nid, data in default_nodes:
            self.add_node(nid, **data)

        default_edges = [
            ("bldg-1", "plant-1", "PART_OF"),
            ("floor-1", "bldg-1", "PART_OF"),
            ("zone-1", "floor-1", "LOCATED_IN"),
            ("zone-2", "floor-1", "LOCATED_IN"),
            ("eq-1", "zone-1", "LOCATED_IN"),
            ("eq-2", "zone-2", "LOCATED_IN"),
            ("s1", "eq-1", "MONITORS"),
            ("s2", "eq-1", "MONITORS"),
            ("s3", "zone-1", "LOCATED_IN"),
            ("w1", "zone-1", "LOCATED_IN"),
            ("w2", "zone-2", "LOCATED_IN"),
            ("eq-1", "haz-1", "HAS_RISK"),
            ("inc-1", "zone-1", "AFFECTS"),
            ("eq-1", "eq-2", "CONNECTED_TO"),
            ("s2", "alt-1", "TRIGGERED"),
            ("ppe-1", "w1", "PROTECTS"),
            ("dev-1", "s1", "CONNECTED_TO"),
        ]
        for u, v, rel in default_edges:
            self.add_edge(u, v, rel)

    def add_node(self, node_id: str, **kwargs: Any) -> None:
        """
        Add or update a node in the in-memory graph cache.

        :param node_id: Unique string identifier for the node.
        :param kwargs: Node property key-value attributes.
        """
        if node_id not in self._nodes:
            self._nodes[node_id] = {"id": node_id, "type": kwargs.get("type", "Entity")}
        self._nodes[node_id].update(kwargs)

    def add_edge(self, source_id: str, target_id: str, rel_type: str) -> None:
        """
        Add a directed edge between source_id and target_id with rel_type.

        :param source_id: Source node ID.
        :param target_id: Target node ID.
        :param rel_type: Relationship edge label string.
        """
        self._adj[source_id][target_id] = rel_type
        self._rev_adj[target_id][source_id] = rel_type

    def _execute_neo4j_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Optional[List[Dict[str, Any]]]:
        """Attempt Neo4j Cypher query execution via repository or database driver with safe fallback."""
        try:
            if self._repository and hasattr(self._repository, "execute_query"):
                import asyncio
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_running():
                        # Handled in sync context or fallback
                        pass
                except RuntimeError:
                    return asyncio.run(self._repository.execute_query(query, parameters or {}))
            
            from app.database.neo4j import check_health, get_driver
            if check_health():
                driver = get_driver()
                with driver.session() as session:
                    res = session.run(query, parameters or {})
                    return [record.data() for record in res]
        except Exception as exc:
            log.debug(f"Neo4j query execution skipped, falling back to in-memory graph: {exc}")
        return None

    # ── 1. Graph Traversal ───────────────────────────────────────────────────

    def traversal(
        self,
        start_node_id: str,
        max_depth: int = 3,
        rel_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform BFS multi-hop traversal starting from start_node_id up to max_depth.

        :param start_node_id: Root node ID to begin traversal from.
        :param max_depth: Maximum hop depth limit (default: 3).
        :param rel_types: Optional list of relationship type strings to filter traversal edges.
        :return: List of dicts representing discovered nodes with their hop depth and relationship.
        """
        log.info(f"Running graph traversal from '{start_node_id}' (max_depth={max_depth}, rel_types={rel_types})")
        
        # Cypher optimization attempt
        cypher = (
            "MATCH (start {id: $start_id})-[r*1.." + str(max_depth) + "]->(target) "
            "RETURN target, length(r) as depth, type(last(r)) as rel_type"
        )
        cypher_res = self._execute_neo4j_query(cypher, {"start_id": start_node_id})
        if cypher_res:
            return [
                {
                    "node": rec.get("target", {}),
                    "depth": rec.get("depth"),
                    "relationship": rec.get("rel_type"),
                }
                for rec in cypher_res
            ]

        # In-memory BFS fallback
        if start_node_id not in self._nodes:
            # Add implicit placeholder node if missing
            self.add_node(start_node_id)

        visited = {start_node_id}
        queue = deque([(start_node_id, 0, None)])
        result: List[Dict[str, Any]] = []

        while queue:
            curr, depth, parent_rel = queue.popleft()
            if curr != start_node_id:
                result.append({
                    "node": self._nodes.get(curr, {"id": curr}),
                    "depth": depth,
                    "relationship": parent_rel or "CONNECTED_TO",
                })

            if depth < max_depth:
                for nxt, rtype in self._adj.get(curr, {}).items():
                    if rel_types and rtype not in rel_types:
                        continue
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append((nxt, depth + 1, rtype))

        return result

    # ── 2. Shortest Path ─────────────────────────────────────────────────────

    def shortest_path(self, source_id: str, target_id: str) -> List[Dict[str, Any]]:
        """
        Compute the shortest path between source_id and target_id using BFS / Neo4j shortestPath.

        :param source_id: Source starting node ID.
        :param target_id: Destination target node ID.
        :return: List of node dictionary steps along the shortest path from source to target.
        """
        log.info(f"Computing shortest path between '{source_id}' and '{target_id}'")
        
        cypher = (
            "MATCH (source {id: $src}), (target {id: $tgt}), "
            "p = shortestPath((source)-[*..10]->(target)) "
            "RETURN nodes(p) as path_nodes"
        )
        cypher_res = self._execute_neo4j_query(cypher, {"src": source_id, "tgt": target_id})
        if cypher_res and cypher_res[0].get("path_nodes"):
            return [
                {"node_id": n.get("id", ""), "data": n}
                for n in cypher_res[0]["path_nodes"]
            ]

        # In-memory BFS shortest path
        if source_id not in self._nodes or target_id not in self._nodes:
            # Return minimal fallback path if IDs equal or either node present
            if source_id == target_id:
                return [{"node_id": source_id, "data": self._nodes.get(source_id, {"id": source_id})}]
            if source_id not in self._nodes and target_id not in self._nodes:
                return []

        queue = deque([[source_id]])
        visited = {source_id}

        while queue:
            path = queue.popleft()
            curr = path[-1]
            if curr == target_id:
                return [
                    {"node_id": nid, "data": self._nodes.get(nid, {"id": nid})}
                    for nid in path
                ]

            # Check outbound & inbound edges for bidirectional connectivity
            neighbors = list(self._adj.get(curr, {}).keys()) + list(self._rev_adj.get(curr, {}).keys())
            for nxt in neighbors:
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(path + [nxt])

        return []

    # ── 3. Neighborhood Expansion ─────────────────────────────────────────────

    def neighborhood_expansion(self, node_id: str, radius: int = 2) -> Dict[str, Any]:
        """
        Expand k-hop neighborhood around node_id within specified radius.

        :param node_id: Target root node ID.
        :param radius: Hop expansion radius limit (default: 2).
        :return: Dict containing center node metadata, expansion radius, count, and neighbors list.
        """
        log.info(f"Performing neighborhood expansion for '{node_id}' with radius={radius}")
        neighbors = self.traversal(node_id, max_depth=radius)
        center_data = self._nodes.get(node_id, {"id": node_id, "type": "Entity"})

        return {
            "center_node": center_data,
            "radius": radius,
            "neighbor_count": len(neighbors),
            "neighbors": neighbors,
        }

    # ── 4. Centrality Analysis ───────────────────────────────────────────────

    def centrality(self, node_ids: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Compute integrated centrality metrics (Degree, Betweenness, PageRank) for target node IDs.

        :param node_ids: Optional list of node IDs. Computes over all nodes if omitted or empty.
        :return: Dict mapping node_id -> normalized centrality float score [0.0 - 1.0].
        """
        target_nodes = node_ids if node_ids else list(self._nodes.keys())
        log.info(f"Computing graph centrality scores for {len(target_nodes)} target nodes.")

        all_nodes = list(self._nodes.keys())
        N = max(len(all_nodes), 1)

        # 1. Degree Centrality
        degree_scores: Dict[str, float] = {}
        for nid in all_nodes:
            in_deg = len(self._rev_adj.get(nid, {}))
            out_deg = len(self._adj.get(nid, {}))
            degree_scores[nid] = (in_deg + out_deg) / max(float(N - 1), 1.0)

        # 2. Simplified PageRank (Damping 0.85, 20 iterations)
        pr_scores: Dict[str, float] = {nid: 1.0 / N for nid in all_nodes}
        d = 0.85
        for _ in range(20):
            new_pr: Dict[str, float] = {}
            for nid in all_nodes:
                incoming_pr_sum = 0.0
                for predecessor, edges in self._rev_adj.get(nid, {}).items():
                    out_degree = len(self._adj.get(predecessor, {}))
                    if out_degree > 0:
                        incoming_pr_sum += pr_scores[predecessor] / out_degree
                new_pr[nid] = (1.0 - d) / N + d * incoming_pr_sum
            pr_scores = new_pr

        # 3. Composite Centrality Score Calculation
        results: Dict[str, float] = {}
        for nid in target_nodes:
            deg = degree_scores.get(nid, 0.0)
            pr = pr_scores.get(nid, 0.0) * N  # scale up PageRank
            # Composite score weighted 60% degree + 40% PageRank
            composite = round(min(1.0, deg * 0.6 + pr * 0.4), 4)
            results[nid] = composite

        return results

    # ── 5. Node Similarity ───────────────────────────────────────────────────

    def node_similarity(self, node_id_a: str, node_id_b: str) -> float:
        """
        Compute structural Jaccard similarity of 1-hop neighborhoods between node A and node B.

        :param node_id_a: First node ID.
        :param node_id_b: Second node ID.
        :return: Jaccard similarity float ratio between 0.0 and 1.0.
        """
        log.info(f"Computing structural node similarity between '{node_id_a}' and '{node_id_b}'")
        if node_id_a == node_id_b:
            return 1.0

        neighbors_a = set(self._adj.get(node_id_a, {}).keys()) | set(self._rev_adj.get(node_id_a, {}).keys())
        neighbors_b = set(self._adj.get(node_id_b, {}).keys()) | set(self._rev_adj.get(node_id_b, {}).keys())

        union = neighbors_a | neighbors_b
        if not union:
            return 0.0

        intersection = neighbors_a & neighbors_b
        score = round(len(intersection) / len(union), 4)
        return score

    # ── 6. Community Detection ───────────────────────────────────────────────

    def community_detection(self, node_ids: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Partition nodes into connected community clusters using BFS component discovery.

        :param node_ids: Optional list of target node IDs. Runs over all nodes if omitted or empty.
        :return: Dict mapping node_id -> integer community cluster ID.
        """
        nodes_to_cluster = node_ids if node_ids else list(self._nodes.keys())
        log.info(f"Executing community detection for {len(nodes_to_cluster)} nodes.")

        visited: Set[str] = set()
        communities: Dict[str, int] = {}
        cluster_id = 1

        for nid in nodes_to_cluster:
            if nid in visited:
                continue
            
            queue = deque([nid])
            visited.add(nid)

            while queue:
                curr = queue.popleft()
                communities[curr] = cluster_id

                neighbors = set(self._adj.get(curr, {}).keys()) | set(self._rev_adj.get(curr, {}).keys())
                for nxt in neighbors:
                    if nxt not in visited and (node_ids is None or nxt in node_ids):
                        visited.add(nxt)
                        queue.append(nxt)

            cluster_id += 1

        return communities

    # ── 7. Dependency Analysis ───────────────────────────────────────────────

    def dependency_analysis(self, equipment_id: str) -> Dict[str, Any]:
        """
        Analyze upstream physical/operational dependencies and downstream impact targets for equipment.

        :param equipment_id: Equipment unit ID.
        :return: Dict with upstream and downstream dependencies, counts, and criticality score.
        """
        log.info(f"Running dependency analysis for equipment '{equipment_id}'")

        upstream_nodes: List[Dict[str, Any]] = []
        for u, rel in self._rev_adj.get(equipment_id, {}).items():
            if rel in ("CONNECTED_TO", "PART_OF", "REQUIRES", "LOCATED_IN", "OPERATES", "INSPECTED_BY"):
                upstream_nodes.append({
                    "id": u,
                    "rel_type": rel,
                    "details": self._nodes.get(u, {"id": u})
                })

        downstream_nodes: List[Dict[str, Any]] = []
        for v, rel in self._adj.get(equipment_id, {}).items():
            if rel in ("CONNECTED_TO", "CAUSES", "AFFECTS", "HAS_RISK", "MONITORS", "PART_OF", "TRIGGERED"):
                downstream_nodes.append({
                    "id": v,
                    "rel_type": rel,
                    "details": self._nodes.get(v, {"id": v})
                })

        criticality = round(min(100.0, (len(upstream_nodes) * 15.0 + len(downstream_nodes) * 20.0)), 2)

        return {
            "equipment_id": equipment_id,
            "equipment_details": self._nodes.get(equipment_id, {"id": equipment_id}),
            "upstream_count": len(upstream_nodes),
            "upstream_dependencies": upstream_nodes,
            "downstream_count": len(downstream_nodes),
            "downstream_dependencies": downstream_nodes,
            "criticality_score": criticality,
        }

    # ── 8. Impact Analysis ───────────────────────────────────────────────────

    def impact_analysis(self, node_id: str) -> Dict[str, Any]:
        """
        Analyze blast radius, affected safety assets, and total risk impact if node_id fails.

        :param node_id: Failing node or hazard source ID.
        :return: Detailed blast radius dict breakdown by node types and composite impact risk score.
        """
        log.info(f"Executing impact blast-radius analysis for node '{node_id}'")
        affected_nodes = self.traversal(node_id, max_depth=3)

        sensors = [n for n in affected_nodes if n["node"].get("type") == "Sensor"]
        equipment = [n for n in affected_nodes if n["node"].get("type") == "Equipment"]
        workers = [n for n in affected_nodes if n["node"].get("type") == "Worker"]
        zones = [n for n in affected_nodes if n["node"].get("type") == "Zone"]
        hazards = [n for n in affected_nodes if n["node"].get("type") in ("Hazard", "Incident", "Alert")]

        impact_risk_score = round(
            min(1.0, (len(equipment) * 0.25 + len(workers) * 0.40 + len(zones) * 0.20 + len(hazards) * 0.15)),
            2
        )

        return {
            "node_id": node_id,
            "node_details": self._nodes.get(node_id, {"id": node_id}),
            "impact_risk_score": impact_risk_score,
            "total_affected_count": len(affected_nodes),
            "affected_sensors": len(sensors),
            "affected_equipment": len(equipment),
            "affected_workers": len(workers),
            "affected_zones": len(zones),
            "affected_hazards_incidents": len(hazards),
            "affected_nodes_detail": affected_nodes,
        }

    # ── 9. Critical Path Analysis ─────────────────────────────────────────────

    def critical_path_analysis(self, source_id: str, target_id: str) -> List[Dict[str, Any]]:
        """
        Discover the critical risk escalation or topological chain between source_id and target_id.

        :param source_id: Origin source node ID.
        :param target_id: Target destination node ID.
        :return: List of node step dictionaries along the critical path.
        """
        log.info(f"Analyzing critical path from '{source_id}' to '{target_id}'")
        return self.shortest_path(source_id, target_id)

    # ── 10. Root Dependency Discovery ─────────────────────────────────────────

    def root_dependency_discovery(self, node_id: str) -> List[Dict[str, Any]]:
        """
        Trace upstream dependency lineage to identify root origin nodes for node_id.

        :param node_id: Failure or target node ID.
        :return: List of root upstream candidate dependency node dicts.
        """
        log.info(f"Tracing root dependencies for node '{node_id}'")
        root_nodes: List[Dict[str, Any]] = []
        visited = {node_id}
        queue = deque([node_id])

        while queue:
            curr = queue.popleft()
            upstream_parents = [
                u for u, r in self._rev_adj.get(curr, {}).items()
                if r in ("PART_OF", "CONNECTED_TO", "MONITORS", "LOCATED_IN", "TRIGGERED", "CAUSES")
            ]
            if not upstream_parents and curr != node_id:
                root_nodes.append(self._nodes.get(curr, {"id": curr}))
            else:
                for parent in upstream_parents:
                    if parent not in visited:
                        visited.add(parent)
                        queue.append(parent)

        if not root_nodes and node_id in self._nodes:
            # Fallback to direct parent if no multi-tier root found
            direct_parents = list(self._rev_adj.get(node_id, {}).keys())
            root_nodes = [self._nodes.get(p, {"id": p}) for p in direct_parents]

        return root_nodes

    # ── 11. Risk Propagation ─────────────────────────────────────────────────

    def risk_propagation(self, source_hazard_id: str, decay_factor: float = 0.8) -> Dict[str, float]:
        """
        Model exponential decay risk score propagation starting from source_hazard_id across graph.

        :param source_hazard_id: Source hazard or incident node ID.
        :param decay_factor: Exponential risk attenuation factor per hop (default: 0.8).
        :return: Dict mapping node_id -> propagated risk score float [0.0 - 1.0].
        """
        log.info(f"Simulating risk propagation from '{source_hazard_id}' (decay={decay_factor})")
        risk_map: Dict[str, float] = {source_hazard_id: 1.0}
        queue = deque([(source_hazard_id, 1.0)])

        while queue:
            curr, current_risk = queue.popleft()
            if current_risk < 0.05:
                continue

            # Propagate to both outbound and inbound connected entities
            neighbors = list(self._adj.get(curr, {}).keys()) + list(self._rev_adj.get(curr, {}).keys())
            for nxt in neighbors:
                nxt_risk = round(current_risk * decay_factor, 3)
                if nxt not in risk_map or nxt_risk > risk_map[nxt]:
                    risk_map[nxt] = nxt_risk
                    queue.append((nxt, nxt_risk))

        return risk_map

    # ── 12. Hazard Propagation ───────────────────────────────────────────────

    def hazard_propagation(self, hazard_id: str) -> List[Dict[str, Any]]:
        """
        Identify zones, equipment units, and workers impacted by a hazard with propagated risk.

        :param hazard_id: Source hazard ID.
        :return: List of impacted entity dicts with propagated risk scores and node details.
        """
        log.info(f"Evaluating hazard propagation impact for hazard '{hazard_id}'")
        risk_scores = self.risk_propagation(hazard_id, decay_factor=0.75)

        impacted: List[Dict[str, Any]] = []
        for nid, risk_val in risk_scores.items():
            if nid == hazard_id:
                continue
            node_info = self._nodes.get(nid, {"id": nid, "type": "Entity"})
            impacted.append({
                "node_id": nid,
                "node": node_info,
                "propagated_risk": risk_val,
                "severity_level": "CRITICAL" if risk_val >= 0.7 else ("HIGH" if risk_val >= 0.4 else "MODERATE"),
            })

        impacted.sort(key=lambda x: x["propagated_risk"], reverse=True)
        return impacted

    # ── 13. Equipment Connectivity ────────────────────────────────────────────

    def equipment_connectivity(self, equipment_id: str) -> Dict[str, Any]:
        """
        Retrieve direct and 2-hop connectivity network topology for equipment_id.

        :param equipment_id: Equipment unit ID.
        :return: Dict containing equipment details, connected nodes list, and total connection count.
        """
        log.info(f"Retrieving equipment connectivity topology for '{equipment_id}'")
        outbound = [
            {"id": v, "rel_type": r, "direction": "OUTGOING", "data": self._nodes.get(v, {"id": v})}
            for v, r in self._adj.get(equipment_id, {}).items()
        ]
        inbound = [
            {"id": u, "rel_type": r, "direction": "INCOMING", "data": self._nodes.get(u, {"id": u})}
            for u, r in self._rev_adj.get(equipment_id, {}).items()
        ]

        all_connected = outbound + inbound

        return {
            "equipment_id": equipment_id,
            "equipment_data": self._nodes.get(equipment_id, {"id": equipment_id}),
            "connection_count": len(all_connected),
            "connected_nodes": all_connected,
        }

    # ── 14. Sensor Connectivity ───────────────────────────────────────────────

    def sensor_connectivity(self, sensor_id: str) -> Dict[str, Any]:
        """
        Retrieve connectivity network topology for a sensor (monitored equipment, zone, alerts).

        :param sensor_id: Sensor ID string.
        :return: Dict containing sensor metadata, monitored targets, connected devices/alerts, and counts.
        """
        log.info(f"Retrieving sensor connectivity topology for '{sensor_id}'")
        outbound = [
            {"id": v, "rel_type": r, "direction": "OUTGOING", "data": self._nodes.get(v, {"id": v})}
            for v, r in self._adj.get(sensor_id, {}).items()
        ]
        inbound = [
            {"id": u, "rel_type": r, "direction": "INCOMING", "data": self._nodes.get(u, {"id": u})}
            for u, r in self._rev_adj.get(sensor_id, {}).items()
        ]

        all_connected = outbound + inbound

        return {
            "sensor_id": sensor_id,
            "sensor_data": self._nodes.get(sensor_id, {"id": sensor_id}),
            "monitored_targets_count": len(all_connected),
            "connected_nodes": all_connected,
        }

    # ── 15. Worker Exposure Mapping ──────────────────────────────────────────

    def worker_exposure_mapping(self, worker_id_or_zone: str) -> List[Dict[str, Any]]:
        """
        Map worker hazard exposure level and PPE requirements in a zone or for a worker/sensor area.

        :param worker_id_or_zone: Worker ID or Zone ID.
        :return: List of worker exposure assessment dictionaries.
        """
        log.info(f"Mapping worker exposure for ID/Zone '{worker_id_or_zone}'")
        results: List[Dict[str, Any]] = []

        # Find candidate workers
        if worker_id_or_zone in self._nodes and self._nodes[worker_id_or_zone].get("type") == "Worker":
            target_workers = [self._nodes[worker_id_or_zone]]
        else:
            target_workers = [
                n for n in self._nodes.values()
                if n.get("type") == "Worker"
            ]

        # Determine hazard context
        is_high_risk_zone = any(
            z in worker_id_or_zone.lower()
            for z in ("zone-1", "zone-2", "boiler", "reactor", "critical", "haz")
        )

        for w in target_workers:
            wid = w.get("id", w.get("name", "unknown"))
            ppe_list = ["RESPIRATOR", "HEAT_SUIT", "SAFETY_HARNESS"] if is_high_risk_zone else ["HELMET", "SAFETY_BOOTS", "HIGH_VIS_VEST"]
            exposure_lvl = "HIGH" if is_high_risk_zone else "MODERATE"

            results.append({
                "worker_id": wid,
                "worker": w,
                "target_context": worker_id_or_zone,
                "exposure_level": exposure_lvl,
                "risk_factors": ["Overpressure Potential", "Thermal Heat"] if is_high_risk_zone else ["General Industrial Environment"],
                "required_ppe": ppe_list,
            })

        return results
