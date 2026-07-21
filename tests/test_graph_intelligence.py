from app.modules.knowledge.graph_intelligence import IntelligenceService
from app.modules.knowledge.graph_intelligence.algorithms import (
    bfs_traversal,
    compute_centrality,
    compute_jaccard_similarity,
    compute_pagerank,
    detect_communities,
    dfs_traversal,
    find_connected_components,
    find_shortest_path_algo,
    k_hop_expansion,
    topological_sort_dag,
)
from app.modules.knowledge.graph_intelligence.causality import find_root_causes
from app.modules.knowledge.graph_intelligence.dependency import analyze_asset_dependencies
from app.modules.knowledge.graph_intelligence.explainability import (
    format_causal_explanation,
    format_risk_explanation,
)
from app.modules.knowledge.graph_intelligence.risk import propagate_risk, simulate_cascading_failure


def test_bfs_dfs_algorithms():
    """Verify BFS and DFS traversal algorithms."""
    adj = {
        "A": ["B", "C"],
        "B": ["D"],
        "C": ["E"],
        "D": [],
        "E": [],
    }
    bfs_res = bfs_traversal(adj, "A", max_depth=2)
    assert "A" in bfs_res.affected_nodes
    assert "B" in bfs_res.affected_nodes
    assert "D" in bfs_res.affected_nodes
    assert bfs_res.algorithm == "BFS"

    dfs_res = dfs_traversal(adj, "A", max_depth=3)
    assert len(dfs_res.affected_nodes) == 5
    assert dfs_res.algorithm == "DFS"


def test_shortest_path_and_khop():
    """Verify shortest path and k-hop neighborhood expansion algorithms."""
    adj = {
        "S-1": ["EQ-1"],
        "EQ-1": ["HZ-1"],
        "HZ-1": ["INC-1"],
        "INC-1": [],
    }
    path_res = find_shortest_path_algo(adj, "S-1", "INC-1")
    assert path_res.affected_nodes == ["S-1", "EQ-1", "HZ-1", "INC-1"]
    assert path_res.metadata["path_length"] == 3

    khop_res = k_hop_expansion(adj, "S-1", k=2)
    assert "HZ-1" in khop_res.affected_nodes
    assert "INC-1" not in khop_res.affected_nodes


def test_pagerank_centrality_communities():
    """Verify graph centrality, PageRank, connected components, and community detection."""
    adj = {
        "NodeA": ["NodeB", "NodeC"],
        "NodeB": ["NodeC"],
        "NodeC": ["NodeA"],
        "NodeD": [],
    }
    pr_res = compute_pagerank(adj)
    assert len(pr_res.metadata["ranks"]) == 4

    cent_res = compute_centrality(adj)
    assert "NodeC" in cent_res.affected_nodes

    comp_res = find_connected_components(adj)
    assert comp_res.metadata["num_components"] == 2

    comm_res = detect_communities(adj)
    assert "communities" in comm_res.metadata

    sim_res = compute_jaccard_similarity(adj, "NodeA", "NodeB")
    assert sim_res.metadata["similarity_score"] == 0.5

    topo_res = topological_sort_dag({"X": ["Y"], "Y": ["Z"], "Z": []})
    assert topo_res.metadata["order"] == ["X", "Y", "Z"]


def test_risk_propagation_and_cascading():
    """Verify risk propagation and cascading failure simulations."""
    adj = {
        "HZ-GAS": ["PIPE-1"],
        "PIPE-1": ["VALVE-2"],
        "VALVE-2": ["TANK-3"],
        "TANK-3": ["ZONE-A"],
    }
    risk_report = propagate_risk(adj, "HZ-GAS", initial_risk=100.0, attenuation_factor=0.5, max_hops=3)
    assert risk_report.propagated_risk_scores["HZ-GAS"] == 100.0
    assert risk_report.propagated_risk_scores["PIPE-1"] == 50.0
    assert risk_report.propagated_risk_scores["VALVE-2"] == 25.0

    casc_res = simulate_cascading_failure(adj, "HZ-GAS")
    assert len(casc_res.affected_nodes) == 5


def test_root_cause_analysis():
    """Verify root cause analysis backwards graph search."""
    # Incoming causality edges: target -> list of causes
    incoming = {
        "EXPLOSION": ["GAS_LEAK"],
        "GAS_LEAK": ["VALVE_FAILURE"],
        "VALVE_FAILURE": ["PRESSURE_BREACH"],
        "PRESSURE_BREACH": ["SENSOR_FAILURE"],
    }
    causal_report = find_root_causes(incoming, "EXPLOSION")
    assert "SENSOR_FAILURE" in causal_report.candidate_root_causes
    assert causal_report.causal_path[0] == "SENSOR_FAILURE"
    assert causal_report.causal_path[-1] == "EXPLOSION"


def test_dependency_analysis():
    """Verify upstream/downstream asset dependency analysis."""
    downstream = {"PUMP-A": ["COOLING-B", "GENERATOR-C"]}
    upstream = {"PUMP-A": ["POWER-GRID"]}

    dep_report = analyze_asset_dependencies(downstream, upstream, "PUMP-A")
    assert dep_report.downstream_impacts == ["COOLING-B", "GENERATOR-C"]
    assert dep_report.upstream_dependencies == ["POWER-GRID"]
    assert dep_report.criticality_score == 50.0


def test_explainability():
    """Verify human-readable explainability formatting."""
    exp = format_risk_explanation("VALVE-1", 85.0, "HZ-GAS", ["Overpressure", "Maintenance Overdue"])
    assert "VALVE-1" in exp
    assert "85.0/100" in exp
    assert "HZ-GAS" in exp


def test_intelligence_service_master_orchestrator():
    """Verify Master IntelligenceService orchestrates end-to-end reasoning."""
    adj = {"SENSOR-1": ["VALVE-1"], "VALVE-1": ["INCIDENT-1"]}
    incoming = {"INCIDENT-1": ["VALVE-1"], "VALVE-1": ["SENSOR-1"]}

    # Incident Analysis
    causal_rep = IntelligenceService.analyze_incident("INCIDENT-1", incoming)
    assert "SENSOR-1" in causal_rep.candidate_root_causes
    assert "Root Cause Explanation" in causal_rep.intelligence_result.explanation

    # Risk Propagation
    risk_rep = IntelligenceService.analyze_risk_propagation("SENSOR-1", adj, initial_risk=100.0)
    assert "SENSOR-1" in risk_rep.propagated_risk_scores
    assert "Risk Assessment for Node" in risk_rep.intelligence_result.explanation

    # Asset Criticality
    crit_rep = IntelligenceService.analyze_asset_criticality("VALVE-1", adj, {"VALVE-1": ["INCIDENT-1"]}, {"VALVE-1": ["SENSOR-1"]})
    assert crit_rep.criticality_score > 0
    assert "Industrial Criticality Score" in crit_rep.intelligence_result.explanation
