"""
query_builder.py — Production Fluent Cypher Query Builder.

Extended with: MERGE, OPTIONAL MATCH, CREATE, UNWIND, CALL, WITH,
ORDER BY, SKIP, multi-alias RETURN, typed relationship direction,
WHERE IN, WHERE CONTAINS, SET properties, DELETE.

Usage:
    query, params = (
        GraphQueryBuilder()
        .node('Equipment', 'e')
        .where(status='OPERATIONAL')
        .order_by('e.name')
        .limit(20)
        .build()
    )

    merge_query, params = (
        GraphQueryBuilder()
        .merge('Sensor', {'id': sensor_id}, {'name': name, 'status': status})
        .build_merge()
    )
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class _QueryMode(str, Enum):
    MATCH = "MATCH"
    MERGE = "MERGE"
    CREATE = "CREATE"


class GraphQueryBuilder:
    """
    Fluent API builder for parameterized Cypher queries.

    Builds MATCH, MERGE, and CREATE queries with full support for:
      - WHERE equality, IN, CONTAINS (case-insensitive)
      - Relationships with direction and hop ranges
      - OPTIONAL MATCH
      - UNWIND + WITH
      - ORDER BY / SKIP / LIMIT
      - SET properties
      - DETACH DELETE
      - Multi-alias RETURN
    """

    def __init__(self) -> None:
        self._mode: _QueryMode = _QueryMode.MATCH
        self._clauses: list[str] = []
        self._params: dict[str, Any] = {}
        self._counter: int = 0
        self._current_alias: str = "n"
        self._return_aliases: list[str] = []
        self._order_by_clause: str | None = None
        self._skip_value: int | None = None
        self._limit_value: int | None = None
        self._set_clauses: list[str] = []
        self._delete_clause: str | None = None
        self._merge_match_props: dict[str, Any] = {}
        self._merge_set_props: dict[str, Any] = {}
        self._merge_label: str | None = None
        self._merge_alias: str = "n"

    # ── Parameter Helpers ──────────────────────────────────────────────────────

    def _next_param(self, prefix: str = "p") -> str:
        key = f"{prefix}_{self._counter}"
        self._counter += 1
        return key

    # ── Start Clauses ──────────────────────────────────────────────────────────

    def node(self, label: str, alias: str = "n") -> "GraphQueryBuilder":
        """Define starting MATCH node: MATCH (alias:label)"""
        self._mode = _QueryMode.MATCH
        self._current_alias = alias
        self._return_aliases = [alias]
        self._clauses = [f"MATCH ({alias}:{label})"]
        return self

    def node_any(self, alias: str = "n") -> "GraphQueryBuilder":
        """MATCH any node without label: MATCH (alias)"""
        self._mode = _QueryMode.MATCH
        self._current_alias = alias
        self._return_aliases = [alias]
        self._clauses = [f"MATCH ({alias})"]
        return self

    def optional_match(self, pattern: str) -> "GraphQueryBuilder":
        """Add an OPTIONAL MATCH clause."""
        self._clauses.append(f"OPTIONAL MATCH {pattern}")
        return self

    def create(self, label: str, alias: str = "n", properties: dict[str, Any] | None = None) -> "GraphQueryBuilder":
        """Switch to CREATE mode."""
        self._mode = _QueryMode.CREATE
        self._current_alias = alias
        self._return_aliases = [alias]
        if properties:
            pkey = self._next_param("props")
            self._params[pkey] = properties
            self._clauses = [f"CREATE ({alias}:{label} ${pkey})"]
        else:
            self._clauses = [f"CREATE ({alias}:{label})"]
        return self

    def merge(
        self,
        label: str,
        match_props: dict[str, Any],
        set_props: dict[str, Any] | None = None,
        alias: str = "n",
    ) -> "GraphQueryBuilder":
        """
        Build a MERGE clause.

        MERGE (alias:Label {match_key: $match_val})
        ON CREATE SET alias += $create_props, alias.created_at = $now
        ON MATCH SET alias += $update_props, alias.updated_at = $now
        """
        self._mode = _QueryMode.MERGE
        self._merge_label = label
        self._merge_alias = alias
        self._merge_match_props = match_props
        self._merge_set_props = set_props or {}
        self._current_alias = alias
        self._return_aliases = [alias]
        return self

    # ── Relationship Traversal ─────────────────────────────────────────────────

    def related(self, rel_type: str, direction: str = "OUTGOING") -> "GraphQueryBuilder":
        """Append a single-hop relationship to the current MATCH chain."""
        if direction == "OUTGOING":
            arrow = f"-[r:{rel_type}]->"
        elif direction == "INCOMING":
            arrow = f"<-[r:{rel_type}]-"
        else:
            arrow = f"-[r:{rel_type}]-"
        self._clauses[-1] = self._clauses[-1] + arrow
        return self

    def relationship(
        self,
        rel_type: str,
        alias: str = "r",
        direction: str = "OUTGOING",
        min_hops: int = 1,
        max_hops: int = 1,
    ) -> "GraphQueryBuilder":
        """Typed relationship with hop range."""
        hops = f"*{min_hops}..{max_hops}" if (min_hops != 1 or max_hops != 1) else ""
        if direction == "OUTGOING":
            arrow = f"-[{alias}:{rel_type}{hops}]->"
        elif direction == "INCOMING":
            arrow = f"<-[{alias}:{rel_type}{hops}]-"
        else:
            arrow = f"-[{alias}:{rel_type}{hops}]-"
        self._clauses[-1] = self._clauses[-1] + arrow
        return self

    def to(self, label: str, alias: str = "m") -> "GraphQueryBuilder":
        """Append target node to the current pattern."""
        self._current_alias = alias
        self._return_aliases = [alias]
        self._clauses[-1] = self._clauses[-1] + f"({alias}:{label})"
        return self

    def to_any(self, alias: str = "m") -> "GraphQueryBuilder":
        """Append unlabeled target node."""
        self._current_alias = alias
        self._return_aliases = [alias]
        self._clauses[-1] = self._clauses[-1] + f"({alias})"
        return self

    # ── Filtering ──────────────────────────────────────────────────────────────

    def where(self, **kwargs: Any) -> "GraphQueryBuilder":
        """WHERE alias.key = $value (equality)."""
        conditions: list[str] = []
        for key, val in kwargs.items():
            pkey = self._next_param(key)
            conditions.append(f"{self._current_alias}.{key} = ${pkey}")
            self._params[pkey] = val
        if conditions:
            self._clauses.append(f"WHERE {' AND '.join(conditions)}")
        return self

    def where_in(self, field: str, values: list[Any], node_alias: str | None = None) -> "GraphQueryBuilder":
        """WHERE alias.field IN $values"""
        alias = node_alias or self._current_alias
        pkey = self._next_param(field)
        self._params[pkey] = values
        self._clauses.append(f"WHERE {alias}.{field} IN ${pkey}")
        return self

    def where_contains(
        self,
        field: str,
        value: str,
        node_alias: str | None = None,
        case_insensitive: bool = True,
    ) -> "GraphQueryBuilder":
        """WHERE toLower(alias.field) CONTAINS toLower($value)"""
        alias = node_alias or self._current_alias
        pkey = self._next_param(field)
        self._params[pkey] = value
        if case_insensitive:
            self._clauses.append(f"WHERE toLower(coalesce({alias}.{field}, '')) CONTAINS toLower(${pkey})")
        else:
            self._clauses.append(f"WHERE {alias}.{field} CONTAINS ${pkey}")
        return self

    def where_raw(self, condition: str, **params: Any) -> "GraphQueryBuilder":
        """Inject a raw WHERE clause with explicit parameter bindings."""
        self._params.update(params)
        self._clauses.append(f"WHERE {condition}")
        return self

    def and_where(self, **kwargs: Any) -> "GraphQueryBuilder":
        """AND additional equality filters on the last WHERE clause."""
        conditions: list[str] = []
        for key, val in kwargs.items():
            pkey = self._next_param(key)
            conditions.append(f"{self._current_alias}.{key} = ${pkey}")
            self._params[pkey] = val
        if conditions and self._clauses:
            # Check if last clause was a WHERE — append AND
            last = self._clauses[-1]
            if last.startswith("WHERE"):
                self._clauses[-1] = last + " AND " + " AND ".join(conditions)
            else:
                self._clauses.append(f"WHERE {' AND '.join(conditions)}")
        return self

    # ── Mutation Clauses ───────────────────────────────────────────────────────

    def set_properties(self, props: dict[str, Any], alias: str | None = None) -> "GraphQueryBuilder":
        """SET alias += $props"""
        target = alias or self._current_alias
        pkey = self._next_param("set_props")
        self._params[pkey] = props
        self._set_clauses.append(f"{target} += ${pkey}")
        return self

    def set_field(self, field: str, value: Any, alias: str | None = None) -> "GraphQueryBuilder":
        """SET alias.field = $value"""
        target = alias or self._current_alias
        pkey = self._next_param(field)
        self._params[pkey] = value
        self._set_clauses.append(f"{target}.{field} = ${pkey}")
        return self

    def delete(self, alias: str | None = None, detach: bool = True) -> "GraphQueryBuilder":
        """[DETACH] DELETE alias"""
        target = alias or self._current_alias
        prefix = "DETACH DELETE" if detach else "DELETE"
        self._delete_clause = f"{prefix} {target}"
        return self

    # ── Control Flow ───────────────────────────────────────────────────────────

    def unwind(self, param: str, alias: str) -> "GraphQueryBuilder":
        """UNWIND $param AS alias"""
        self._clauses.append(f"UNWIND ${param} AS {alias}")
        self._current_alias = alias
        return self

    def with_clause(self, *aliases: str) -> "GraphQueryBuilder":
        """WITH alias1, alias2, ..."""
        self._clauses.append(f"WITH {', '.join(aliases)}")
        return self

    def call(self, procedure: str, *yield_fields: str) -> "GraphQueryBuilder":
        """CALL procedure YIELD field1, field2"""
        if yield_fields:
            self._clauses.append(f"CALL {procedure} YIELD {', '.join(yield_fields)}")
        else:
            self._clauses.append(f"CALL {procedure}")
        return self

    # ── Result Shaping ─────────────────────────────────────────────────────────

    def returns(self, *aliases: str) -> "GraphQueryBuilder":
        """Explicitly set RETURN aliases."""
        self._return_aliases = list(aliases)
        return self

    def order_by(self, field: str, desc: bool = False) -> "GraphQueryBuilder":
        """ORDER BY field [DESC]"""
        direction = " DESC" if desc else ""
        self._order_by_clause = f"ORDER BY {field}{direction}"
        return self

    def skip(self, offset: int) -> "GraphQueryBuilder":
        """SKIP $offset"""
        self._skip_value = offset
        return self

    def limit(self, max_results: int) -> "GraphQueryBuilder":
        """LIMIT $limit"""
        self._limit_value = max_results
        return self

    # ── Build ──────────────────────────────────────────────────────────────────

    def _append_set_delete(self, parts: list[str]) -> None:
        if self._set_clauses:
            parts.append(f"SET {', '.join(self._set_clauses)}")
        if self._delete_clause:
            parts.append(self._delete_clause)

    def _append_return_order_limit(self, parts: list[str]) -> None:
        if self._return_aliases and not self._delete_clause:
            parts.append(f"RETURN {', '.join(self._return_aliases)}")
        if self._order_by_clause:
            parts.append(self._order_by_clause)
        if self._skip_value is not None:
            self._params["__skip"] = self._skip_value
            parts.append("SKIP $__skip")
        if self._limit_value is not None:
            self._params["__limit"] = self._limit_value
            parts.append("LIMIT $__limit")

    def build(self) -> tuple[str, dict[str, Any]]:
        """Build and return (query_string, parameters_dict) for the current mode."""
        if self._mode == _QueryMode.MERGE:
            return self.build_merge()
        if self._mode == _QueryMode.CREATE:
            return self.build_create()
        return self.build_match()

    def build_match(self) -> tuple[str, dict[str, Any]]:
        """Assemble a MATCH query."""
        if not self._clauses:
            raise ValueError("GraphQueryBuilder: no clauses defined — call .node() first")
        parts = list(self._clauses)
        self._append_set_delete(parts)
        self._append_return_order_limit(parts)
        return "\n".join(parts), dict(self._params)

    def build_merge(self) -> tuple[str, dict[str, Any]]:
        """Assemble a MERGE + ON CREATE/MATCH SET query."""
        if not self._merge_label:
            raise ValueError("GraphQueryBuilder: call .merge() before .build_merge()")
        alias = self._merge_alias

        # Build match property filter
        match_conditions: list[str] = []
        for key, val in self._merge_match_props.items():
            pkey = self._next_param(f"match_{key}")
            match_conditions.append(f"{key}: ${pkey}")
            self._params[pkey] = val
        match_str = ", ".join(match_conditions)

        parts = [f"MERGE ({alias}:{self._merge_label} {{{match_str}}})"]

        if self._merge_set_props:
            sp_key = self._next_param("set_props")
            self._params[sp_key] = self._merge_set_props
            self._params["__now"] = "__CURRENT_TIMESTAMP__"
            parts.append(
                f"ON CREATE SET {alias} += ${sp_key}, {alias}.created_at = datetime()\n"
                f"ON MATCH  SET {alias} += ${sp_key}, {alias}.updated_at = datetime()"
            )

        for extra_clause in self._clauses:
            parts.append(extra_clause)

        self._append_set_delete(parts)
        self._append_return_order_limit(parts)
        return "\n".join(parts), dict(self._params)

    def build_create(self) -> tuple[str, dict[str, Any]]:
        """Assemble a CREATE query."""
        if not self._clauses:
            raise ValueError("GraphQueryBuilder: call .create() first")
        parts = list(self._clauses)
        self._append_set_delete(parts)
        self._append_return_order_limit(parts)
        return "\n".join(parts), dict(self._params)

    # ── Pagination Helper ──────────────────────────────────────────────────────

    @staticmethod
    def paginate(offset: int = 0, page_size: int = 20) -> dict[str, int]:
        """Return skip/limit params for use in raw Cypher queries."""
        return {"skip": offset, "limit": page_size}
