"""deduplicator.py — Entity & Evidence Deduplicator."""

from app.modules.graphrag.ranking.fusion import FusedEvidence


def deduplicate_evidence(evidence_items: list[FusedEvidence]) -> list[FusedEvidence]:
    """Deduplicate evidence items by source ID and content string."""
    seen_ids = set()
    deduped = []
    for item in evidence_items:
        key = f"{item.source_type}:{item.source_id}:{item.content[:40]}"
        if key not in seen_ids:
            seen_ids.add(key)
            deduped.append(item)
    return deduped
