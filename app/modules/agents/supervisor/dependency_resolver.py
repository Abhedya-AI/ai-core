"""dependency_resolver.py — Workflow Dependency Resolver.

Determines the execution DAG order between specialized agents based on
input/output data dependencies.
"""

from app.core.logging import get_logger

log = get_logger("agents.supervisor.dependency_resolver")

# Standard dependency graph: Agent → List of prerequisite agents
_AGENT_DEPENDENCIES: dict[str, list[str]] = {
    "VisionAgent": [],
    "DocumentAgent": [],
    "RiskAgent": ["VisionAgent"],
    "PredictionAgent": ["VisionAgent"],
    "RootCauseAgent": ["VisionAgent", "RiskAgent"],
    "ComplianceAgent": ["DocumentAgent"],
    "EmergencyAgent": ["RiskAgent", "PredictionAgent"],
    "NotificationAgent": ["EmergencyAgent", "ComplianceAgent", "RiskAgent"],
}


class DependencyResolver:
    """
    Resolves dependencies between specialized agents to create valid topological stages.
    """

    def resolve_stages(self, requested_agent_names: list[str]) -> list[list[str]]:
        """
        Group requested agents into topological stages where each stage contains
        agents that can run in parallel, and later stages depend on earlier stages.

        Args:
            requested_agent_names: List of agent names to execute.

        Returns:
            List of stages, where each stage is a list of agent names that can run in parallel.
        """
        requested_set = set(requested_agent_names)

        # Build in-degree map and adjacency list for requested subset
        in_degree: dict[str, int] = {name: 0 for name in requested_set}
        deps_map: dict[str, list[str]] = {name: [] for name in requested_set}

        for agent_name in requested_set:
            prereqs = _AGENT_DEPENDENCIES.get(agent_name, [])
            for prereq in prereqs:
                if prereq in requested_set:
                    in_degree[agent_name] += 1
                    deps_map[prereq].append(agent_name)

        stages: list[list[str]] = []
        visited: set[str] = set()

        while len(visited) < len(requested_set):
            # Find all nodes with in-degree 0 among unvisited
            current_stage = [
                node for node in requested_set
                if node not in visited and in_degree[node] == 0
            ]

            if not current_stage:
                # Cycle or resolution stuck — break fallback
                remaining = list(requested_set - visited)
                log.warning(f"DependencyResolver: deadlock/cycle detected. Remaining agents: {remaining}")
                stages.append(remaining)
                break

            stages.append(current_stage)
            for node in current_stage:
                visited.add(node)
                for successor in deps_map[node]:
                    in_degree[successor] -= 1

        log.info(
            f"DependencyResolver: resolved {len(requested_agent_names)} agents "
            f"into {len(stages)} stage(s): {stages}"
        )
        return stages
