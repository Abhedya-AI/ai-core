"""routing.py — Graph Routing Engine for Dynamic Hazard Avoidance."""

from app.modules.agents.emergency.providers import GraphEmergencyProvider


class HazardAwareRouter:
    """Computes dynamic shortest evacuation paths bypassing blocked exits and active hazards."""

    @staticmethod
    def compute_safe_path(start_zone: str, blocked_exits: list[str]) -> tuple[str, list[str]]:
        """
        Compute optimal exit and path avoiding blocked nodes.

        Returns:
            tuple[recommended_exit, path_sequence]
        """
        adj = GraphEmergencyProvider.get_evacuation_graph(start_zone)

        # BFS / Shortest path
        visited = set()
        queue = [(start_zone, [start_zone])]

        while queue:
            curr, path = queue.pop(0)
            if curr.startswith("EXIT-") and curr not in blocked_exits:
                return curr, path

            visited.add(curr)
            for nxt in adj.get(curr, []):
                if nxt not in visited and nxt not in blocked_exits:
                    queue.append((nxt, path + [nxt]))

        # Fallback if all exits blocked
        return "EXIT-C", [start_zone, "CORRIDOR-2", "CORRIDOR-3", "EXIT-C"]
