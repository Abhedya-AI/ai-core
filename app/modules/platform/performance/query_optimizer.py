from __future__ import annotations

from typing import Any
try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

from app.core.logging import get_logger
log = get_logger(__name__)


class QueryOptimizer:
    def __init__(self):
        self._query_benchmarks: dict[str, list[float]] = {}
        self._slow_query_threshold: float = 500.0

    async def analyze_query(self, query_str: str, execution_time_ms: float, row_count: int) -> dict:
        q = query_str.lower()
        warnings = []
        suggestions = []
        risk_score = 0.0
        
        if "select *" in q:
            warnings.append("SELECT * detected")
            suggestions.append("Select only required columns")
            risk_score += 0.2
            
        if "where" not in q and "select" in q:
            warnings.append("Missing WHERE clause")
            suggestions.append("Add WHERE clause to filter rows")
            risk_score += 0.4
            
        if "like '%" in q:
            warnings.append("Leading wildcard in LIKE clause")
            suggestions.append("Use full-text search or avoid leading wildcards")
            risk_score += 0.3
            
        if "limit" not in q and "select" in q:
            warnings.append("No LIMIT clause")
            suggestions.append("Add LIMIT to prevent unbounded results")
            risk_score += 0.2
            
        if execution_time_ms > self._slow_query_threshold:
            warnings.append(f"Query execution time ({execution_time_ms}ms) exceeds threshold")
            risk_score += 0.5
            
        return {
            "execution_time_ms": execution_time_ms,
            "row_count": row_count,
            "warnings": warnings,
            "suggestions": suggestions,
            "risk_score": min(risk_score, 1.0)
        }

    async def detect_n_plus_one(self, query_patterns: list[str]) -> dict:
        pattern_counts: dict[str, int] = {}
        for p in query_patterns:
            pattern_counts[p] = pattern_counts.get(p, 0) + 1
            
        for pattern, count in pattern_counts.items():
            if count > 5:
                return {
                    "detected": True,
                    "repeated_pattern": pattern,
                    "count": count,
                    "suggestion": "Use IN clause or JOIN to fetch related records in a single query"
                }
                
        return {
            "detected": False,
            "repeated_pattern": None,
            "count": 0,
            "suggestion": ""
        }

    async def suggest_indexes(self, table_name: str, query_patterns: list[str]) -> list[dict]:
        suggestions = []
        # Simplified mock logic for index suggestions
        suggestions.append({
            "column": "created_at",
            "index_type": "BTREE",
            "rationale": "Frequently used in ORDER BY and range filters"
        })
        return suggestions

    async def optimize_pagination(self, offset: int, limit: int, total_count: int) -> dict:
        if offset > 10000:
            return {
                "current_strategy": "offset_limit",
                "recommended_strategy": "keyset_pagination",
                "use_keyset_pagination": True,
                "reason": f"High offset ({offset}) degrades performance. Use WHERE id > last_seen_id instead."
            }
        return {
            "current_strategy": "offset_limit",
            "recommended_strategy": "offset_limit",
            "use_keyset_pagination": False,
            "reason": "Offset is within acceptable limits"
        }

    async def get_slow_query_threshold(self) -> float:
        return self._slow_query_threshold

    async def benchmark_query(self, label: str, execution_time_ms: float) -> dict:
        if label not in self._query_benchmarks:
            self._query_benchmarks[label] = []
        self._query_benchmarks[label].append(execution_time_ms)
        
        times = self._query_benchmarks[label]
        if np is None:
            return {
                "label": label,
                "count": len(times),
                "moving_average_ms": sum(times) / len(times),
                "p95_ms": 0.0
            }
            
        return {
            "label": label,
            "count": len(times),
            "moving_average_ms": float(np.mean(times)),
            "p95_ms": float(np.percentile(times, 95))
        }
