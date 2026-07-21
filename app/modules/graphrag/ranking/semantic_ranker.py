"""semantic_ranker.py — Vector similarity ranker."""

from typing import Any


def rank_docs_by_similarity(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank document chunks by cosine similarity score descending."""
    return sorted(docs, key=lambda x: float(x.get("similarity_score", 0.0)), reverse=True)
