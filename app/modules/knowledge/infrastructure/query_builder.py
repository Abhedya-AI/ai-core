"""
query_builder.py — Fluent Cypher Query Builder.

Enables programmatic query construction for complex searches while automatically
parameterizing inputs to guarantee safe Cypher execution.
"""

from typing import Any


class GraphQueryBuilder:
    """Fluent API builder for parameterized Cypher MATCH queries."""

    def __init__(self) -> None:
        self._start_node: str | None = None
        self._where_conditions: list[str] = []
        self._relationships: list[str] = []
        self._target_nodes: list[str] = []
        self._params: dict[str, Any] = {}
        self._param_counter: int = 0
        self._limit: int | None = None

    def node(self, label: str, alias: str = "n") -> "GraphQueryBuilder":
        """Define the starting node label."""
        self._start_node = f"({alias}:{label})"
        self._current_alias = alias
        return self

    def where(self, **kwargs: Any) -> "GraphQueryBuilder":
        """Add property equality filters."""
        for key, val in kwargs.items():
            param_key = f"{key}_{self._param_counter}"
            self._param_counter += 1
            self._where_conditions.append(f"{self._current_alias}.{key} = ${param_key}")
            self._params[param_key] = val
        return self

    def related(self, rel_type: str, direction: str = "OUTGOING") -> "GraphQueryBuilder":
        """Add a relationship hop."""
        if direction == "OUTGOING":
            rel_str = f"-[r:{rel_type}]->"
        elif direction == "INCOMING":
            rel_str = f"<-[r:{rel_type}]-"
        else:
            rel_str = f"-[r:{rel_type}]-"
        self._relationships.append(rel_str)
        return self

    def to(self, label: str, alias: str = "m") -> "GraphQueryBuilder":
        """Define the target node of the relationship hop."""
        self._target_nodes.append(f"({alias}:{label})")
        self._current_alias = alias
        return self

    def limit(self, max_results: int) -> "GraphQueryBuilder":
        """Set query result limit."""
        self._limit = max_results
        return self

    def build(self) -> tuple[str, dict[str, Any]]:
        """
        Build and return the Cypher query string and parameter dict.

        Returns:
            tuple[query_string, parameters_dict]
        """
        if not self._start_node:
            raise ValueError("Query builder requires a starting node: .node('Label')")

        cypher_parts = [f"MATCH {self._start_node}"]

        if self._relationships and self._target_nodes:
            cypher_parts.append(f"{self._relationships[0]}{self._target_nodes[0]}")

        if self._where_conditions:
            cypher_parts.append(f"WHERE {' AND '.join(self._where_conditions)}")

        return_alias = self._current_alias if hasattr(self, "_current_alias") else "n"
        cypher_parts.append(f"RETURN {return_alias}")

        if self._limit:
            cypher_parts.append(f"LIMIT {self._limit}")

        return " ".join(cypher_parts), self._params
