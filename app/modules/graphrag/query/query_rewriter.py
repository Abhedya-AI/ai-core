"""query_rewriter.py — Query Standardization / Rewriting module."""

from app.modules.graphrag.query.parser import ParsedQuery


def rewrite_query_for_retrieval(parsed_query: ParsedQuery) -> str:
    """Standardize query string for optimal embedding and vector retrieval."""
    entities_str = ", ".join(parsed_query.entity_ids) if parsed_query.entity_ids else ""
    if entities_str:
        return f"{parsed_query.raw_query} (Focus Entities: {entities_str})"
    return parsed_query.raw_query
